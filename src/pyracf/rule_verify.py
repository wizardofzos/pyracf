import pandas as pd
import importlib.resources
import yaml
import warnings
from .frame_filter import FrameFilter
from .racf_functions import generic2regex
from .utils import readableList


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

    def verify(self, rules=None, domains=None, module=None, reset=False):
        ''' verify fields in profiles against the expected value, issues are returned in a df '''

        if rules or domains or module or reset:
            self.load_rules(rules, domains, module, reset)

        if not (hasattr(self,'_verify') and 'rules' in self._verify and 'domains' in self._verify):
            raise TypeError('rules and domains must be loaded before running verify')
            
        def listMe(item):
            ''' make list in parameters optional when there is only 1 item '''
            return item if type(item)==list else [item]

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


        brokenSum = RuleFrame(columns=['CLASS','PROFILE','FIELD_NAME','EXPECT','VALUE'])
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

                for tbCrit in tbCriteria:
                    candDF = tbDF  # candidates for field checking
                    if 'class' in tbCrit:
                        if tbEntity!='GR':
                            print('only for GR')
                        candDF = candDF.loc[whereIsClass(candDF, tbCrit['class'])]
                    if '-class' in tbCrit:
                        if tbEntity=='GR':
                            candDF = candDF.loc[~ whereIsClass(candDF, tbCrit['-class'])]

                    if 'profile' in tbCrit:
                        candDF = candDF.loc[candDF.index.get_level_values(ixLevel).str.match(generic2regex(tbCrit['profile']))]
                    if '-profile' in tbCrit:
                        candDF = candDF.loc[ ~ candDF.index.get_level_values(ixLevel).str.match(generic2regex(tbCrit['-profile']))]

                    matchPattern = None
                    if 'match' in tbCrit:
                        matchPattern = tbCrit['match'].replace('.','\.').replace('*','\*')\
                                                      .replace('(','(?P<').replace(')','>[^.]*)')
                        matched = candDF[tbName+'_NAME'].str.extract(matchPattern)  # extract 1 qualifier

                    for fldCrit in listMe(tbCrit['test']):
                        # entries in tbDF and in matched must be compared, so combine test results in fldLocs array.
                        # final .loc[ ] test is done once in assignment to 'broken' frame.
                        fldLocs = [True] * candDF.shape[0]
                        fldExpect = fldCrit['expect'] if 'expect' in fldCrit else None
                        fldName = None
                        if matchPattern:
                            if fldCrit['field'] in matched.columns:
                                fldName = fldCrit['field']
                                if fldExpect:
                                    fldLocs &= matched[fldName].gt('') & ~ matched[fldName].isin(self._verify['domains'][fldExpect])
                                if 'or' in fldCrit:
                                    fldLocs &= ~ matched[fldName].isin(listMe(fldCrit['or']))
                        if not fldName:
                            fldName = fldCrit['field'] if fldCrit['field'] in candDF.columns else tbName+'_'+fldCrit['field']
                            if fldExpect:
                                fldLocs &= candDF[fldName].gt('') & ~ candDF[fldName].isin(self._verify['domains'][fldExpect])
                            if 'or' in fldCrit:
                                fldLocs &= ~ candDF[fldName].isin(listMe(fldCrit['or']))

                        if any(fldLocs):
                            broken = candDF.loc[fldLocs].copy()\
                                           .rename({tbName+'_CLASS_NAME':'CLASS', tbName+'_NAME':'PROFILE', fldName:'VALUE'},axis=1)
                            if tbEntity!='GR':
                                broken['CLASS'] = tbClassName
                            if matchPattern:
                                broken['VALUE'] = matched[fldName]
                            broken['FIELD_NAME'] = fldName
                            broken['EXPECT'] = fldExpect
                            brokenSum = pd.concat([brokenSum,broken[brokenSum.columns]],
                                                   sort=False, ignore_index=True)
        return RuleFrame(brokenSum)


class RuleFrame(pd.DataFrame,FrameFilter):
    @property
    def _constructor(self):
        ''' a result of a method is also a RuleFrame  '''
        return RuleFrame

    _verifyFilterKwds = {'resclass':'CLASS', 'profile':'PROFILE', 'field':'FIELD_NAME', 'value':'VALUE', 'found':'VALUE', 'expect':'EXPECT'}

    def gfilter(df, *selection, **kwds):
        ''' Search profiles using GENERIC pattern on the data fields.  selection can be one or more values, corresponding to data levels of the df.
        alternatively specify the field names via an alias keyword, r.verify().gfilter(field='OWN*') '''
        return df.valueFilter(*selection, **kwds, kwdValues=df._verifyFilterKwds)

    def rfilter(df, *selection, **kwds):
        ''' Search profiles using regex on the data fields.  selection can be one or more values, corresponding to data levels of the df
        alternatively specify the field names via an alias keyword, r.verify().gfilter(field='(OWNER|DFLTGRP)')  '''
        return df.valueFilter(*selection, **kwds, kwdValues=df._verifyFilterKwds, regexPattern=True)

