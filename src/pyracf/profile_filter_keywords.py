from .utils import simpleListed

class ProfileFilterKeywords():
    '''generation routines for keywords on find/skip.

    args:
        df (ProfileFrame): frame to filter
        kwd (str): (alias) keyword found in filter command
        sel (str, list): selection value found in filter command

    returns:
        list of field name and field values to use in loc[ ]
    '''

    def add(kwd, entry):
        '''Add alias to map.

        args:
            kwd (str): alias name to use in find/skip on ProfileFrames
            entry (str, callable): processor of alias

        example:
            import pyracf
            from pyracf.profile_filter_keywords import ProfileFilterKeywords
            ProfileFilterKeywords.add('name', 'COLUMN_NAME')
        '''
        ProfileFilterKeywords._map[kwd] = entry

    def _permitsForUserID(df, kwd, sel):
        '''find/skip keyword to select permits given to user ID(s) or any of their connect groups.
        '''
        if df.empty:
            return ['AUTH_ID',[]]
        valid = ['DSACC', 'DSCACC', 'GRACC', 'GRCACC']
        prefix = df._fieldPrefix
        if prefix.strip('_') not in valid:
            raise TypeError(f'{kwd} selector used in {prefix[:-1]} is supported for dataset and general resource access tables {simpleListed(valid)}')
        else:
            userIDs = df._RACFobject.users.find(sel).index
            grpIDs = df._RACFobject.connectData.find(None,sel).index.get_level_values(0)
            aclIDs = set(list(userIDs)+list(grpIDs))
            return [prefix+'AUTH_ID', aclIDs]

    _map = {'permits': _permitsForUserID}
