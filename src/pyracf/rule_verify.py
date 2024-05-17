import pandas as pd
import importlib.resources
import re
import yaml
import warnings
from .frame_filter import FrameFilter
from .racf_functions import generic2regex
from .utils import listMe, readableList, simpleListed


class RuleVerifier:
    ''' verify fields in profiles against expected values, issues are returned in a df.

    rules can be passed as a list of tuples, and a dict with domains, via parameter, or as function result from external module.
    created from RACF object with the .rules property.
    '''

    def __init__(self, RACFobject):
        self._RACFobject = RACFobject
        self._rules = None
        self._domains = {}
        self._module = None

    def load(self, rules=None, domains={}, module=None, reset=False, defaultmodule=".profile_field_rules"):
        '''load rules + domains from yaml str, structure or from packaged module

        Args:
            rules (list, str): list of lists with test specifications, or yaml str field that expands into a list of lists
            domains (dict, str): one or more domain in a dict(name=[entries]), or in a yaml string
            module (str): name of module that contains functions rules() and domains()
            defaultmodule (str): module name to be used if all parameters are omitted
            reset (bool): clear rules, domains and module in RuleVerifier object, before loading new values

        Returns:
            RuleVerifier: the updated object

        Example:

        ::

            r.rules.load(rules = [
                (['DSBD'],
                 {'id': '101',
                  'rule': 'Integrity of test libraries',
                  'profile': 'TEST*.**',
                  'test': [{'field':'UACC', 'value':['NONE','READ']},
                          {'field':'WARNING', 'value':'NO'},
                          {'field':'NOTIFY_ID', 'fit':'DELETE'}],
                 }
                )
                                 ]
                        ).verify()

        '''

        if reset:  # clear prior load
            self._rules = None
            self._domains = {}
            self._module = None

        if rules and domains: pass  # complete parameters ?
        elif module: pass  # complete parameters ?
        elif self._rules and self._domains: pass  # previously loaded or specified ?
        elif self._module:  # previously specified ?
            module = self._module
        else:
            module = defaultmodule  # backstop

        if rules and domains: pass  # got everything from parms, ignore module and history
        elif (self._rules and self._domains) and not module:  # get missing component(s) from prior load
            if not rules:
                rules = self._rules
            if not domains:
                domains = self._domains
        else:  # get the missing component(s) from module
            ruleset = importlib.import_module(module, package="pyracf")
            ruleset = importlib.reload(ruleset)  # reload module for easier test of modifications
            if not rules:
                rules = ruleset.rules(self)
            if not domains:
                domains = ruleset.domains(self,pd)  # needs pandas

        if rules and type(rules)==str:
            rules = yaml.safe_load(rules)
        if domains and type(domains)==str:
            domains = yaml.safe_load(domains)

        self._rules=rules
        self._domains=domains

        return self

    def add_domains(self, domains=None):
        ''' Add domains to the end of the domain list, from a dict or a yaml string value.

        Args:
            domains (dict, str): one or more domain in a dict(name=[entries]), or in a yaml string

        Returns:
            RuleVerifier: The updated object

        Example::

          v = r.rules.load()

          v.add_domains({'PROD_GROUPS': ['PRODA','PRODB,'PRODCICS'],
                         'TEST_GROUPS': ['TEST1','TEST2']})

          v.add_domains({'SYS1': r.connect('SYS1').index})

        '''
        if type(domains)==dict:  # just a dict
            pass
        elif type(domains)==str:  # just a yaml (?) str
            domains = yaml.safe_load(domains)
        else:
            raise TypeError('domains parameter must be a dict or a yaml string')

        for (name,items) in domains.items():
            if type(name)==str:
                if type(items)==list:  # name and list?
                    pass
                else:  # name and list?
                    try:
                        shape = items.shape
                    except:
                        raise TypeError(f'domain entry {name} must have a list or a pandas object')
                    else:
                        if len(shape)!=1:
                            raise TypeError(f'domain entry {name} must have a one-dimensional, list-like value')
            else:
                raise TypeError(f'domain entry {name} should have a name and a list')

        self._domains.update(domains)

        return self

    def verify(self, rules=None, domains={}, module=None, reset=False, id=True, syntax_check=True):
        ''' verify fields in profiles against the expected value, issues are returned in a df

        Args:
            id (bool): False: suppress ID column from the result frame. The values in this column are taken from the id property in rules
            syntax_check (bool): False: suppress implicit syntax check

        Returns:
            RuleFrame: Result object

        Example::

          r.rules.load().verify()

        '''

        if rules or domains or module or reset or not (self._rules and self._domains):
            self.load(rules, domains, module, reset)

        if not (self._rules and self._domains):
            raise TypeError('rules and domains must be loaded before running verify')

        if type(id)!=bool:
            raise TypeError('issue id must be True or False')

        def initArray(value, like):
            ''' create an array of True to apply (AND) EXCLUDE type actions, or an array for False to OR SELECT type actions '''
            if value:
                return pd.Series(True, index=like.index)
            else:
                return pd.Series(False, index=like.index)
            #if value:
            #    return pd.array([True]*like.shape[0],bool)
            #else:
            #    return pd.array([False]*like.shape[0],bool)
            #if value:
            #    return np.ones(like.shape[0],bool)
            #else:
            #    return np.zeros(like.shape[0],bool)

        def whereIsClass(df, classnames):
            ''' generate .loc[ ] argument for the _CLASS_NAME index field, supporting literals, generics, and lists of these '''
            classPattern = ''
            generic = False
            for cl in listMe(classnames):
                classPattern += generic2regex(cl) + "|"
                generic &= cl.find('*')==-1 and cl.find('%')==-1
            if generic:
                return df.index.get_level_values(0).str.match(classPattern[:-1])
            elif type(classnames)==str:
                return df.index.get_level_values(0)==classnames
            else:
                return df.index.get_level_values(0).isin(classnames)

        def safeDomain(item):
            ''' lookup domain identifier, return content or issue message '''
            try:
                return self._domains[item]
            except KeyError:
                warnings.warn(f"fit argument {item} not in domain list, try {readableList(self._domains.keys())} instead")
                return []

        if syntax_check:
            syntax = self.syntax_check(confirm=False)
            if not syntax.empty:
                warnings.warn('verify() cannot process rules with syntax failures')
                return syntax

        columns = ['CLASS','PROFILE','FIELD_NAME','EXPECT','ACTUAL','RULE','ID']
        if not id:
            columns = columns[:-1]
        brokenSum = RuleFrame(columns=columns)

        for (tbNames,*tbCriteria) in self._rules:
            for tbName in listMe(tbNames):
                try:
                    tbDF = self._RACFobject.table(tbName)
                except KeyError:
                    warnings.warn(f'no table {tbName} in RACF object')
                    continue
                if tbDF.empty:
                    continue

                tbEntity = tbName[0:2]
                tbClassName = {'DS':'dataset', 'GP':'group', 'GR':'general', 'US':'user'}[tbEntity]
                ixLevel = 1 if tbEntity=='GR' else 0  # GR has CLASS before NAME in the index

                # each tbCrit is a dict with 0 or 1 class, profile, match, select and test specifications

                for tbCrit in tbCriteria:
                    subjectDF = tbDF  # subject for this test
                    matchPattern = None  # indicator that matched (dynamic) fields are used in this test
                    actionLocs = {}   # filled by find and skip

                    if 'class' in tbCrit:
                        if tbEntity!='GR':
                            print('only for GR')
                        subjectDF = subjectDF.loc[whereIsClass(subjectDF, tbCrit['class'])]
                    if '-class' in tbCrit:
                        if tbEntity=='GR':
                            subjectDF = subjectDF.loc[~ whereIsClass(subjectDF, tbCrit['-class'])]

                    if 'profile' in tbCrit:
                        subjectDF = subjectDF.loc[subjectDF.index.get_level_values(ixLevel).str.match(generic2regex(tbCrit['profile']))]
                    if '-profile' in tbCrit:
                        subjectDF = subjectDF.loc[ ~ subjectDF.index.get_level_values(ixLevel).str.match(generic2regex(tbCrit['-profile']))]

                    if 'match' in tbCrit:
                        matchPattern = tbCrit['match'].replace('.',r'\.').replace('*',r'\*')\
                                                      .replace('(','(?P<').replace(')','>[^.]*)')
                        matched = subjectDF[tbName+'_NAME'].str.extract(matchPattern)  # extract 1 qualifier

                    # find and skip use same parser, if these kwds are used, actionLocs are filled
                    # suffix find and skip with any character(s) to specify alternative selections

                    for (action,*actCrits) in tbCrit.items(): # should only find 1 item in each tbCrit, but have to access key+value
                        if action[0:4]=='find': action = 'find'
                        elif action[0:4]=='skip': action = 'skip'
                        else: break
                        if action not in actionLocs:
                            actionLocs[action] = initArray(False, like=subjectDF)

                        # 1 or more fields can be compared in each select/-select
                        # each field compare consists of 2 or 3 tests (fldLocs) that are AND-ed
                        # result of those AND-ed test are OR-ed into actLocs
                        # entries in subjectDF and in matched must be compared, so combine test results in Locs arrays.
                        # *actCrits accepts filter directives with 1 tuple or a list of tuples
                        # listMe(actCrit) helps unroll the list of tuples

                        for actCrit in actCrits:
                            actLocs = initArray(True, like=subjectDF)
                            for fldCrit in listMe(actCrit):
                                fldLocs = initArray(False, like=subjectDF)
                                if matchPattern and fldCrit['field'] in matched.columns:
                                    fldName = fldCrit['field']
                                    fldColumn = matched[fldName]  # look in the match result
                                else:  # not a matching field name in match result
                                    fldName = '_'.join([tbName,fldCrit['field']])
                                    fldColumn = subjectDF[fldName]  # look in the main table
                                if 'fit' in fldCrit:
                                    fldLocs |= fldColumn.gt('') & fldColumn.isin(safeDomain(fldCrit['fit']))
                                if 'value' in fldCrit:
                                    if type(fldCrit['value'])==str:
                                        fldLocs |= fldColumn.eq(fldCrit['value'])
                                    else:
                                        fldLocs |= fldColumn.gt('') & fldColumn.isin(fldCrit['value'])
                                actLocs &= fldLocs
                            actionLocs[action] |= actLocs

                    # actual reporting, relies on subjectDF, matched and tbLocs to be aligned.
                    # when test: command is processed, we combine the class, profile and filter commands in tbLocs
                    # the blocks in test: each create a new fldLocs off tbLocs
                    # we run each field, from all tests separately, and combine results in brokenSum

                    if 'test' in tbCrit:
                        tbLocs = initArray(True, like=subjectDF)
                        if 'find' in actionLocs: tbLocs &= actionLocs['find']
                        if 'skip' in actionLocs: tbLocs &= ~ actionLocs['skip']

                        for fldCrit in listMe(tbCrit['test']):
                            fldLocs = tbLocs.copy()  # updates to fldLocs clobber tbLocs too, unless you copy()
                            # test can contain 1 dict or a list of dicts
                            # entries in subjectDF and in matched must be compared, so combine test results in fldLocs array.
                            # final .loc[ ] test is done once in assignment to 'broken' frame.
                            if matchPattern and fldCrit['field'] in matched.columns:
                                fldName = fldCrit['field']
                                fldColumn = matched[fldName]  # look in the match result
                            else:  # not a matching field name in match result
                                fldName = '_'.join([tbName,fldCrit['field']])
                                fldColumn = subjectDF[fldName]  # look in the main table
                            if 'fit' in fldCrit:
                                fldLocs &= fldColumn.gt('') & ~ fldColumn.isin(safeDomain(fldCrit['fit']))
                            if 'value' in fldCrit:
                                if type(fldCrit['value'])==str:
                                    fldLocs &= ~ fldColumn.eq(fldCrit['value'])
                                else:
                                    fldLocs &= fldColumn.gt('') & ~ fldColumn.isin(fldCrit['value'])

                            if any(fldLocs):
                                broken = subjectDF.loc[fldLocs].copy()
                                broken['ACTUAL'] = matched[fldName] if matchPattern else broken[fldName]
                                broken = broken.rename({tbName+'_CLASS_NAME':'CLASS', tbName+'_NAME':'PROFILE'},axis=1)
                                if tbEntity!='GR':
                                    broken['CLASS'] = tbClassName
                                broken['FIELD_NAME'] = fldName
                                broken['EXPECT'] = fldCrit['fit'] if 'fit' in fldCrit else simpleListed(fldCrit['value']) if 'value' in fldCrit else '?'
                                broken['RULE'] = fldCrit['rule'] if 'rule' in fldCrit else tbCrit['rule'] if 'rule' in tbCrit else ''
                                if id:
                                    broken['ID'] = fldCrit['id'] if 'id' in fldCrit else tbCrit['id'] if 'id' in tbCrit else ''
                                brokenSum = pd.concat([brokenSum,broken[brokenSum.columns]],
                                                       sort=False, ignore_index=True)
                    else:
                        warnings.warn(f'missing test directive in {tbCrit}')

        return RuleFrame(brokenSum)

    def syntax_check(self, confirm=True):
        ''' check rules and domains for consistency and unknown directives

        specify confirm=False to suppress the message when all is OK

        Args:
            confirm (bool): False if the success message should be suppressed, so in automated testing the result frame has .empty

        Example::

          r.rules.load().syntax_check()

          if r.rules.load().syntax_check(confirm=False).empty:
              print('No syntax errors in default policy')

        '''

        if not (self._rules and self._domains):
            raise TypeError('rules and domains must be loaded before running syntax check')

        def broken(field,value,comment):
            brokenList.append(dict(FIELD=field, VALUE=value, COMMENT=comment))

        brokenList = []

        for (name,*items) in self._domains:
            if type(name)!=str:
                broken('domain',Name,f"domain entry {Name} must have a string lable")
            if isinstance(items,list) :pass
            else:
                try:
                    shape = items.shape
                except:
                    broken('domain',Name,f"domain entry {Name} does not have a pandas value object")
                else:
                    if len(shape)>1:
                        broken('domain',Name,f"domain entry {Name} must have a one-dimensional, list-like value")


        for (tbNames,*tbCriteria) in self._rules:
            for tbName in listMe(tbNames):
                tbDF = self._RACFobject.table(tbName)
                if isinstance(tbDF,pd.DataFrame):
                    if tbDF.empty:
                        tbDefined = False  # empty frame has no columns
                    else:
                         tbDefined = True  # check the field names in the frame
                else:
                    broken('table',tbName,f"no table {tbName} in RACF object")
                    tbDefined = False

                tbEntity = tbName[0:2]
                tbClassName = {'DS':'dataset', 'GP':'group', 'GR':'general', 'US':'user'}[tbEntity]
                ixLevel = 1 if tbEntity=='GR' else 0  # GR has CLASS before NAME in the index

                # each tbCrit is a dict with 0 or 1 class, profile, match, select and test specifications

                for tbCrit in tbCriteria:

                    for action in tbCrit.keys():
                        if action not in ['class','-class','profile','-profile','match','test','rule','id']:
                            if action[0:4]!='find' and action[0:4]!='skip':
                                broken('action',action,f"unsupported action {action} with table {tbNames}")

                    if 'class' in tbCrit:
                        if tbEntity!='GR':
                            broken('class',tbCrit['class'],f"cannot use {tbCrit['class']} in {tbClassName} table")

                    if 'match' in tbCrit:
                        matchFields = re.findall(r'\((\S+?)\)',tbCrit['match'])
                        if len(matchFields)==0:
                            broken('match',tbCrit['match'],f"at least 1 field should be defined between parentheses")
                    else:
                        matchFields = None

                    for (action,*actCrits) in tbCrit.items(): # should only find 1 item, but have to access key+value
                        if action[0:4]=='find': action = 'find'
                        elif action[0:4]=='skip': action = 'skip'
                        else: break

                        if type(actCrits)!=list:
                            broken('filter',actCrit,'find/skip should have a list of criteria')

                        for actCrit in actCrits:
                            for fldCrit in listMe(actCrit):
                                if type(fldCrit)!=dict:
                                    broken('filter',fldCrit,'each of criteria should be a dict')
                                for section in fldCrit.keys():
                                    if section not in ['field','fit','value','rule']:
                                        broken('filter',fldCrit,f"unsupported section {section} in {action}")
                                if 'field' not in fldCrit:
                                    broken('filter',fldCrit,f"field must be specified in filter {fldCrit}")
                                if not('fit' in fldCrit or 'value' in fldCrit):
                                    broken('filter',fldCrit,f"fit or value should be specified in filter {fldCrit}")

                                if tbDefined and '_'.join([tbName,fldCrit['field']]) not in tbDF.columns:
                                    if matchFields and fldCrit['field'] in matchFields: pass
                                    else:
                                        broken('field',fldCrit['field'],f"field name {fldCrit['field']} not found in {tbName} or match definition")
                                if 'fit' in fldCrit and fldCrit['fit'] not in self._domains:
                                    broken('fit',fldCrit['fit'],f"domain name {fldCrit['fit']} in filter not defined")
                                if 'value' in fldCrit and type(fldCrit['value'])==bool:
                                    broken('value',fldCrit['field'],f"yaml text string {fldCrit['value']} for {fldCrit['field']} is not a str")

                    if 'test' in tbCrit:
                        for fldCrit in listMe(tbCrit['test']):
                            if type(fldCrit)!=dict:
                                broken('test',fldCrit,'each of criteria should be a dict')
                            for section in fldCrit.keys():
                                if section not in ['field','fit','value','rule','id']:
                                    broken('test',fldCrit,f"unsupported section {section} in {action}")
                            if 'field' not in fldCrit:
                                broken('test',fldCrit,f"field must be specified in test {fldCrit}")
                            if not('fit' in fldCrit or 'value' in fldCrit):
                                broken('test',fldCrit,f"fit or value must be specified in test {fldCrit}")

                            if tbDefined and '_'.join([tbName,fldCrit['field']]) not in tbDF.columns:
                                if matchFields and fldCrit['field'] in matchFields: pass
                                else:
                                    broken('field',fldCrit['field'],f"field name {fldCrit['field']} not found in {tbName} or match definition")
                            if 'fit' in fldCrit and fldCrit['fit'] not in self._domains:
                                broken('fit',fldCrit['fit'],f"domain name {fldCrit['fit']} in test not defined")
                            if 'value' in fldCrit and type(fldCrit['value'])==bool:
                                broken('value',fldCrit['field'],f"yaml text string {fldCrit['value']} for {fldCrit['field']} is not a str")
                    else:
                        broken('table',tbName,f'test directive missing in {tbName}, no output will be generated')

        if not brokenList and confirm:
            brokenList.append(dict(field='rules', value='OK', comment='No problem found in rules'))
        return RuleFrame(brokenList)


class RuleFrame(pd.DataFrame,FrameFilter):
    ''' Output of a verify() action '''

    @property
    def _constructor(self):
        ''' a result of a method is also a RuleFrame  '''
        return RuleFrame

    _verifyFilterKwds = {'resclass':'CLASS', 'profile':'PROFILE', 'field':'FIELD_NAME', 'actual':'ACTUAL', 'found':'ACTUAL', 'expect':'EXPECT', 'fit':'EXPECT', 'value':'EXPECT', 'id':'ID'}

    def find(df, *selection, **kwds):
        '''Search rule results using GENERIC pattern on the data fields.  selection can be one or more values, corresponding to data columns of the df.

        alternatively specify the field names via an alias keyword:

        ``r.rules.load().verify().find(field='OWN*')``

        specify selection as regex using re.compile:

        ``r.rules.load().verify().find( field=re.compile('(OWNER|DFLTGRP)' )``
        '''
        return df._frameFilter(*selection, **kwds, kwdValues=df._verifyFilterKwds)

    def skip(df, *selection, **kwds):
        '''Exclude rule results using GENERIC pattern on the data fields.  selection can be one or more values, corresponding to data columns of the df

        alternatively specify the field names via an alias keyword:

        ``r.rules.load().verify().skip(actual='SYS1')``
        '''
        return df._frameFilter(*selection, **kwds, kwdValues=df._verifyFilterKwds, exclude=True)

