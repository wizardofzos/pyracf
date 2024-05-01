from .racf_functions import generic2regex
from .utils import readableList

class FrameFilter():
    ''' selection routines make selections from frames without knowing the index or column names.
    with useIndex=False: relies on the columns in the frame.
    selection can be one or more values, corresponding to data levels of the df.
    alternatively specify the field names via an alias keyword, r.datasets.acl().gfilter(user="IBM*")
    kwdValues must be a dict mapping selection keywords to column names.

    with useIndex=True: uses the index fields, allowing one or more generic or regex field patterns.

    entries must match all selection criteria, so to reduce number of compare/regex calls, we iteratively shrink the df by doing repeated .loc[ ] calls.
    specify exclude=True to exclude entries that match all criteria from the result.
    in this case we prune the entries that must be excluded from an intial array, and only call .loc[ ] once. '''

    def frameFilter(df, *selection, kwdValues={'':None}, useIndex=False, exclude=False, regexPattern=False, **kwds):

        skipSelect = (None,'**','.*') if regexPattern else (None,'**')
        if exclude:  # reverse selection, so collect all comparison results
            locs = [True]*len(df)
        columnSelect = []  # combine column+value from positional and keyword parameters

        if useIndex:
            s = -1
            for sel in selection:
                s += 1
                if sel not in skipSelect:
                    if regexPattern:
                        result = df.index.get_level_values(s).str.match(sel)
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
                if sel not in skipSelect:
                    columnSelect.append([df.columns[s],sel])

        for kwd,sel in kwds.items():
            if kwd in kwdValues:
                columnSelect.append([kwdValues[kwd],sel])
            elif kwd in df.columns:
                columnSelect.append([kwd,sel])
            elif hasattr(df,'_fieldPrefix') and df._fieldPrefix+kwd in df.columns:
                columnSelect.append([df._fieldPrefix+kwd,sel])
            else:
                 raise TypeError(f"unknown selection filter({kwd}={sel}), try {readableList(kwdValues.keys())}, or a column name in uppercase instead")

        for [column,sel] in columnSelect:
            if regexPattern:
                result = df[column].str.match(sel)
            elif type(sel)==str:
                if sel=='**':
                    result = df[column].gt('')
                elif len(sel)>2 and sel[0]=='*' and sel[-1]=='*' and sel[1:-1].find('*')==-1:
                    result = df[column].str.contains(sel[1:-1])
                elif sel=='*' or (sel.find('*')==-1 and sel.find('%')==-1):
                    result = df[column]==sel
                else:
                    result = df[column].str.match(generic2regex(sel))
            elif type(sel)==list:
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
