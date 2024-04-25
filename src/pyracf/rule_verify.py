import importlib.resources
import yaml
import pandas as pd
import warnings
from .racf_functions import generic2regex
from .utils import readableList


class RuleVerifier:
    ''' verify fields in profiles against expected values, issues are returned in a df.
    rules can be passed as a list of tuples, or dict via parameter, or as function result from external module.
    '''

    def load_rules(self, rules=None, domains=None, module=".profile_field_rules"):
        ''' load rules + domains from structure or from packaged module '''

        if not(rules and domains):
            ruleset = importlib.import_module(module, package="pyracf")
            ruleset = importlib.reload(ruleset)  # reload module for easier test of modifications
            if not rules:
                rules = ruleset.rules(self)
            if not domains:
                domains = ruleset.domains(self,pd)  # needs pandas

        if type(rules)==str:
            rules= yaml.safe_load(rules)

        self._verify = dict(rules=rules, domains=domains)
        
        return self

    def verify(self, rules=None, domains=None, module=None):
        ''' verify fields in profiles against the expected value, issues are returned in a df '''

        if rules or domains or module:
            self.load_rules(rules, domains, module)

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

class RuleFrame(pd.DataFrame):
    @property
    def _constructor(self):
        ''' a result of a method is also a RuleFrame  '''
        return RuleFrame

    _verFilterKwds = {'resclass':'CLASS', 'profile':'PROFILE', 'field':'FIELD_NAME', 'value':'VALUE', 'except':'EXPECT', 'found':'EXPECT'}

    def gfilter(df, *selection, **kw):
        ''' Search profiles using GENERIC pattern on the data fields.  selection can be one or more values, corresponding to data levels of the df.
        alternatively specify the field names via an alias keyword, r.verify().gfilter(field='OWN*') '''

        for s in range(len(selection)):
            if selection[s] not in (None,'**'):
                column = df.columns[s]
                if selection[s]=='*' or (selection[s].find('*')==-1 and selection[s].find('%')==-1 ):
                    df = df.loc[df[column]==selection]
                else:
                    df = df.loc[df[column].str.match(generic2regex(selection[s]))]
        for kwd,selection in kw.items():
            if kwd in df._verFilterKwds:
                column = df._verFilterKwds[kwd]
                if selection=='*' or (selection.find('*')==-1 and selection.find('%')==-1 ):
                    df = df.loc[df[column]==selection]
                else:
                    df = df.loc[df[column].str.match(generic2regex(selection))]
            else:
                raise TypeError(f"unknown selection gfilter({kwd}=), try {readableList(df._verFilterKwds.keys())} instead")
        return df

    def rfilter(df, *selection, **kw):
        ''' Search profiles using regex on the data fields.  selection can be one or more values, corresponding to data levels of the df
        alternatively specify the field names via an alias keyword, r.verify().gfilter(field='(OWNER|DFLTGRP)')  '''

        for s in range(len(selection)):
            if selection[s] not in (None,'**','.*'):
                column = df.columns[s]
                df = df.loc[df[column].str.match(selection[s])]
        for kwd,selection in kw.items():
            if kwd in df._verFilterKwds:
                column = df._verFilterKwds[kwd]
                if selection not in (None,'**','.*'):
                    df = df.loc[df[column].str.match(selection)]
            else:
                raise TypeError(f"unknown selection rfilter({kwd}=), try {readableList(df._verFilterKwds.keys())} instead")
        return df

