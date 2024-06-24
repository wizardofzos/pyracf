import pandas as pd
from .frame_filter import FrameFilter
from .profile_filter_keywords import ProfileFilterKeywords
from .racf_functions import accessAllows, accessKeywords, generic2regex
from .xls_writers import XlsWriter

class AclFrame(pd.DataFrame, FrameFilter):
    '''output of the .acl() method'''
    @property
    def _constructor(self):
        ''' a result of a method is also a ProfileFrame  '''
        return AclFrame

    _aclFilterKwds = {'user':'USER_ID', 'auth':'AUTH_ID', 'id':'AUTH_ID', 'access':'ACCESS'}

    def find(df, *selection, **kwds):
        '''Search acl entries using GENERIC pattern on the data fields.

        selection can be one or more values, corresponding to data columns of the df.
        alternatively specify the field names via an alias keyword (user, auth, id or access) or column name in upper case::

            r.datasets.acl().find(user="IBM*")

        specify regex using ``re.compile``::

            r.datasets.acl().find( user=re.compile('(IBMUSER|SYS1)') )
        '''
        return df._frameFilter(*selection, **kwds, kwdValues=df._aclFilterKwds, useIndex=False)

    def skip(df, *selection, **kwds):
        '''Exclude acl entries using GENERIC pattern on the data fields.

        selection can be one or more values, corresponding to data columns of the df.
        alternatively specify the field names via an alias keyword (user, auth, id or access) or column name in upper case::

            r.datasets.acl().skip(USER_ID="IBMUSER", ACCESS='ALTER')
        '''
        return df._frameFilter(*selection, **kwds, kwdValues=df._aclFilterKwds, useIndex=False, exclude=True)


class ProfileFrame(pd.DataFrame, FrameFilter, XlsWriter):
    '''pandas frames with RACF profiles, the main properties that the RACF object provides'''
    #properties that are copied to result frames
    _metadata = ['_RACFobject','_fieldPrefix']

    @property
    def _constructor(self):
        '''result of a method is also a ProfileFrame'''
        return ProfileFrame

    def __finalize__(self, other, method=None, **kwargs):
        """propagate metadata from other to self, fixed for pd.concat

        Parameters:
            other : the object from which to get the attributes that we are going to propagate
            method : optional, a passed method name ; possibly to take different types of propagation actions based on this
        """
        if method=='concat':
            # copy metadata from first available concatenation source
            for name in self._metadata:
                if not hasattr(self, name):
                    for x in other.objs:
                        if hasattr(x, name):
                            object.__setattr__(self, name, getattr(x, name))
                            break
        else:
            if isinstance(other,ProfileFrame):
                for name in self._metadata:
                    if not hasattr(self, name) and hasattr(other, name):
                        object.__setattr__(self, name, getattr(other, name))
        return self

    def read_pickle(path):
        return ProfileFrame(pd.read_pickle(path))

    def to_pickle(self, path):
        '''ensure RACFobject is not saved in pickle'''
        md = self._metadata
        self._metadata = []
        pd.to_pickle(self,path)
        self._metadata = md

    # (alias) keywords to use in find/skip
    _profileFilterKwds = ProfileFilterKeywords._map

    def find(df, *selection, **kwds):
        r'''Search profiles using GENERIC pattern on the index fields.

        selection can be one or more values, corresponding to index levels of the df.
        in addition(!), specify field names via an alias keyword or column name::

            r.datasets.find("SYS1.**",UACC="ALTER")

        specify regex using ``re.compile``::

            r.datasets.find(re.compile(r'SYS[12]\..*') )
        '''
        return df._frameFilter(*selection, **kwds, kwdValues=df._profileFilterKwds, useIndex=True)

    def skip(df, *selection, **kwds):
        '''Exclude profiles using GENERIC pattern on the index fields.

        selection can be one or more values, corresponding to index levels of the df
        alternatively, specify field names via an alias keyword or column name::

            r.datasets.skip(DSBD_UACC="NONE")
        '''
        return df._frameFilter(*selection, **kwds, kwdValues=df._profileFilterKwds, useIndex=True, exclude=True)

    def gfilter(df, *selection, **kwds):
        '''Search profiles using GENERIC pattern on the index fields.

        selection can be one or more values, corresponding to index levels of the df

        use ``find()`` for more options
        '''
        return df._frameFilter(*selection, **kwds, useIndex=True)

    def rfilter(df, *selection, **kwds):
        ''' Search profiles using refex on the index fields.

        selection can be one or more values, corresponding to index levels of the df

        use ``find(re.compile('pattern'))`` for more options
        '''
        return df._frameFilter(*selection, **kwds, useIndex=True, regexPattern=True)

    def _giveMeProfiles(df, selection=None, option=None):
        '''Select profiles using the index fields.

        args:
            selection: str or tuple.  Tuples check for group + user id in connects, or class + profile key in generals.
            option: controls how selection is interpreted, and how data must be returned:

              * None is for (expensive) backward compatibility, returns a df with 1 profile.

              * LIST returns a series for 1 profile, much faster and easier to process.
        '''
        if not selection:
            raise TypeError('profile criteria not specified...')
        if option in (None,'LIST','L'):  # return 1 profile
            # 1 string, several strings in a tuple, or a mix of strings and None
            if type(selection)==str and not option:
                selection = [selection]  # [] forces return of a df, not a Series
            elif type(selection)==tuple:
                if any([s in (None,'**') for s in selection]):  # any qualifiers are a mask
                    selection = tuple(slice(None) if s in (None,'**') else s for s in selection),
                else:
                    selection = [selection]
            else:
                pass
            try:
                return df.loc[selection]
            except KeyError:
                if not option:  # return empty DataFrame with all the original columns
                    return df.head(0)
                else:  # return Series
                    return []
        else:
            raise TypeError(f'unexpected last parameter {option}')


    def stripPrefix(df, deep=False, prefix=None, setprefix=None):
        '''remove table prefix from column names, for shorter expressions

        args:
            deep (bool): shallow only changes column names in the returned value, deep=True changes the ProfileFrame.
            prefix (str): specified the prefix to remove if df._fieldPrefix is unavailable.
            setprefix (str): restores _fieldPrefix in the ProfileFrame if it was removed by .merge.

        Save typing with the query() function::

            r.datasets.stripPrefix().query("UACC==['CONTROL','ALTER']")

        '''
        if df.shape==(0,0):
            return df
        prefix = prefix if prefix else setprefix if setprefix else df._fieldPrefix
        if deep:  # reset column names in source frame
            df.columns = [c.replace(prefix,"") for c in df.columns]
            if setprefix:
                 df._fieldPrefix = setprefix
            return df
        else:
            rframe = df.rename({c:c.replace(prefix,"") for c in df.columns}, axis=1)
            if setprefix:
                 rframe._fieldPrefix = setprefix
            return rframe


    def acl(df, permits=True, explode=False, resolve=False, admin=False, access=None, allows=None, sort="profile"):
        '''transform the {dataset,general}[Conditional]Access ProfileFrame into an access control list Frame

        args:
            permits (bool): True: show normal ACL (with the groups identified as ``-group-`` in the USER_ID column).
            explode (bool): True: replace each groups with the users connected to the group (in the USER_ID column).
                A user ID may occur several times in USER_ID with various ACCESS levels.
            resolve (bool): True: show user specific permit, or the highest group permit for each user.
            admin (bool): True: add the users that have ability to change the profile or the groups on the ACL (in the ADMIN_ID column),
                VIA identifies the group name, AUTHORITY the RACF privilege involved.
            access (str): show entries that are equal to the access level specified, e.g., access='CONTROL'.
            allows (str): show entries that are higher or equal to the access level specified, e.g., allows='UPDATE'.
            sort (str): sort the resulting output by column: user, access, id, admin, profile.
        '''
        RACFobject = df._RACFobject

        tbName = df._fieldPrefix.strip('_')
        tbEntity = tbName[0:2]
        if tbName in ["DSBD","DSACC","DSCACC"]:
            tbProfileKeys = ["NAME","VOL"]
            _baseProfiles = RACFobject.table('DSBD')
            _accessLists = RACFobject.table('DSACC')
            _condAccessLists = RACFobject.table('DSCACC')
        elif tbName in ["GRBD","GRACC","GRCACC"]:
            tbProfileKeys = ["CLASS_NAME","NAME"]
            _baseProfiles = RACFobject.table('GRBD')
            _accessLists = RACFobject.table('GRACC')
            _condAccessLists = RACFobject.table('GRCACC')
        else:
            raise TypeError(f'Table {tbName} not supported for acl( ), except DSBD, DSACC, DSCACC, GRBD, GRACC or GRCACC.')

        if tbName in ["DSBD","GRBD"]:
            # profiles selected, add corresp. access + cond.access frames
            tbProfiles = df[[df._fieldPrefix+k for k in tbProfileKeys+["OWNER_ID","UACC"]]].stripPrefix()
            if any(tbProfiles.index.duplicated()):  # result of concatenating tables?
                tbProfiles = tbProfiles.drop_duplicates()
            tbPermits = []
            for tb in [_accessLists, _condAccessLists]:
                if not tb.empty:
                    tbPermits.append(tb.merge(tbProfiles["UACC"], left_index=True, right_index=True).stripPrefix(setprefix=tb._fieldPrefix))
            tbPermits = pd.concat(tbPermits,sort=False)\
                          .drop(["RECORD_TYPE","ACCESS_CNT","UACC"],axis=1)\
                          .fillna(' ')
        elif tbName in ["DSACC","DSCACC","GRACC","GRCACC"]:
            # access frame selected, add profiles from frame tbEntity+BD
            tbPermits = df.stripPrefix()
            tbPermits.drop(["RECORD_TYPE","ACCESS_CNT"],axis=1,inplace=True)
            if any(tbPermits.duplicated()):  # result of concatenating tables?  Need to check conditional columns too, not in index.
                tbPermits = tbPermits.drop_duplicates()
            tbProfiles = _baseProfiles.loc[tbPermits.droplevel([-2,-1]).index.drop_duplicates()].stripPrefix(setprefix=_baseProfiles._fieldPrefix)
            tbProfiles = tbProfiles[tbProfileKeys+["OWNER_ID","UACC"]]
        else:
            raise TypeError(f'Table {tbName} not supported for acl( ), except DSBD, DSACC, DSCACC, GRBD, GRACC or GRCACC.')

        # tbProfiles and tbPermits have column names without the tbName prefix

        returnFields = ["USER_ID","AUTH_ID","ACCESS"]
        conditionalFields = ["CATYPE","CANAME","NET_ID","CACRITERIA"]

        sortBy = {"user":["USER_ID"]+tbProfileKeys,
                  "access":["RANKED_ACCESS","USER_ID"],
                  "id":["AUTH_ID"]+tbProfileKeys,
                  "admin":"ADMIN_ID",
                  "profile":tbProfileKeys+["USER_ID"]}
        if sort not in sortBy:
            raise TypeError(f'Sort value {sort} not supported for acl( ), use one of {",".join(sortBy.keys())}.')

        if explode or resolve or admin:  # get view of connectData with only one index level (the group name)
            groupMembers = RACFobject._connectData.droplevel(1)

        if explode or resolve:  # get user IDs connected to groups into field USER_ID
            acl = AclFrame(pd.merge(tbPermits, groupMembers[["USCON_NAME"]], how="left", left_on="AUTH_ID", right_index=True))
            acl.insert(3,"USER_ID",acl["USCON_NAME"].where(acl["USCON_NAME"].notna(),acl["AUTH_ID"]))
        elif permits:  # just the userid+access from RACF, add USER_ID column for consistency
            acl = AclFrame(tbPermits)
            acl.insert(3,"USER_ID",acl["AUTH_ID"].where(~ acl["AUTH_ID"].isin(RACFobject._groups.index.values),"-group-"))
        else:
            acl = AclFrame(tbPermits.head(0))
            if not admin:  # no option that produces data?
                return acl  # give up early, prevent KeyErrors due to empty tables

        if permits or explode or resolve:  # add -uacc- pseudo access
            uacc = tbProfiles.query("UACC!='NONE'").copy()
            if not uacc.empty:
                uacc["OWNER_ID"] = "-uacc-" # is renamed to AUTH_ID
                uacc["USER_ID"] = "-uacc-"
                uacc = uacc.rename({"OWNER_ID":"AUTH_ID","UACC":"ACCESS"},axis=1)
                acl = pd.concat([acl,uacc], ignore_index=True, sort=False).fillna(' ') # lose index b/c concat doesn't support us

        if resolve or sort=="access":
            # map access level to number, add 10 for user permits so they override group permits in sort_values( )
            acl["RANKED_ACCESS"] = acl["ACCESS"].map(accessKeywords.index)
            acl["RANKED_ACCESS"] = acl["RANKED_ACCESS"].where(acl["USER_ID"]!=acl["AUTH_ID"], acl["RANKED_ACCESS"]+10)
        if resolve:
            # keep highest value of RANKED_ACCESS, this is at least twice as fast as using .iloc[].idxmax()
            condAcc = ["CATYPE","CANAME"] if "CATYPE" in acl.columns else []
            acl = acl.sort_values(tbProfileKeys+["USER_ID"]+condAcc+["RANKED_ACCESS"])\
                     .drop_duplicates(tbProfileKeys+["USER_ID"]+condAcc, keep='last')
        if sort=="access":
            acl.RANKED_ACCESS = 10 - (acl.RANKED_ACCESS % 10)  # highest access first

        if admin:
            # owner of the profile, or group special, or group authority
            # users who own the profiles
            profile_userowners = pd.merge(tbProfiles, RACFobject._users["USBD_NAME"],
                                          how="inner", left_on="OWNER_ID", right_index=True)\
                                   .rename({"OWNER_ID":"ADMIN_ID"},axis=1)\
                                   .drop(["USBD_NAME","UACC"],axis=1)
            profile_userowners["AUTHORITY"] = "OWNER"
            profile_userowners["VIA"] = "-profile-"
            profile_userowners["ACCESS"] = "-owner-"

            # groups that own the profiles
            profile_groupowner1 = pd.merge(tbProfiles, RACFobject._groups[["GPBD_NAME"]],
                                           how="inner", left_on="OWNER_ID", right_index=True)\
                                    .drop(["GPBD_NAME","UACC"],axis=1)
            profile_groupowner1["ACCESS"] = "-owner-"
            profile_groupowner2 = pd.merge(profile_groupowner1, RACFobject._ownertreeLines, how="inner", left_on="OWNER_ID", right_index=True)\
                                    .drop(["GROUP","OWNER_ID"],axis=1)
            # identify group special on owner group and on any owning group
            profile_groupowner1.rename({"OWNER_ID":"OWNER_IDS"},axis=1,inplace=True)
            # continue with group special processing to find admin users

            # who has administrative authority to modify groups from the ACL?
            admin_owners = pd.merge(tbPermits, RACFobject._groups[["GPBD_NAME","GPBD_OWNER_ID","GPBD_SUPGRP_ID"]],
                                    how="inner", left_on="AUTH_ID", right_index=True)
            admin_owners["USER_ID"] = "-group-"

            # users who own those groups
            admin_gowners = admin_owners.query("GPBD_OWNER_ID != GPBD_SUPGRP_ID")\
                                        .rename({"GPBD_NAME":"VIA","GPBD_OWNER_ID":"ADMIN_ID"},axis=1)\
                                        .drop(["GPBD_SUPGRP_ID"],axis=1)
            admin_gowners["AUTHORITY"] = "OWNER"

            # find all owner groups + groups up to SYS1 or user ID that breaks ownership
            admin_grpspec1 = admin_owners.query("GPBD_OWNER_ID == GPBD_SUPGRP_ID")\
                                         .drop(["GPBD_OWNER_ID","GPBD_SUPGRP_ID"],axis=1)
            admin_grpspec2 = pd.merge(admin_grpspec1, RACFobject._ownertreeLines, how="inner", left_on="AUTH_ID", right_index=True)\
                               .drop(["GPBD_NAME","GROUP"],axis=1)
            admin_grpspec1.rename({"GPBD_NAME":"OWNER_IDS"},axis=1,inplace=True)

            # identify group special on ACL group and on any owning group
            admin_grpspec = pd.merge(pd.concat([admin_grpspec1,admin_grpspec2,profile_groupowner1,profile_groupowner2], sort=False),\
                                     groupMembers[["USCON_NAME","USCON_GRP_ID","USCON_GRP_SPECIAL"]]\
                                             .query('USCON_GRP_SPECIAL == "YES"'),
                                     how="inner", left_on="OWNER_IDS", right_index=True)\
                               .rename({"USCON_NAME":"ADMIN_ID","OWNER_IDS":"VIA"},axis=1)\
                               .drop(["USCON_GRP_ID","USCON_GRP_SPECIAL"],axis=1)
            admin_grpspec["AUTHORITY"] = "GRPSPECIAL"

            # CONNECT or JOIN authority on an ACL group
            admin_grpauth = pd.merge(tbPermits, groupMembers[["USCON_NAME","USCON_GRP_ID","GPMEM_AUTH"]]
                                                 .query('GPMEM_AUTH==["CONNECT","JOIN"]'),
                                     how="inner", left_on="AUTH_ID", right_index=True)\
                              .rename({"USCON_NAME":"ADMIN_ID","USCON_GRP_ID":"VIA","GPMEM_AUTH":"AUTHORITY"},axis=1)
            admin_grpauth["USER_ID"] = "-group-"

            acl = pd.concat([acl,profile_userowners,admin_gowners,admin_grpspec,admin_grpauth],
                            ignore_index=True, sort=False).fillna(' ')
            returnFields += ["ADMIN_ID","AUTHORITY","VIA"]

        if access:
            # acl = acl.loc[acl["ACCESS"].map(accessKeywords.index)==accessKeywords.index(access.upper())]
            acl = acl.loc[acl["ACCESS"]==accessKeywords[accessKeywords.index(access.upper())]]
        if allows:
            # acl = acl.loc[acl["ACCESS"].map(accessKeywords.index)>=accessKeywords.index(allows.upper())]
            # acl = acl.loc[acl["ACCESS"].isin(accessKeywords[accessKeywords.index(allows.upper()):])]
            acl = acl.loc[acl["ACCESS"].isin(accessAllows(allows.upper()))]

        condAcc = conditionalFields if "CATYPE" in acl.columns and any(acl["CATYPE"].gt(' ')) else []
        return acl.sort_values(by=sortBy[sort])[tbProfileKeys+returnFields+condAcc].reset_index(drop=True)

