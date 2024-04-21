import pandas as pd
from .racf_functions import accessKeywords, generic2regex

class AclFrame(pd.DataFrame):
    @property
    def _constructor(self):
        ''' a result of a method is also a ProfileFrame  '''
        return AclFrame

    def gfilter(df, *selection, **kw):
        ''' Search profiles using GENERIC pattern on the data fields.  selection can be one or more values, corresponding to data levels of the df.
        alternatively specify the field namesvia an alias keyword, r.datasets.acl().gfilter(user="IBM*") '''

        _aclFilterKwds = {'user':'USER_ID', 'auth':'AUTH_ID', 'id':'AUTH_ID', 'access':'ACCESS'}
        for s in range(len(selection)):
            if selection[s] not in (None,'**'):
                column = df.columns[s]
                if selection[s]=='*':
                    df = df.loc[df[column]=='*']
                else:
                    df = df.loc[df[column].str.match(generic2regex(selection[s]))]
        for kwd,selection in kw.items():
            if kwd in _aclFilterKwds:
                column =_aclFilterKwds[kwd]
                if selection=='*':
                    df = df.loc[df[column]=='*']
                else:
                    df = df.loc[df[column].str.match(generic2regex(selection))]
            else:
                raise TypeError(f"unknown selection gfilter({kwd}=), try {list(_aclFilterKwds.keys())} instead")
        return df

    def rfilter(df, *selection, **kw):
        ''' Search profiles using regex on the data fields.  selection can be one or more values, corresponding to data levels of the df
        alternatively specify the field namesvia an alias keyword, r.datasets.acl().rfilter(user="I.*R")  '''

        _aclFilterKwds = {'user':'USER_ID', 'auth':'AUTH_ID', 'id':'AUTH_ID', 'access':'ACCESS'}
        for s in range(len(selection)):
            if selection[s] not in (None,'**','.*'):
                column = df.columns[s]
                df = df.loc[df[column].str.match(selection[s])]
        for kwd,selection in kw.items():
            if kwd in _aclFilterKwds:
                column =_aclFilterKwds[kwd]
                if selection not in (None,'**','.*'):
                    df = df.loc[df[column].str.match(selection)]
            else:
                raise TypeError(f"unknown selection rfilter({kwd}=), try {list(_aclFilterKwds.keys())} instead")
        return df


class ProfileFrame(pd.DataFrame):
    ''' properties that are copied to result frames '''
    _metadata = ['_RACFobject','_fieldPrefix']
    
    @property
    def _constructor(self):
        ''' a result of a method is also a ProfileFrame  '''
        return ProfileFrame
    
    def read_pickle(path):
        return ProfileFrame(pd.read_pickle(path))
    
    def to_pickle(self, path):
        ''' ensure RACFobject is not saved in pickle '''
        md = self._metadata
        self._metadata = []
        pd.to_pickle(self,path)
        self._metadata = md

    def gfilter(df, *selection):
        ''' Search profiles using GENERIC pattern on the index fields.  selection can be one or more values, corresponding to index levels of the df '''
        for s in range(len(selection)):
            if selection[s] not in (None,'**'):
                if selection[s]=='*':
                    df = df.loc[df.index.get_level_values(s)=='*']
                else: 
                    df = df.loc[df.index.get_level_values(s).str.match(generic2regex(selection[s]))]
        return df

    def rfilter(df, *selection):
        ''' Search profiles using refex on the index fields.  selection can be one or more values, corresponding to index levels of the df '''
        for s in range(len(selection)):
            if selection[s] not in (None,'**','.*'):
                df = df.loc[df.index.get_level_values(s).str.match(selection[s])]
        return df

    def giveMeProfiles(df, selection=None, option=None):
        ''' Search profiles using the index fields.  selection can be str or tuple.  Tuples check for group + user id in connects, or class + profile key in generals.
        option controls how selection is interpreted, and how data must be returned:
        None is for (expensive) backward compatibility, returns a df with 1 profile.
        LIST returns a series for 1 profile, much faster and easier to process.
        '''
        if not selection:
            raise StoopidException('profile criteria not specified...')
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
                if not option:  # return DataFrame with profiles
                    return ProfileFrame()
                else:  # return Series 
                    return []
        else:
            raise StoopidException(f'unexpected last parameter {option}')


    def stripPrefix(df, deep=False, prefix=None, setprefix=None):
        ''' strip table prefix from column names, shallow is only in the returned value, deep changes the table.
            prefix can be specified f df._fieldPrefix is unavailable.
            if the ProfileFrame is processed with .merge, _fieldPrefix is lost and can be restored with setprefix parm.  '''
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
        ''' transform {dataset,general}[Conditional]Access table:
        permits=True: show normal ACL (with the groups identified in field USER_ID)
        explode=True: replace all groups with the users connected to the groups (in field USER_ID)
        resolve=True: show user specific permit, or the highest group permit for each user
        admin=True: add the users that have ability to change the groups on the ACL (in field ADMIN_ID)
            VIA identifies the group name, AUTHORITY the RACF privilege involved
        access=access level: show entries that are equal to the level specified, access='CONTROL'
        allows=access level: show entries that are higher or equal to the level specified, allows='UPDATE'
        sort=["user","access","id","admin","profile"] sort the resulting output
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
            raise StoopidException(f'Table {tbName} not supported for acl( ), except DSBD, DSACC, DSCACC, GRBD, GRACC or GRCACC.')

        if tbName in ["DSBD","GRBD"]:
            # profiles selected, add corresp. access + cond.access frames
            tbProfiles = df[[df._fieldPrefix+k for k in tbProfileKeys+["OWNER_ID","UACC"]]].stripPrefix()
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
            tbProfiles = _baseProfiles.loc[tbPermits.droplevel([-2,-1]).index.drop_duplicates()].stripPrefix(setprefix=_baseProfiles._fieldPrefix)
            tbProfiles = tbProfiles[tbProfileKeys+["OWNER_ID","UACC"]]
        else:
            raise StoopidException(f'Table {tbName} not supported for acl( ), except DSBD, DSACC, DSCACC, GRBD, GRACC or GRCACC.')
          
        # tbProfiles and tbPermits have column names without the tbName prefix
        
        returnFields = ["USER_ID","AUTH_ID","ACCESS"]
        if tbName in ["DSCACC","GRCACC"]:
            returnFields = returnFields+["CATYPE","CANAME","NET_ID","CACRITERIA"]

        sortBy = {"user":["USER_ID"]+tbProfileKeys, 
                  "access":["RANKED_ACCESS","USER_ID"],
                  "id":["AUTH_ID"]+tbProfileKeys, 
                  "admin":"ADMIN_ID", 
                  "profile":tbProfileKeys+["USER_ID"]}
        if sort not in sortBy:
            raise StoopidException(f'Sort value {sort} not supported for acl( ), use one of {",".join(sortBy.keys())}.')
        
        if explode or resolve or admin:  # get view of connectData with only one index level (the group name)
            groupMembers = RACFobject._connectData.droplevel(1)

        if explode or resolve:  # get user IDs connected to groups into field USER_ID
            acl = AclFrame(pd.merge(tbPermits, groupMembers[["USCON_NAME"]], how="left", left_on="AUTH_ID", right_index=True))
            acl.insert(3,"USER_ID",acl["USCON_NAME"].where(acl["USCON_NAME"].notna(),acl["AUTH_ID"]))
        elif permits:  # just the userid+access from RACF, add USER_ID column for consistency
            acl = AclFrame(tbPermits)
            acl.insert(3,"USER_ID",acl["AUTH_ID"].where(~ acl["AUTH_ID"].isin(RACFobject._groups.index.values),"-group-"))
        else:
            acl = AclFrame(columns=tbProfileKeys+returnFields)
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
            acl = acl.loc[acl["ACCESS"].map(accessKeywords.index)==accessKeywords.index(access.upper())]
        if allows:
            acl = acl.loc[acl["ACCESS"].map(accessKeywords.index)>=accessKeywords.index(allows.upper())]
        return acl.sort_values(by=sortBy[sort])[tbProfileKeys+returnFields].reset_index(drop=True)

