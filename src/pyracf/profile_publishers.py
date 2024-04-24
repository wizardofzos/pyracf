from .profile_frame import ProfileFrame
from .utils import deprecated

class ProfilePublisher():
    ''' straight forward presentation and easy filtered results of Profile Frames from the RACF object.
    these are in hand-crafted additions to the protperties automatically defined from _recordtype_info. '''

    ### user frames

    def user(self, userid=None, pattern=None):
        return self._users.giveMeProfiles(userid, pattern)

    def connect(self, group=None, userid=None, pattern=None):
        ''' connect('SYS1') returns 1 index level with user IDs, connect(None,'IBMUSER') returns 1 index level with group names '''
        if pattern=='L' or pattern=='LIST':
            return self._connectData.giveMeProfiles((group,userid), pattern)
        else:
            if group and (not userid or userid=='**'):
                # with group given, return connected user IDs via index (.loc['group'] strips level(0))
                selection = group
            elif userid and (not group or group=='**'):
                # with user ID given, return connected groups via index (only level(0))
                return self._connectData.loc[(slice(None),userid),].droplevel(1)
            else:
                # with group + user ID given, return 1 entry with all index levels (because only the data columns will be of interest)
                selection = [(group,userid)]
            try:
                return self._connectData.loc[selection]
            except KeyError:
                return ProfileFrame()


    @property
    def userUSRDATA(self):
        # retained here due to deprecated property definition
        return self._userUSRDATA

    installdata = property(deprecated(userUSRDATA,"installdata"))

    @property
    def userDistributedIdMapping(self):
        # retained here due to deprecated property definition
        return self._userDistributedIdMapping

    userDistributedMapping = property(deprecated(userDistributedIdMapping,"userDistributedMapping"))


    @property
    def specials(self):
        return self._users.loc[self._users['USBD_SPECIAL'] == 'YES']

    @property
    def operations(self):
        return self._users.loc[self._users['USBD_OPER'] == 'YES']

    @property
    def auditors(self):
        return self._users.loc[self._users['USBD_AUDITOR'] == 'YES']

    @property
    def revoked(self):
        return self._users.loc[self._users['USBD_REVOKE'] == 'YES']


    ### group frames

    def group(self, group=None, pattern=None):
        return self._groups.giveMeProfiles(group, pattern)

    @property
    def groupsWithoutUsers(self):
        return self._groups.loc[~self.groups.GPBD_NAME.isin(self._connectData.USCON_GRP_ID)]
    

    ### dataset frames
        
    def dataset(self, profile=None, pattern=None):
        return self._datasets.giveMeProfiles(profile, pattern)

    def datasetConditionalPermit(self, profile=None, id=None, access=None, pattern=None):
        return self._datasetConditionalAccess.giveMeProfiles((profile,id,access), pattern)

    def datasetPermit(self, profile=None, id=None, access=None, pattern=None):
        return self._datasetAccess.giveMeProfiles((profile,id,access), pattern)

    @property
    def uacc_read_datasets(self):
        return self._datasets.loc[self._datasets.DSBD_UACC=="READ"]
    @property
    def uacc_update_datasets(self):
        return self._datasets.loc[self._datasets.DSBD_UACC=="UPDATE"]
    @property
    def uacc_control_datasets(self):
        return self._datasets.loc[self._datasets.DSBD_UACC=="CONTROL"]
    @property
    def uacc_alter_datasets(self):
        return self._datasets.loc[self._datasets.DSBD_UACC=="ALTER"]


    ### general resource frames

    @property
    def generals(self, query=None):
        # retained here due to deprecated property definition
        return self._generals

    generics = property(deprecated(generals,"generics"))

    def general(self, resclass=None, profile=None, pattern=None):
        return self._generals.giveMeProfiles((resclass,profile), pattern)

    @property
    def generalMembers(self, query=None):
        # retained here due to deprecated property definition
        return self._generalMembers    

    genericMembers = property(deprecated(generalMembers,"genericMembers"))

    @property
    def generalAccess(self, query=None):
        # retained here due to deprecated property definition
        return self._generalAccess

    genericAccess = property(deprecated(generalAccess,"genericAccess"))
    
    def generalPermit(self, resclass=None, profile=None, id=None, access=None, pattern=None):
        return self._generalAccess.giveMeProfiles((resclass,profile,id,access), pattern)
    
    
    @property
    def generalConditionalAccess(self):
        # retained here due to deprecated property definition
        return self._generalConditionalAccess

    genericConditionalAccess = property(deprecated(generalConditionalAccess,"genericConditionalAccess"))
    
    def generalConditionalPermit(self, resclass=None, profile=None, id=None, access=None, pattern=None):
        return self._generalConditionalAccess.giveMeProfiles((resclass,profile,id,access), pattern)

    @property
    def SSIGNON(self): # GRSIGN
        return self._generalSSIGNON.join(self._generals['GRBD_APPL_DATA'])
