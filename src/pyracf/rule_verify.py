import pandas as pd
import importlib.resources
import re
import yaml
import warnings
from .frame_filter import FrameFilter
from .racf_functions import generic2regex
from .utils import listMe, readableList, simpleListed, nameInColumns

def _construct_yaml_map(self, node):
    '''Add suffix to duplicate node keys in yaml input'''
    data = {}
    yield data
    for key_node, value_node in node.value:
        key = self.construct_object(key_node, deep=True)
        val = self.construct_object(value_node, deep=True)
        if key in data:
            for i in range(1,999):
                candidate = f'{key}#{i}'
                if candidate not in data:
                    warnings.warn(f'duplicate key "{key}" in yaml input, new key value {candidate} substituted', FutureWarning)
                    key = candidate
                    break
        data.update({key: val})

yaml.constructor.SafeConstructor.add_constructor(u'tag:yaml.org,2002:map', _construct_yaml_map)


class RuleFrame(pd.DataFrame,FrameFilter):
    ''' Output of a verify() action '''

    @property
    def _constructor(self):
        ''' a result of a method is also a RuleFrame  '''
        return RuleFrame

    _verifyFilterKwds = {'resclass':'CLASS', 'profile':'PROFILE', 'field':'FIELD_NAME', 'actual':'ACTUAL', 'found':'ACTUAL', 'expect':'EXPECT', 'fit':'EXPECT', 'value':'EXPECT', 'id':'ID'}

    def find(df, *selection, **kwds):
        '''Search rule results using GENERIC pattern on the data fields.  selection can be one or more values, corresponding to data columns of the df.

        alternatively specify the field names via an alias keyword (resclass, profile, field, actual, found, expect, fit, value or id):

        ``r.rules.load().verify().find(field='OWN*')``

        specify selection as regex using re.compile:

        ``r.rules.load().verify().find( field=re.compile('(OWNER|DFLTGRP)' )``
        '''
        return df._frameFilter(*selection, **kwds, kwdValues=df._verifyFilterKwds)

    def skip(df, *selection, **kwds):
        '''Exclude rule results using GENERIC pattern on the data fields.  selection can be one or more values, corresponding to data columns of the df

        alternatively specify the field names via an alias keyword (resclass, profile, field, actual, found, expect, fit, value or id):

        ``r.rules.load().verify().skip(actual='SYS1')``
        '''
        return df._frameFilter(*selection, **kwds, kwdValues=df._verifyFilterKwds, exclude=True)


class RuleVerifier:
    ''' verify fields in profiles against expected values, issues are returned in a df.

    rules can be passed as a dict of [tuples or lists], and a dict with domains, via parameter, or as function result from external module.
    created from RACF object with the .rules property.
    '''

    def __init__(self, RACFobject):
        self._RACFobject = RACFobject
        self._rules = None
        self._domains = {}
        self._module = None

    def load(self, rules=None, domains=None, module=None, reset=False, defaultmodule=".profile_field_rules"):
        '''load rules + domains from yaml str, structure or from packaged module

        Args:
            rules (dict, str): dict of tuples or lists with test specifications, or yaml str field that expands into a dict of lists
            domains (dict, str): one or more domain in a dict(name=[entries]), or in a yaml string
            module (str): name of module that contains functions rules() and domains()
            defaultmodule (str): module name to be used if all parameters are omitted
            reset (bool): clear rules, domains and module in RuleVerifier object, before loading new values

        Returns:
            RuleVerifier: the updated object

        Example:

        ::

            r.rules.load(rules = {'test libraries':
                (['DSBD'],
                 {'id': '101',
                  'rule': 'Integrity of test libraries',
                  'profile': 'TEST*.**',
                  'test': [{'field':'UACC', 'value':['NONE','READ']},
                          {'field':'WARNING', 'value':'NO'},
                          {'field':'NOTIFY_ID', 'fit':'DELETE'}],
                 }
                )
                                 }
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

        if rules and isinstance(rules,str):
            rules = yaml.safe_load(rules)
        if domains and isinstance(domains,str):
            domains = yaml.safe_load(domains)

        self._rules=rules
        self._domains=domains

        return self

    def add_domains(self, domains=None):
        ''' Add domains to the end of the domain list, from a dict or a yaml string value.

        Args:
            domains (dict, str): one or more domains in a dict(name=[entries]), or in a yaml string

        Returns:
            RuleVerifier: The updated object

        Example::

          v = r.rules.load()

          v.add_domains({'PROD_GROUPS': ['PRODA','PRODB','PRODCICS'],
                         'TEST_GROUPS': ['TEST1','TEST2']})

          v.add_domains({'SYS1': r.connect('SYS1').index})

        '''
        if domains and isinstance(domains,dict):  # just a dict
            pass
        elif domains and isinstance(domains,str):  # just a yaml (?) str
            domains = yaml.safe_load(domains)
        else:
            raise TypeError('domains parameter must be a dict or a yaml string')

        for (name,items) in domains.items():
            if isinstance(name,str):
                if isinstance(items,list):  # name and list?
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

    def get_domains(self, domains=None):
        ''' Get domain definitions as a dict, or one entry as a list.

        Args:
            domains str: name of domain entry to return as list, or None to return all

        Returns:
            dict or list

        Example::

          v.get_domains() # all domains as a dict

          v.get_domains('PROD_GROUPS') # one domain as a list

        '''
        if not domains:
            return self._domains
        elif isinstance(domains,str):  # just 1 domain?
            return self._domains[domains] if domains in self._domains else []
        else:
            raise TypeError('domains parameter must be the name of a domain, or missing')

    def verify(self, rules=None, domains=None, module=None, reset=False, id=True, verbose=False, syntax_check=None, optimize='rows cols') -> RuleFrame:
        ''' verify fields in profiles against the expected value, issues are returned in a df

        Args:
            id (bool): False: suppress ID column from the result frame. The values in this column are taken from the id property in rules
            syntax_check (bool): deprecated
            verbose (bool): True: print progress messages
            optimize (str): cols to improve join speed, rows to use pre-selection

        Returns:
            Result object (RuleFrame)

        Example::

          r.rules.load().verify()

        '''

        import time

        if rules or domains or module or reset or not (self._rules and self._domains):
            self.load(rules, domains, module, reset)

        if not (self._rules and self._domains):
            raise TypeError('rules and domains must be loaded before running verify')

        if not isinstance(id,bool):
            raise TypeError('issue id must be True or False')

        if syntax_check is not None:
            warnings.warn('syntax_check option is deprecated, syntax_check is now implied')

        def initArray(value, like):
            ''' create an array of True to apply (AND) EXCLUDE type actions, or an array for False to OR SELECT type actions '''
            return pd.Series(value, index=like.index)
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
            elif isinstance(classnames,str):
                return df.index.get_level_values(0)==classnames
            else:
                return df.index.get_level_values(0).isin(classnames)

        def safeDomain(item):
            ''' lookup domain identifier, return content or issue message '''
            try:
                return self._domains[item]
            except KeyError:
                warnings.warn(f"fit argument {item} not in domain list, try {readableList(self._domains.keys())} instead", SyntaxWarning)
                return []

        v_m_rule = None  # current rule name
        def v_m(*parms):
            '''print verbose progress message'''
            if verbose:
                nonlocal v_m_rule
                if v_m_rule != tbRuleName:
                    v_m_rule = tbRuleName
                    print("Processing starts:",v_m_rule)
                print(*parms)

        if '_rules parsed, checked and normalized' not in self._rules:
            syntax = self.syntax_check(confirm=False)
            if not syntax.empty:
                warnings.warn('verify() cannot process rules with syntax failures', SyntaxWarning)
                return syntax

        columns = ['CLASS','PROFILE','FIELD_NAME','EXPECT','ACTUAL','RULE','ID']
        if not id:
            columns = columns[:-1]
        brokenSum = RuleFrame(columns=columns)
        savedViews = {}

        for tbRuleName, (tbNames,*tbCriteria) in self._rules.items():
            if tbRuleName == '_rules parsed, checked and normalized': continue
            for tbName in listMe(tbNames):
                if tbName in savedViews:
                    (tbDF,tbModel) = savedViews[tbName]
                else:
                    tbModel = tbName  # in case the result of the selection is saved
                    try:
                        tbDF = self._RACFobject.table(tbName)
                    except KeyError:
                        warnings.warn(f'no table {tbName} in RACF object', SyntaxWarning)
                        continue
                if tbDF.empty:
                    continue
                v_m('table',tbName,'shape',tbDF.shape)

                tbEntity = tbModel[0:2]
                tbClassName = {'DS':'dataset', 'GP':'group', 'GR':'general', 'US':'user'}[tbEntity]
                ixLevel = 1 if tbEntity=='GR' else 0  # GR has CLASS before NAME in the index

                # each tbCrit is a dict with 0 or 1 class, profile, match, select and test specifications

                for tbCrit in tbCriteria:
                    subjectDF = tbDF  # subject for this test
                    matchPattern = None  # indicator that matched (dynamic) fields are used in this test

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
                        if isinstance(tbCrit['match'],list) or tbCrit['match'].find('(')==-1:  # match profile key on dsname or resource name (list)
                            subjectDF = subjectDF.match(tbCrit['match'])
                    if '-match' in tbCrit:  # all except the matched profile(s)
                        subjectDF = subjectDF.loc[subjectDF.index.difference(subjectDF.match(tbCrit['-match']).index)]

                    # find and skip use same parser, if these kwds are used, actionLocs are filled
                    # suffix find and skip with any character(s) to specify alternative selections
                    # first we do selection only on fields in subjectDF, and reduce the size of this Frame

                    actionLocs = {}   # filled by find and skip
                    doneFindSkip = True  # False when Find and Skip have to be redone, in case join or match directives are used
                    for (action,actCrit) in tbCrit.items(): # we have to access key (directive) + value (parms)
                        if action[0:4]=='find': action = 'find'
                        elif action[0:4]=='skip': action = 'skip'
                        else: continue
                        if 'rows' not in optimize.split():
                            doneFindSkip = False
                            continue
                        if action not in actionLocs:
                            actionLocs[action] = initArray(False, like=subjectDF)

                        # 1 or more fields can be compared in each find/skip
                        # each field compare consists of 2 or 3 tests (fldLocs) that are AND-ed
                        # result of those AND-ed test are OR-ed into actLocs

                        actLocs = initArray(True, like=subjectDF)
                        for fldCrit in listMe(actCrit):
                            early = True  # are names for this field criterium already in subjectDF?
                            fldLocs = initArray(False, like=subjectDF)
                            if '_field_early' in fldCrit:
                                fldName = nameInColumns(subjectDF,fldCrit['field'],prefix=tbModel)
                                fldColumn = subjectDF[fldName]  # look only in the main table
                                if 'fit' in fldCrit:
                                    fldLocs |= fldColumn.gt('') & fldColumn.isin(safeDomain(fldCrit['fit']))
                                if 'value' in fldCrit:
                                    if isinstance(fldCrit['value'],str):
                                        fldLocs |= fldColumn.eq(fldCrit['value'])
                                    else:
                                        fldLocs |= fldColumn.gt('') & fldColumn.isin(fldCrit['value'])
                                if 'eq' in fldCrit:
                                    if '_eq_early' in fldCrit:
                                        fldName = nameInColumns(subjectDF,fldCrit['eq'],prefix=tbModel)
                                        fldLocs |= fldColumn.eq(subjectDF[fldName])
                                    else:
                                        early = False
                                if 'ne' in fldCrit:
                                    if '_ne_early' in fldCrit:
                                        fldName = nameInColumns(subjectDF,fldCrit['ne'],prefix=tbModel)
                                        if any(fldLocs):
                                            fldLocs &= fldColumn.ne(subjectDF[fldName])
                                        else:
                                            fldLocs = fldColumn.ne(subjectDF[fldName])
                                    else:
                                        early = False
                                actLocs &= fldLocs
                            else:
                                early = False
                            if not early:
                                doneFindSkip = False  # at least one field was not in subjectDF, so redo after join + match complete
                                if action=='skip':  # a skip that cannot resolve a field would skip too much, so don't skip in first attempt
                                    actLocs = initArray(False, like=subjectDF)
                                    break
                        actionLocs[action] |= actLocs
                    if 'find' in actionLocs: subjectDF = subjectDF.loc[actionLocs['find']]
                    if 'skip' in actionLocs: subjectDF = subjectDF.loc[~ actionLocs['skip']]

                    if 'join' in tbCrit:
                        joinCrit = tbCrit['join']
                        if isinstance(joinCrit,str): # join: userTSO or join: USOMVS
                            joinTab = joinCrit
                            joinCol = None
                        elif isinstance(joinCrit,dict): # join: {table: userTSO, on: AUTH_ID}
                            joinTab = ''
                            joinCol = None
                            if 'table' in joinCrit:
                                joinTab = joinCrit['table']
                            if 'on' in joinCrit:
                                joinCol = joinCrit['on']
                        else:
                            raise ValueError(f"join directive {joinCrit} needs a table and on field name")
                        if 'how' in joinCrit:
                            joinMethod = joinCrit['how']
                            if joinMethod not in ['left','right','outer','inner','cross']:
                                raise ValueError("only 'left','right','outer','inner' and 'cross' are accepted join methods")
                        else:
                            joinMethod = 'inner'

                        if joinTab in savedViews:
                            (joinDF,joinModel) = savedViews[joinTab]
                        elif joinTab.isupper():
                            joinDF = self._RACFobject.table(joinTab)
                            joinModel = joinTab
                        else:
                            joinDF = getattr(self._RACFobject,joinTab)
                            joinModel = joinDF._fieldPrefix
                        if joinModel=='': print('panic joinModel',joinTab)
                        if joinModel=='USCON':
                            if tbEntity=='US':  # link from user ID to connect groups
                                joinDF=joinDF.droplevel(0)  # so use the user ID index level for join

                        if joinCol:
                            joinCol=nameInColumns(subjectDF,joinCol)

                        if 'cols' in optimize.split():
                            left_cols = nameInColumns(tbDF,tbCrit['_refFields'],returnAll=True)
                            right_cols = nameInColumns(joinDF,tbCrit['_refFields'],returnAll=True)
                        else:
                            left_cols = slice(None)
                            right_cols = slice(None)

                        v_m('join','results before',subjectDF.shape,'join with',joinTab,joinDF.shape)
                        start = time.time()
                        subjectDF = subjectDF[left_cols].join(joinDF[right_cols], on=joinCol, how=joinMethod).fillna('')
                        used = time.time() - start
                        v_m('join','results after',subjectDF.shape,'elapsed {:.6f} seconds'.format(used))

                    if 'match' in tbCrit:
                        if isinstance(tbCrit['match'],str) and tbCrit['match'].find('(')!=-1:  # match and extract
                            matchPattern = tbCrit['match'].replace('.',r'\.').replace('*',r'\*')\
                                                          .replace('(','(?P<').replace(')','>[^.]*)')
                            matched = subjectDF[subjectDF._fieldPrefix+'NAME'].str.extract(matchPattern)  # extract 1 qualifier

                    # find and skip use same parser, if these kwds are used, actionLocs are filled
                    # suffix find and skip with any character(s) to specify alternative selections
                    # now we repeat the selection, including the joined and matched fields

                    actionLocs = {}   # filled by find and skip
                    for (action,actCrit) in tbCrit.items(): # we have to access key (directive) + value (parms)
                        if doneFindSkip: continue  # no need to redo
                        elif action[0:4]=='find': action = 'find'
                        elif action[0:4]=='skip': action = 'skip'
                        else: continue
                        if action not in actionLocs:
                            actionLocs[action] = initArray(False, like=subjectDF)

                        # 1 or more fields can be compared in each select/-select
                        # each field compare consists of 2 or 3 tests (fldLocs) that are AND-ed
                        # result of those AND-ed test are OR-ed into actLocs
                        # entries in subjectDF and in matched must be compared, so combine test results in Locs arrays.

                        actLocs = initArray(True, like=subjectDF)
                        for fldCrit in listMe(actCrit):
                            fldLocs = initArray(False, like=subjectDF)
                            if '_field_matched' in fldCrit:
                                fldColumn = matched[fldCrit['field']]  # look in the match result
                            else:  # not a matching field name in match result, look in data columns
                                fldName = nameInColumns(subjectDF,fldCrit['field'])
                                fldColumn = subjectDF[fldName]  # look in the main table
                            if 'fit' in fldCrit:
                                fldLocs |= fldColumn.isin(safeDomain(fldCrit['fit']))
                            if 'value' in fldCrit:
                                if isinstance(fldCrit['value'],str):
                                    fldLocs |= fldColumn.eq(fldCrit['value'])
                                elif '' in fldCrit['value']:
                                    fldLocs |= fldColumn.isin(fldCrit['value'])
                                else:
                                    fldLocs |= fldColumn.gt('') & fldColumn.isin(fldCrit['value'])
                            if 'eq' in fldCrit:
                                series = matched[fldCrit['_eq']] if '_eq_matched' in fldCrit else subjectDF[nameInColumns(subjectDF,fldCrit['eq'])]
                                fldLocs |= fldColumn.eq(series)
                            if 'ne' in fldCrit:
                                series = matched[fldCrit['_ne']] if '_ne_matched' in fldCrit else subjectDF[nameInColumns(subjectDF,fldCrit['ne'])]
                                if any(fldLocs):
                                    fldLocs &= fldColumn.ne(series)
                                else:
                                    fldLocs = fldColumn.ne(series)
                            actLocs &= fldLocs
                        actionLocs[action] |= actLocs

                    tbLocs = initArray(True, like=subjectDF)
                    if 'find' in actionLocs: tbLocs &= actionLocs['find']
                    if 'skip' in actionLocs: tbLocs &= ~ actionLocs['skip']

                    if 'save' in tbCrit:
                        if isinstance(tbNames,str) or (isinstance(tbNames,list) and len(tbNames)==1):
                            savedViews[tbCrit['save']] = (subjectDF.loc[tbLocs].copy(), tbModel)
                        else:
                            warnings.warn(f"save: {tbCrit['save']} ignored, {tbNames} is more than 1 input table")

                    # actual reporting, relies on subjectDF, matched and tbLocs to be aligned.
                    # when test: command is processed, we combine the class, profile and filter commands in tbLocs
                    # the blocks in test: each create a new fldLocs off tbLocs
                    # we run each field, from all tests separately, and combine results in brokenSum

                    v_m('selected',sum([t for t in tbLocs]),'from',subjectDF.shape)
                    if 'test' in tbCrit:
                        for fldCrit in listMe(tbCrit['test']):
                            fldLocs = initArray(False, like=subjectDF)
                            if '_field_matched' in fldCrit:
                                fldName = fldCrit['field']
                                fldColumn = matched[fldCrit['field']]  # look in the match result
                            else:  # not a matching field name in match result, look in data columns
                                fldName = nameInColumns(subjectDF,fldCrit['field'])
                                fldColumn = subjectDF[fldName]  # look in the main table
                            if 'fit' in fldCrit:
                                fldLocs |= fldColumn.isin(safeDomain(fldCrit['fit']))
                            if 'value' in fldCrit:
                                if isinstance(fldCrit['value'],str):
                                    fldLocs |= fldColumn.eq(fldCrit['value'])
                                elif '' in fldCrit['value']:
                                    fldLocs |= fldColumn.isin(fldCrit['value'])
                                else:
                                    fldLocs |= fldColumn.gt('') & fldColumn.isin(fldCrit['value'])
                            if 'eq' in fldCrit:
                                series = matched[fldCrit['_eq']] if '_eq_matched' in fldCrit else subjectDF[nameInColumns(subjectDF,fldCrit['eq'])]
                                fldLocs |= fldColumn.eq(series)
                            if 'ne' in fldCrit:
                                series = matched[fldCrit['_ne']] if '_ne_matched' in fldCrit else subjectDF[nameInColumns(subjectDF,fldCrit['ne'])]
                                if any(fldLocs):
                                    fldLocs &= fldColumn.ne(series)
                                else:
                                    fldLocs = fldColumn.ne(series)
                            if 'action' in fldCrit and fldCrit['action'].upper() in ['FAILURE','FAIL','F','V']:  # fldLocs selection fails the test
                                fldAction = 'not '
                                NOTfldAction = ''
                                fldLocs = tbLocs & fldLocs
                            else:  # fldLocs selection is policy compliant, so report items where fldLocs is False
                                fldAction = ''
                                NOTfldAction = 'not '
                                fldLocs = tbLocs & ~fldLocs
                            if '_field_matched' in fldCrit:  # match: also selects the records that match
                                fldLocs &= fldColumn.notna()

                            v_m('test','flagged',sum([t for t in fldLocs]),'from',subjectDF.shape)
                            if any(fldLocs):
                                broken = subjectDF.loc[fldLocs].copy()
                                broken['ACTUAL'] = matched[fldName] if '_field_matched' in fldCrit else broken[fldName]
                                broken = broken.rename({tbModel+'_CLASS_NAME':'CLASS', tbModel+'_NAME':'PROFILE'},axis=1)
                                if tbEntity!='GR':
                                    broken['CLASS'] = tbClassName
                                broken['FIELD_NAME'] = fldName
                                broken['EXPECT'] = fldAction + fldCrit['fit'] if 'fit' in fldCrit else \
                                                   fldAction + simpleListed(fldCrit['value']) if 'value' in fldCrit else \
                                                   fldAction + broken[nameInColumns(subjectDF,fldCrit['eq'])] if 'eq' in fldCrit else \
                                                   NOTfldAction + broken[nameInColumns(subjectDF,fldCrit['ne'])]  if 'ne' in fldCrit else '?'
                                broken['RULE'] = fldCrit['rule'] if 'rule' in fldCrit else tbCrit['rule'] if 'rule' in tbCrit else tbRuleName
                                if id:
                                    broken['ID'] = fldCrit['id'] if 'id' in fldCrit else tbCrit['id'] if 'id' in tbCrit else ''
                                brokenSum = pd.concat([brokenSum,broken[brokenSum.columns]],
                                                       sort=False, ignore_index=True)
                    elif 'save' in tbCrit:
                        pass
                    else:
                        warnings.warn(f'missing output directive in {tbCrit}, test or save expected', SyntaxWarning)

        return RuleFrame(brokenSum)

    def syntax_check(self, confirm=True) -> RuleFrame:
        ''' parse rules and domains, check for consistency and unknown directives, normalize field names

        specify confirm=False to suppress the message when all is OK

        Args:
            confirm (bool): False if the success message should be suppressed, so in automated testing the result frame has .empty

        Returns:
            syntax messages (RuleFrame)

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
        savedViews = {}

        for (name,*items) in self._domains:
            if not isinstance(name,str):
                broken('domain',name,f"domain entry {name} must have a string lable")
            if isinstance(items,list):
                pass
            else:
                try:
                    shape = items.shape
                except:
                    broken('domain',name,f"domain entry {name} does not have a pandas value object")
                else:
                    if len(shape)>1:
                        broken('domain',name,f"domain entry {name} must have a one-dimensional, list-like value")


        for tbRuleName, (tbNames,*tbCriteria) in self._rules.items():
            for tbName in listMe(tbNames):
                if tbName in savedViews:
                    (tbDF,tbModel,_) = savedViews[tbName]
                else:
                    tbDF = self._RACFobject.table(tbName)
                    tbModel = tbName
                if isinstance(tbDF,pd.DataFrame):
                    if tbDF.empty:
                        tbDefined = False  # empty frame has no columns
                    else:
                        tbDefined = True  # check the field names in the frame
                else:
                    broken('rule',tbRuleName,f"no table {tbName} in RACF object")
                    tbDefined = False

                tbEntity = tbModel[0:2]
                tbClassName = {'DS':'dataset', 'GP':'group', 'GR':'general', 'US':'user'}[tbEntity]
                ixLevel = 1 if tbEntity=='GR' else 0  # GR has CLASS before NAME in the index

                # each tbCrit is a dict with 0 or 1 class, profile, match, select and test specifications

                for tbCrit in tbCriteria:
                    tbCrit['_matchFields'] = []
                    tbCrit['_refFields'] = ['CLASS_NAME', 'NAME']
                    matchFields = None
                    if tbDefined:
                        tbColumns = tbDF.columns
                    else:
                        tbColumns = [tbModel+'_NAME']

                    for action in tbCrit.keys():
                        if action not in ['class','-class','profile','-profile','join','match','-match','test','rule','id','save'] and action[0]!='_':
                            if action[0:4]!='find' and action[0:4]!='skip':
                                broken('action',action,f"unsupported action {action} with table {tbNames}")

                    if 'class' in tbCrit:
                        if tbEntity!='GR':
                            broken('class',tbCrit['class'],f"cannot use {tbCrit['class']} in {tbClassName} table")

                    if 'match' in tbCrit:
                        if isinstance(tbCrit['match'],str) and tbCrit['match'].find('(')!=-1:
                            matchFields = re.findall(r'\((\S+?)\)',tbCrit['match'])
                            if len(matchFields)==0:
                                broken('match',tbCrit['match'],f"at least 1 field should be defined between parentheses")
                            else:
                                tbCrit['_matchFields'] = matchFields
                        else:
                            if isinstance(tbCrit['match'],(str,list)):
                                for m in listMe(tbCrit['match']):
                                    if m.find('*')!=-1 or m.find('%')!=-1:
                                        broken('match',tbCrit['match'],f"no generic patterns supported in match")
                                    if m.find('(')!=-1 or m.find(')')!=-1:
                                        broken('match',tbCrit['match'],f"extraction pattern cannot be used in list")
                            else:
                                broken('match',tbCrit['match'],f"unrecognized type type(tbCrit['match'])")

                    if '-match' in tbCrit:
                        if isinstance(tbCrit['-match'],(str,list)):
                            for m in listMe(tbCrit['-match']):
                                if m.find('*')!=-1 or m.find('%')!=-1:
                                    broken('-match',tbCrit['-match'],f"no generic patterns supported in match")
                                if m.find('(')!=-1 or m.find(')')!=-1:
                                    broken('-match',tbCrit['-match'],f"extraction pattern cannot be used in list")
                        else:
                            broken('-match',tbCrit['-match'],f"unrecognized type type(tbCrit['-match'])")

                    if 'join' in tbCrit:
                        joinCrit = tbCrit['join']
                        if isinstance(joinCrit,str): # join: userTSO or join: USOMVS
                            joinTab = joinCrit
                            joinCol = None
                        elif isinstance(joinCrit,dict): # join: {table: userTSO, on: AUTH_ID}
                            for d in joinCrit:
                                if d not in ['table','on',True,'how'] and d[0]!='_':
                                    broken('join',joinCrit,f"unknown join parameter {d}")
                            joinTab = ''
                            joinCol = None
                            if 'table' in joinCrit:
                                joinTab = joinCrit['table']
                            if  'on' in joinCrit:
                                joinCol = joinCrit['on']
                            if  True in joinCrit:  # borked 'on'
                                joinCrit['on'] = joinCrit[True]
                                joinCol = joinCrit[True]
                        else:
                            broken('join',joinCrit,f"join directive {joinCrit} needs a table and on field name")
                        if 'how' in joinCrit:
                            if joinCrit['how'] not in ['left','right','outer','inner','cross']:
                                broken('join',joinCrit, "only 'left','right','outer','inner' and 'cross' are accepted join methods")
                        if joinTab in savedViews:
                            (joinDF,joinModel,_) = savedViews[joinTab]
                        elif joinTab.isupper():
                            joinDF = self._RACFobject.table(joinTab)
                        else:
                            joinDF = getattr(self._RACFobject,joinTab)
                        if isinstance(joinDF,pd.DataFrame):
                            tbColumns = tbColumns.union(joinDF.columns)  # field names available in find/skip/test
                            if joinCol:
                                names = nameInColumns(tbDF,joinCol,returnAll=True)
                                if tbDefined and len(names)==1:
                                     tbCrit['_refFields'].append(joinCol)
                                elif len(names)==0:
                                    broken('join',joinCrit,f"column name in join directive {joinCrit} not found")
                                elif len(names)>1:
                                    broken('join',joinCrit,f"column name in join directive {joinCrit} ambiguous, found ','.join(joincols)")
                                else:
                                    broken('join',joinCrit,f"column name in join directive {joinCrit} unusable")
                        else:
                            broken('join',joinCrit,f"join directive {joinCrit} contains non-existing table name")

                    for (action,actCrit) in tbCrit.items():
                        if action[0:4]=='find': action = 'find'
                        elif action[0:4]=='skip': action = 'skip'
                        else: continue

                        for fldCrit in listMe(actCrit):
                            if not isinstance(fldCrit,dict):
                                broken('filter',fldCrit,'each of criteria should be a dict')
                            for section in fldCrit.keys():
                                if section not in ['field','fit','value','rule','eq','ne'] and section[0]!='_':
                                    broken('filter',fldCrit,f"unsupported section {section} in {action}")
                            if 'field' not in fldCrit:
                                broken('filter',fldCrit,f"field must be specified in filter {fldCrit}")
                            elif fldCrit['field'].find('(')!=-1:
                                broken('field',fldCrit['field'],f"remove parentheses from matched field in filter {fldCrit}")
                            if not('fit' in fldCrit or 'value' in fldCrit or 'eq' in fldCrit or 'eq' in fldCrit):
                                broken('filter',fldCrit,f"fit, value, eq or ne should be specified in filter {fldCrit}")

                            if 'fit' in fldCrit and fldCrit['fit'] not in self._domains:
                                broken('fit',fldCrit['fit'],f"domain name {fldCrit['fit']} in filter not defined")
                            if 'value' in fldCrit and isinstance(fldCrit['value'],bool):
                                broken('value',fldCrit['field'],f"yaml text string {fldCrit['value']} for {fldCrit['field']} is not a str")

                            for fN in ['field','eq','ne']:
                                if fN in fldCrit:
                                    names = nameInColumns(None,fldCrit[fN],columns=tbColumns,returnAll=True)
                                    if tbDefined and len(names)==1:
                                         tbCrit['_refFields'].append(fldCrit[fN])
                                         if names[0] in tbDF.columns:
                                             fldCrit['_'+fN+'_early'] = True
                                    elif matchFields and fldCrit[fN] in matchFields:
                                         fldCrit['_'+fN+'_matched'] = True
                                    elif tbDefined:
                                        broken('field',fldCrit[fN],f"field name {fldCrit[fN]} not found in {tbName} or match definition")

                    if 'save' in tbCrit:
                        if isinstance(tbNames,str) or (isinstance(tbNames,list) and len(tbNames)==1):
                            savedViews[tbCrit['save']] = (tbDF, tbModel, tbCrit)
                        else:
                            broken('save',tbCrit['save'],f"save: supported for 1 input table, {tbNames} has more than 1")

                    if 'test' in tbCrit:
                        for fldCrit in listMe(tbCrit['test']):
                            if not isinstance(fldCrit,dict):
                                broken('test',fldCrit,'each of criteria should be a dict')
                            for section in fldCrit.keys():
                                if section not in ['field','fit','value','action','rule','id','eq','ne'] and section[0]!='_':
                                    broken('test',fldCrit,f"unsupported section {section} in {action}")
                            if 'field' not in fldCrit:
                                broken('test',fldCrit,f"field must be specified in test {fldCrit}")
                            elif fldCrit['field'].find('(')!=-1:
                                broken('field',fldCrit['field'],f"remove parentheses from matched field in filter {fldCrit}")
                            if not('fit' in fldCrit or 'value' in fldCrit or 'eq' in fldCrit or 'ne' in fldCrit):
                                broken('test',fldCrit,f"fit or value must be specified in test {fldCrit}")

                            for fN in ['field','eq','ne']:
                                if fN in fldCrit:
                                    names = nameInColumns(None,fldCrit[fN],columns=tbColumns,returnAll=True)
                                    if tbDefined and len(names)==1:
                                         tbCrit['_refFields'].append(fldCrit[fN])
                                    elif matchFields and fldCrit[fN] in matchFields:
                                         fldCrit['_'+fN+'_matched'] = True
                                    elif tbDefined:
                                        broken('field',fldCrit[fN],f"field name {fldCrit[fN]} not found in {tbName} or match definition")
                            if 'fit' in fldCrit and fldCrit['fit'] not in self._domains:
                                broken('fit',fldCrit['fit'],f"domain name {fldCrit['fit']} in test not defined")
                            if 'value' in fldCrit and isinstance(fldCrit['value'],bool):
                                broken('value',fldCrit['field'],f"yaml text string {fldCrit['value']} for {fldCrit['field']} is not a str")
                            if 'action' in fldCrit and fldCrit['action'].upper() not in ['FAILURE','FAIL','F','V']:
                                broken('action',fldCrit['field'],f"action {fldCrit['action']} for {fldCrit['field']} not recorgnized")
                    elif 'save' in tbCrit:
                        pass
                    else:
                        broken('rule',tbRuleName,f'no output directive found in {tbRuleName}, save or test expected')

                    tbCrit['_refFields'] = list(set(tbCrit['_refFields']))
                    # update tbCrit where view was created with the referenced field names
                    if tbName in savedViews:
                        (_,_,defCrit) = savedViews[tbName]
                        defCrit['_refFields'].extend(tbCrit['_refFields'])
                    if 'join' in tbCrit and joinTab in savedViews:
                        (_,_,defCrit) = savedViews[joinTab]
                        defCrit['_refFields'].extend(tbCrit['_refFields'])

        self._rules['_rules parsed, checked and normalized'] = ['',{}]

        if not brokenList and confirm:
            brokenList.append(dict(field='rules', value='OK', comment='No problem found in rules'))
        return RuleFrame(brokenList)
