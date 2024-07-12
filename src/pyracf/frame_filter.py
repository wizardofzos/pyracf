import re
import pandas as pd
from .racf_functions import generic2regex
from .utils import listMe, readableList

class FrameFilter():
    '''filter routines that select or exclude records from a the 3 DataFrames classes
    '''

    def _frameFilter(df, *selection, kwdValues={}, useIndex=False, exclude=False, regexPattern=False, **kwds):
        '''selection routines find and skip use this to select from frames without knowing the index or column names.

        with useIndex=False: rely on the columns in the frame.
        selection can be one or more values, corresponding to data levels of the df.
        alternatively specify the field names via an alias keyword:
            r.datasets.acl().find(user="IBM*")
        regex selections are supported via a Pattern object:
            r.datasets.find(DSBD_UACC=re.compile('(CONTROL|ALTER)'))
        kwdValues must be a dict mapping selection keywords to column names.

        with useIndex=True: use the index fields, allowing one or more generic or regex field patterns.

        entries must match all selection criteria, so to reduce number of compare/regex calls, we iteratively shrink the df by doing repeated .loc[ ] calls.

        specify exclude=True to exclude entries that match all criteria from the result.
        in this case we prune the entries that must be excluded from an intial array, and only call .loc[ ] once.
        '''

        if not isinstance(df,pd.DataFrame) or df.empty:
            return df

        skipSelect = (None,'**','.*') if regexPattern else (None,'**')
        if exclude:  # reverse selection, so collect all comparison results
            if len(selection)==0 and len(kwds)==0:  # empty skip criteria means don't skip anything
                return df
            locs = pd.Series(True, index=df.index)
        columnSelect = []  # combine column+value from positional and keyword parameters

        if useIndex:
            s = -1
            for sel in selection:
                s += 1
                if sel is None or (isinstance(sel,str) and sel in skipSelect):
                    continue
                elif regexPattern or isinstance(sel,re.Pattern):
                    result = df.index.get_level_values(s).str.match(sel)
                elif isinstance(sel,(list,pd.Index,pd.Series)):
                    result = df.index.get_level_values(s).isin(sel)
                elif len(sel)>2 and sel[0]=='*' and sel[-1]=='*' and sel[1:-1].find('*')==-1:
                    result = df.index.get_level_values(s).str.contains(sel[1:-1])
                elif sel=='*' or (sel.find('*')==-1 and sel.find('%')==-1):
                    result = df.index.get_level_values(s)==sel
                else:
                    result = df.index.get_level_values(s).str.match(generic2regex(sel))

                if exclude:
                    locs &= result
                else:
                    df = df.loc[result]
        else:
            s = -1
            for sel in selection:
                s += 1
                if sel is None or (isinstance(sel,str) and sel in skipSelect):
                    continue
                else:
                    columnSelect.append([df.columns[s],sel])

        for kwd,sel in kwds.items():
            if kwd=='match':
                if hasattr(df,'_fieldPrefix') and df._fieldPrefix[0:2] in ('DS','GR'):
                    if exclude:
                        locs &= df.index.isin(df.match(sel).index)
                    else:
                        df = df.match(sel)
                else:
                    raise TypeError('match keyword only applies to DS (dataset) and GR (general resource) ProfileFrames')
            elif kwd in kwdValues:
                if callable(kwdValues[kwd]):
                    columnSelect.append(kwdValues[kwd](df,kwd,sel))  # function returns [column,selection]
                else:
                    columnSelect.append([kwdValues[kwd],sel])
            elif kwd in df.columns:
                columnSelect.append([kwd,sel])
            elif hasattr(df,'_fieldPrefix') and df._fieldPrefix+kwd in df.columns:
                columnSelect.append([df._fieldPrefix+kwd,sel])
            else:
                 if len(kwdValues)==0:
                     raise TypeError(f"unknown selection filter({kwd}={sel}), try a column name in uppercase instead, with or without prefix")
                 else:
                     raise TypeError(f"unknown selection filter({kwd}={sel}), try {readableList(kwdValues.keys())}, or a column name in uppercase instead, with or without prefix")

        for [column,sel] in columnSelect:
            if regexPattern or isinstance(sel,re.Pattern):
                result = df[column].str.match(sel)
            elif isinstance(sel,str):
                if sel=='**':
                    result = df[column].gt('')
                elif len(sel)>2 and sel[0]=='*' and sel[-1]=='*' and sel[1:-1].find('*')==-1:
                    result = df[column].str.contains(sel[1:-1])
                elif sel=='*' or (sel.find('*')==-1 and sel.find('%')==-1):
                    result = df[column]==sel
                else:
                    result = df[column].str.match(generic2regex(sel))
            elif isinstance(sel,(list,set,tuple,pd.Index,pd.Series)):
                generic = any([s.find('*')>=0 or s.find('%')>=0 for s in sel])
                if generic:
                    sel = '|'.join([generic2regex(s) for s in sel])
                    result = df[column].str.match(sel)
                else:
                    result = df[column].isin(sel)
            else:
                result = df[column]==sel

            if exclude:
                locs &= result
            else:
                df = df.loc[result]

        if exclude:
            df = df.loc[~ locs]
        return df

    def match(df, *selection, show_resource=False):
        """dataset or general resource related records that match a given dataset name or resource.

        Args:
            *selection: for dataset Frames: a dataset name.  for general Frames: a resource name, or a class and a resource name.
                Each of these can be a str, or a list of str.
            show_resource (bool): True: add a column with the resource name in the output Frame

        Returns:
            ProfileFrame with 0 or 1 entries for one resource, several if a list of resources is given

        Example::

          r.datasets.match('SYS1.PROCLIB')

          r.datasets.match(['SYS1.PARMLIB','SYS1.PROCLIB'], show_resource=True)

          r.generals.match('FACILITY', 'BPX.SUPERUSER')

          r.generals.find('FACILITY',match='BPX.SUPERUSER')

        If you have a list of resource names, you can feed this into ``match()`` to obtain a ProfileFrame with a matching profile for each name.
        Next you concatenate these into one ProfileFrame and remove any duplicate profiles::

          resourceList = ['SYS1.PARMLIB','SYS1.PROCLIB']

          profileList = r.datasets.match(resourceList)

        or::

          profileList = pd.concat(
            [r.datasets.match(rname) for rname in resourceList]
                                  ).drop_duplicates()

        or::

          rlist = pd.DataFrame(resourceList, columns=['dsn'])

          profileList = pd.concat(
                  list(rlist.dsn.apply(r.datasets.match))
                                 ).drop_duplicates()

        and apply any of the methods on this profileList, such as::

          profileList.acl(resolve=True, allows='UPDATE')

        Note: the resource name is not included in the output of acl(), so you should specify similar resources in the selection.
        """
        frames = []
        if hasattr(df,'_fieldPrefix'):
            frameType = df._fieldPrefix[0:2]
            if frameType == 'DS':
                if len(selection)!=1:
                    raise TypeError('match keyword requires one parameter containing the data set name')
                else:
                    byQual = {}
                    for q,d in map(lambda dsn: (dsn.split('.',1)[0],dsn), listMe(selection[0])):
                        byQual.setdefault(q,[]).append(d)
                    for qual,dsns in byQual.items():
                        inqual = df.filter(like=qual+'.', axis=0)
                        if not inqual.empty:
                            for sel in dsns:
                                result = inqual.loc[inqual.index.get_level_values(0)==sel]  # check if there is a matching fully qualified
                                if result.empty:
                                    result = inqual[[re.match(x,sel)!=None for x in inqual[''.join([df._fieldPrefix,'NAME'])].apply(generic2regex)]]
                                if show_resource:
                                    result = result.copy()
                                    result['RESOURCE'] = sel
                                # for DSBD we expect 1 profile (or 0), for DSACC and DSCACC we must return all permits for the profile
                                frames.append(result.head(1) if len(result.index.names)==1 else result.loc[[result.index[0][0]]])
                        else:
                            raise ValueError(f'fully qualified data set name expected, with dots between qualifiers, not {selection[0]}')
            elif frameType == 'GR':
                if len(selection)==1:
                    start = df
                    sel = selection[0]
                elif len(selection)==2:
                    if isinstance(selection[0],str):
                        start = df.find(selection[0])
                    else:
                        start = df.loc[selection[0]]
                    sel = selection[1]
                else:
                    raise TypeError('match keyword requires an optional resclass and a parameter containing the resource name')
                if not start.empty:
                    for sel in listMe(sel):
                        result = start.loc[start.index.get_level_values(1)==sel]  # check if there is a matching discrete
                        if result.empty:
                            result = start[[re.match(x,sel)!=None for x in start[''.join([df._fieldPrefix,'NAME'])].apply(generic2regex)]]
                        # find first profile (the first match) for each class, store True/False in array
                        locs = []
                        prevClass = ''
                        for (i0,i1,*rest) in result.index:
                            if i0 != prevClass:
                                prevClass = i0
                                prevResource = i1
                            locs.append(i0==prevClass and i1==prevResource)
                        if show_resource:
                            result = result.loc[locs].copy()
                            result['RESOURCE'] = sel
                            frames.append(result)
                        else:
                            frames.append(result.loc[locs])
            else:
                frames = None

            if frames!=None:
                if len(frames)==0:
                    return df.head(0)
                elif len(frames)==1:
                    return frames[0]
                else:
                    return pd.concat(frames).drop_duplicates()

        raise TypeError('match keyword only applies to DS (dataset) and GR (general resource) ProfileFrames')

