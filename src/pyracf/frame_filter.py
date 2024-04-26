from .racf_functions import generic2regex
from .utils import readableList

class FrameFilter():
    ''' selection routines used make selections from frames without knowing the index or column names.
    valueFilter relies on the columns in the frame.
    selection can be one or more values, corresponding to data levels of the df.
    alternatively specify the field namesvia an alias keyword, r.datasets.acl().gfilter(user="IBM*")
    kwdValues must be a dict mapping selection keywords to column names.

    indexFilter uses the index fields, allowing one or more generic or regex field patterns.

    entries must match all selection criteria, so to reduce number of compare/regex calls, we iteratively shrink the df by doing repeated .loc[ ] calls.
    specify exclude=True to exclude entries that match all criteria from the result.
    in this case we prune the entries that must be excluded from an intial array, and only call .loc[ ] once. '''

    def valueFilter(df, *selection, kwdValues, exclude=False, regexPattern=False, **kwds):
        ''' Search profiles using GENERIC or regex pattern on the data columns. '''

        skipSelect = (None,'**','.*') if regexPattern else (None,'**')
        if exclude:  # reverse selection, so collect all comparison results
            locs = [True]*len(df)
        for s in range(len(selection)):
            if selection[s] not in skipSelect:
                column = df.columns[s]
                if regexPattern:
                    result = df[column].str.match(selection[s])
                elif selection[s]=='*' or (selection[s].find('*')==-1 and selection[s].find('%')==-1 ):
                    result = df[column]==selection[s]
                else:
                    result = df[column].str.match(generic2regex(selection[s]))
                if exclude:
                    locs &= result
                else:
                    df = df.loc[result]
        for kwd,sel in kwds.items():
            if kwd in kwdValues:
                column = kwdValues[kwd]
                if regexPattern:
                    result = df[column].str.match(sel)
                elif  sel=='*' or (sel.find('*')==-1 and sel.find('%')==-1 ):
                    result = df[column]==sel
                else:
                    result = df[column].str.match(generic2regex(sel))
                if exclude:
                    locs &= result
                else:
                    df = df.loc[result]
            else:
                raise TypeError(f"unknown selection gfilter({kwd}=), try {readableList(kwdValues.keys())} instead")
        if exclude:
            df = df.loc[~ locs]
        return df


    def indexFilter(df, *selection, exclude=False, regexPattern=False):
        ''' Search profiles using GENERIC or regex pattern on the index fields.  selection can be one or more values, corresponding to index levels of the df '''
        skipSelect = (None,'**','.*') if regexPattern else (None,'**')
        if exclude:  # reverse selection, so collect all comparison results
            locs = [True]*len(df)
        for s in range(len(selection)):
            if selection[s] not in skipSelect:
                if regexPattern:
                    result = df.index.get_level_values(s).str.match(selection[s])
                elif selection[s]=='*' or (selection[s].find('*')==-1 and selection[s].find('%')==-1 ):
                    result = df.index.get_level_values(s)==selection[s]
                else: 
                    result = df.index.get_level_values(s).str.match(generic2regex(selection[s]))
                if exclude:
                    locs &= result
                else:
                    df = df.loc[result]
        if exclude:
            df = df.loc[~ locs]
        return df


