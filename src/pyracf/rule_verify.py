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
    rules can be passed as a list of tuples, or dict via parameter, or as function result from external module.
    '''

    def load_rules(self, rules=None, domains=None, module=None, reset=False, defaultmodule=".profile_field_rules"):
        ''' load rules + domains from structure or from packaged module '''

        if reset and hasattr(self,'_verify'):  # clear prior load
            del self._verify

        if not((rules and domains) or module or hasattr(self,'_verify')):  # no complete parameters, no prior load?
            module = defaultmodule  # backstop

        if rules and domains: pass  # got everything, ignore module and history
        elif hasattr(self,'_verify') and not module:  # get missing component(s) from prior load
            if not rules:
                rules = self._verify['rules']
            if not domains:
                domains = self._verify['domains']
        else:  # get the missing component(s) from module
            ruleset = importlib.import_module(module, package="pyracf")
            ruleset = importlib.reload(ruleset)  # reload module for easier test of modifications
            if not rules:
                rules = ruleset.rules(self)
            if not domains:
                domains = ruleset.domains(self,pd)  # needs pandas

        if rules and type(rules)==str:
            rules = yaml.safe_load(rules)

        self._verify = dict(rules=rules, domains=domains)

        return self

    def verify(self, rules=None, domains=None, module=None, reset=False, id='manual'):
        ''' verify fields in profiles against the expected value, issues are returned in a df '''

        if rules or domains or module or reset:
            self.load_rules(rules, domains, module, reset)

        if not (hasattr(self,'_verify') and 'rules' in self._verify and 'domains' in self._verify):
            raise TypeError('rules and domains must be loaded before running verify')

        if id not in ['manual','off']:
            raise TypeError('issue id must be manual or off')

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
                return self._verify['domains'][item]
            except KeyError:
                warnings.warn(f"fit argument {item} not in domain list, try {readableList(self._verify['domains'].keys())} instead")
                return []

        columns = ['CLASS','PROFILE','FIELD_NAME','EXPECT','ACTUAL','COMMENT','ID']
        if id=='off':
            columns = columns[:-1]
        brokenSum = RuleFrame(columns=columns)

        for (tbNames,*tbCriteria) in self._verify['rules']:
            for tbName in listMe(tbNames):
                try:
                    tbDF = self.table(tbName)
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
                    actionLocs = {}   # filled by select and -select

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
                        matchPattern = tbCrit['match'].replace('.','\.').replace('*','\*')\
                                                      .replace('(','(?P<').replace(')','>[^.]*)')
                        matched = subjectDF[tbName+'_NAME'].str.extract(matchPattern)  # extract 1 qualifier

                    # filter and -filter use same parser, if these kwds are used, actionLocs are filled
                    # suffix filter and -filter with any character(s) to specify alternative selections

                    for (action,*actCrits) in tbCrit.items(): # should only find 1 item in each tbCrit, but have to access key+value
                        if action[0:6]=='filter': action = 'filter'
                        elif action[0:7]=='-filter': action = '-filter'
                        else: break
                        if action not in actionLocs:
                            actionLocs[action] = pd.array([False] * subjectDF.shape[0])

                        # 1 or more fields can be compared in each select/-select
                        # each field compare consists of 2 or 3 tests (fldLocs) that are AND-ed
                        # result of those AND-ed test are OR-ed into actLocs
                        # entries in subjectDF and in matched must be compared, so combine test results in Locs arrays.
                        # *actCrits supports filter directives with 1 tuple or a list of tuples
                        # listMe(actCrit) helps unrole the list of tuples

                        for actCrit in actCrits:
                            actLocs = pd.array([True] * subjectDF.shape[0])
                            for fldCrit in listMe(actCrit):
                                if 'field' not in fldCrit:
                                    warnings.warn(f'field must be specified in filter {fldCrit}')
                                if not('fit' in fldCrit or 'value' in fldCrit):
                                    warnings.warn(f'fit or value must be specified in filter {fldCrit}')
                                fldLocs = pd.array([False] * subjectDF.shape[0])
                                if matchPattern and fldCrit['field'] in matched.columns:
                                    fldName = fldCrit['field']
                                    fldColumn = matched[fldName]  # look in the match result
                                else:  # not a matching field name in match result
                                    fldName = tbName+'_'+fldCrit['field']
                                    fldColumn = subjectDF[fldName]  # look in the main table
                                if 'fit' in fldCrit:
                                    fldLocs |= fldColumn.gt('') & fldColumn.isin(safeDomain(fldCrit['fit']))
                                if 'value' in fldCrit:
                                    fldLocs |= fldColumn.isin(listMe(fldCrit['value']))
                                actLocs &= fldLocs
                            actionLocs[action] |= actLocs

                    # actual reporting, relies on subjectDF, matched and tbLocs to be aligned.
                    # when test: command is processed, we combine the class, profile and filter commands in tbLocs
                    # the blocks in test: each create a new fldLocs off tbLocs
                    # we run each field, from all tests separately, and combine results in brokenSum

                    if 'test' in tbCrit:
                        tbLocs = pd.array([True] * subjectDF.shape[0])
                        if 'filter' in actionLocs: tbLocs &= actionLocs['filter']
                        if '-filter' in actionLocs: tbLocs &= ~ actionLocs['-filter']

                        for fldCrit in listMe(tbCrit['test']):
                            # test can contain 1 dict or a list of dicts
                            # entries in subjectDF and in matched must be compared, so combine test results in fldLocs array.
                            # final .loc[ ] test is done once in assignment to 'broken' frame.
                            fldLocs = tbLocs
                            if matchPattern and fldCrit['field'] in matched.columns:
                                fldName = fldCrit['field']
                                fldColumn = matched[fldName]  # look in the match result
                            else:  # not a matching field name in match result
                                fldName = tbName+'_'+fldCrit['field']
                                fldColumn = subjectDF[fldName]  # look in the main table
                            if 'fit' in fldCrit:
                                fldLocs &= fldColumn.gt('') & ~ fldColumn.isin(safeDomain(fldCrit['fit']))
                            if 'value' in fldCrit:
                                fldLocs &= ~ fldColumn.isin(listMe(fldCrit['value']))

                            if any(fldLocs):
                                broken = subjectDF.loc[fldLocs].copy()\
                                               .rename({tbName+'_CLASS_NAME':'CLASS', tbName+'_NAME':'PROFILE', fldName:'ACTUAL'},axis=1)
                                if tbEntity!='GR':
                                    broken['CLASS'] = tbClassName
                                if matchPattern:
                                    broken['ACTUAL'] = matched[fldName]
                                broken['FIELD_NAME'] = fldName
                                broken['EXPECT'] = fldCrit['fit'] if 'fit' in fldCrit else simpleListed(fldCrit['value']) if 'value' in fldCrit else '?'
                                broken['COMMENT'] = fldCrit['comment'] if 'comment' in fldCrit else tbCrit['comment'] if 'comment' in tbCrit else ''
                                if id!='off':
                                    broken['ID'] = fldCrit['id'] if 'id' in fldCrit else tbCrit['id'] if 'id' in tbCrit else ''
                                brokenSum = pd.concat([brokenSum,broken[brokenSum.columns]],
                                                       sort=False, ignore_index=True)
                    else:
                        warnings.warn(f'missing test directive in {tbCrit}')

        return RuleFrame(brokenSum)

    def syntax_check(self, confirm=False):
        ''' check rules and domains for consistency and unknown directives
            specify confirm=True to get a message when all is OK '''

        def broken(field,value,comment):
            brokenList.append(dict(FIELD=field, VALUE=value, COMMENT=comment))

        brokenList = []

        for (tbNames,*tbCriteria) in self._verify['rules']:
            for tbName in listMe(tbNames):
                tbDF = self.table(tbName)
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
                        if action not in ['class','-class','profile','-profile','match','test','comment','id']:
                            if action[0:6]!='filter' and action[0:7]!='-filter':
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
                        if action[0:6]=='filter': action = 'filter'
                        elif action[0:7]=='-filter': action = '-filter'
                        else: break

                        if type(actCrits)!=list:
                            broken('filter',actCrit,'filter should have a list of criteria')

                        for actCrit in actCrits:
                            for fldCrit in listMe(actCrit):
                                if type(fldCrit)!=dict:
                                    broken('filter',fldCrit,'each of criteria should be a dict')
                                for section in fldCrit.keys():
                                    if section not in ['field','fit','value','comment']:
                                        broken('filter',fldCrit,f"unsupported section {section} in {action}")
                                if 'field' not in fldCrit:
                                    broken('filter',fldCrit,f"field must be specified in filter {fldCrit}")
                                if not('fit' in fldCrit or 'value' in fldCrit):
                                    broken('filter',fldCrit,f"fit or value must be specified in filter {fldCrit}")
    
                                if tbDefined and tbName+'_'+fldCrit['field'] not in tbDF.columns:
                                    if matchFields and fldCrit['field'] in matchFields: pass
                                    else:
                                        broken('field',fldCrit['field'],f"field name {fldCrit['field']} not found in {tbName} or match definition")
                                if 'fit' in fldCrit and fldCrit['fit'] not in self._verify['domains']:
                                    broken('fit',fldCrit['fit'],f"domain name {fldCrit['fit']} in filter not defined")

                    if 'test' not in tbCrit:
                        broken('test',tbCrit,'test directive missing, no output will be generated')
                    else:
                        for fldCrit in listMe(tbCrit['test']):
                            if type(fldCrit)!=dict:
                                broken('test',fldCrit,'each of criteria should be a dict')
                            for section in fldCrit.keys():
                                if section not in ['field','fit','value','comment','id']:
                                    broken('test',fldCrit,f"unsupported section {section} in {action}")
                            if 'field' not in fldCrit:
                                broken('test',fldCrit,f"field must be specified in test {fldCrit}")
                            if not('fit' in fldCrit or 'value' in fldCrit):
                                broken('test',fldCrit,f"fit or value must be specified in test {fldCrit}")

                            if tbDefined and tbName+'_'+fldCrit['field'] not in tbDF.columns:
                                if matchFields and fldCrit['field'] in matchFields: pass
                                else:
                                    broken('field',fldCrit['field'],f"field name {fldCrit['field']} not found in {tbName} or match definition")
                            if 'fit' in fldCrit and fldCrit['fit'] not in self._verify['domains']:
                                broken('fit',fldCrit['fit'],f"domain name {fldCrit['fit']} in test not defined")

        if not brokenList and confirm:
            brokenList.append(dict(field='rules', value='OK', comment='No problem found in rules'))
        return RuleFrame(brokenList)


class RuleFrame(pd.DataFrame,FrameFilter):
    @property
    def _constructor(self):
        ''' a result of a method is also a RuleFrame  '''
        return RuleFrame

    _verifyFilterKwds = {'resclass':'CLASS', 'profile':'PROFILE', 'field':'FIELD_NAME', 'actual':'ACTUAL', 'found':'ACTUAL', 'expect':'EXPECT', 'fit':'EXPECT', 'value':'EXPECT'}

    def gfilter(df, *selection, **kwds):
        ''' Search profiles using GENERIC pattern on the data fields.  selection can be one or more values, corresponding to data levels of the df.
        alternatively specify the field names via an alias keyword, r.verify().gfilter(field='OWN*') '''
        return df.valueFilter(*selection, **kwds, kwdValues=df._verifyFilterKwds)

    def rfilter(df, *selection, **kwds):
        ''' Search profiles using regex on the data fields.  selection can be one or more values, corresponding to data levels of the df
        alternatively specify the field names via an alias keyword, r.verify().gfilter(field='(OWNER|DFLTGRP)')  '''
        return df.valueFilter(*selection, **kwds, kwdValues=df._verifyFilterKwds, regexPattern=True)

