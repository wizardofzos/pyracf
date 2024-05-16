from .group_structure import GroupStructureTree
from .profile_frame import ProfileFrame
from .rule_verify import RuleFrame
from .utils import deprecated
import warnings

class ProfileSelectionFrame():
    """Data selection methods to retrieve one profile, or profiles from one ProfileFrame, using exact match.

    The parameter(s) to these methods are used as a literal search argument, and return entries that fully match the argument(s).
    Selection criteria have to match the profile exactly, generic patterns are taken as literals.

    These methods typically have a name referring to the singular.

    The number of selection parameters depends on the ProfileFrame, matching the number of index fields in the ProfileFrame.  When you specify a parameter as None or '**', the level is ignored in the selection.

    When the optional parameter ``option='LIST'`` is added, and one profile is returned, the data is returned as a pandas Series instead of a ProfileFrame.
    """

    ### group frames

    def group(self, group=None, option=None) -> ProfileFrame:
        """data frame with 1 record from ``.groups`` when the group is found, or an empty frame.

        Example:
            ``r.group('SYS1')``
        """
        return self._groups._giveMeProfiles(group, option=option)


    ### user frames

    def user(self, userid=None, option=None) -> ProfileFrame:
        """data frame with 1 record from ``.users`` when the user ID is found, or an empty frame.

        Example:
            ``r.user('IBMUSER')``
        """
        return self._users._giveMeProfiles(userid, option=option)

    def connect(self, group=None, userid=None, option=None) -> ProfileFrame:
        '''data frame with record(s) from ``.connectData``, fitting the parameters exactly, or an empty frame.

        Example:
            ``r.connect('SYS1','IBMUSER')``

        If one of the parameters is written as ``None``, or the second parameter is
        omitted, all profiles matching the specified parameter are shown, with
        one index level instead of the 2 index levels that .connectData holds.
        For example, ``r.connect('SYS1')`` shows all users connected to SYS1,
        whereas ``r.connect(None, 'IBMUSER')`` shows all the groups IBMUSER is
        member of. Instead of ``None``, you may specify ``'**'``.

        ``connect('SYS1')`` returns 1 index level with user IDs, ``connect(None,'IBMUSER')`` returns 1 index level with group names
        You can also write ``connect(userid='IBMUSER')`` for the latter.

        You can find all entries in ``.users`` that have a group connection to SYSPROG as follows:

        ``r.users.loc[r.users.USBD_NAME.isin(r.connect('SYSPROG').index)]``

        or

        ``r.users.query("_NAME in @r.connect('SYSPROG').index")``

        These forms use the index structure of ``.connect``, rather than the data,
        giving better speed. The 2nd example references the index field
        ``_NAME`` rather than the data column ``USBD_NAME``.
        '''
        if option=='L' or option=='LIST':
            return self._connectData._giveMeProfiles((group,userid), option=option)
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
                return self._connectData.head(0) # empty frame


    ### dataset frames

    def dataset(self, profile=None, option=None) -> ProfileFrame:
        """data frame with 1 record from ``.datasets`` when a profile is found, fitting the parameters exactly, or an empty frame.

        Example:
            ``r.dataset('SYS1.*.**')``

        To show all dataset profiles starting with SYS1 use:

        ``r.datasets.find('SYS1.**')``
        """
        return self._datasets._giveMeProfiles(profile, option=option)

    def datasetPermit(self, profile=None, id=None, access=None, option=None) -> ProfileFrame:
        """data frame with records from ``.datasetAccess``, fitting the parameters exactly, or an empty frame

        Example:
            ``r.datasetPermit('SYS1.*.**', None, 'UPDATE')``

        This shows all IDs with update access on the ``SYS1.*.**`` profile (if this exists). To show entries from all dataset profiles starting with SYS1 use:

        ``r.datasetAccess.find('SYS1.**', '**', 'UPDATE')``

        or

        ``r.datasets.find('SYS1.**').acl(access='UPDATE')``
        """
        return self._datasetAccess._giveMeProfiles((profile,id,access), option=option)

    def datasetConditionalPermit(self, profile=None, id=None, access=None, option=None) -> ProfileFrame:
        """data frame with records from ``.datasetConditionalAccess``, fitting the parameters exactly, or an empty frame.

        Example:
            ``r.datasetConditionalPermit('SYS1.*.**', None, 'UPDATE')``

        To show entries from all conditional permits for ``ID(*)`` use:

        ``r.datasetConditionalAccess.find('**', '*', '**')``
        """
        return self._datasetConditionalAccess._giveMeProfiles((profile,id,access), option=option)


    ### general resource frames

    def general(self, resclass=None, profile=None, option=None) -> ProfileFrame:
        """data frame with profile(s) from ``.generals`` fitting the parameters exactly, or an empty frame.

        Example:
            ``r.general('FACILITY', 'BPX.**')``

        If one of the parameters is written as ``None`` or ``'**'``, or the second
        parameter is omitted, all profiles matching the specified parameter are shown:

        ``r.general('UNIXPRIV')``

        To show general resource profiles relevant to z/OS UNIX use:

        ``r.generals.find('FACILITY', 'BPX.**')``
        """
        return self._generals._giveMeProfiles((resclass,profile), option=option)

    def generalPermit(self, resclass=None, profile=None, id=None, access=None, option=None) -> ProfileFrame:
        """data frame with records from ``.generalAccess``, fitting the parameters exactly, or an empty frame.

        Example:
            ``r.generalPermit('UNIXPRIV', None, None, 'UPDATE')``

        This shows all IDs with  update access on the any UNIXPRIV profile (if this exists). To show entries from all TCICSTRN profiles starting with CICSP use:

        ``r.generalAccess.find('TCICSTRN', 'CICSP*')``
        """
        return self._generalAccess._giveMeProfiles((resclass,profile,id,access), option=option)

    def generalConditionalPermit(self, resclass=None, profile=None, id=None, access=None, option=None) -> ProfileFrame:
        """data frame with records from ``.generalConditionalAccess`` fitting the parameters exactly, or an empty frame.

        Example:
            ``r.generalConditionalPermit('FACILITY')``

        To show entries from all conditional permits for ``ID(*)`` use one of the following:

        ``r.generalConditionalPermit('**', '**', '*', '**')``

        ``r.generalConditionalPermit(None, None, '*', None)``

        ``r.generalConditionalAccess.find(None, None, '*', None)``

        ``r.generalConditionalAccess.find(None, None, re.compile('\\*'), None)``

        """
        return self._generalConditionalAccess._giveMeProfiles((resclass,profile,id,access), option=option)


class ProfileAnalysisFrame():
    """These properties present a subset of a DataFrame, or the result of DataFrame intersections, to identify points of interest.

    The properties do not support parameters, but you can chain a .find() or .skip() method to filter the results.
    """

    ### group frames

    @property
    def groupsWithoutUsers(self) -> ProfileFrame:
        """DataFrame with all groups that have no user IDs connected (empty groups).
        """
        return self._groups.loc[~self.groups.GPBD_NAME.isin(self._connectData.USCON_GRP_ID)]

    @property
    def ownertree(self) -> GroupStructureTree:
        '''dict with the user IDs that own groups as key, and a list of their owned groups as values.
        if a group in this list owns groups, the entry is replaced by a dict.
        '''
        if not (hasattr(self,"_ownertree") and self._ownertree):
            self._ownertree = GroupStructureTree(self._groups,"GPBD_OWNER_ID")
        return self._ownertree

    @property
    def grouptree(self) -> GroupStructureTree:
        '''dict starting with SYS1, and a list of groups owned by SYS1 as values.
        if a group in this list owns groups, the entry is replaced by a dict.
        because SYS1s superior group is blank/missing, we return the first group that is owned by "".
        '''
        if not (hasattr(self,"_grouptree") and self._grouptree):
            self._grouptree = GroupStructureTree(self._groups,"GPBD_SUPGRP_ID")
        return self._grouptree


    ### user frames

    @property
    def specials(self) -> ProfileFrame:
        """DataFrame (like ``.users``) with all users that have the ‘special attribute’ set.
        Effectively this is the same as the result from:

        ``r.users.loc[r.users['USBD_SPECIAL'] == 'YES']``
        """
        return self._users.loc[self._users['USBD_SPECIAL'] == 'YES']

    @property
    def operations(self) -> ProfileFrame:
        """DataFrame (like ``.users``) with all users that have the ‘operations attribute’ set.
        """
        return self._users.loc[self._users['USBD_OPER'] == 'YES']

    @property
    def auditors(self) -> ProfileFrame:
        """DataFrame with all users that have the ‘auditor attribute’ set.
        """
        return self._users.loc[self._users['USBD_AUDITOR'] == 'YES']

    @property
    def revoked(self) -> ProfileFrame:
        """Returns a DataFrame with all revoked users.
        """
        return self._users.loc[self._users['USBD_REVOKE'] == 'YES']


    ### dataset frames

    @property
    def uacc_read_datasets(self) -> ProfileFrame:
        """DataFrame with all dataset definitions that have a Universal Access of ‘READ’
        """
        return self._datasets.loc[self._datasets.DSBD_UACC=="READ"]
    @property
    def uacc_update_datasets(self) -> ProfileFrame:
        """DataFrame with all dataset definitions that have a Universal Access of ‘UPDATE’
        """
        return self._datasets.loc[self._datasets.DSBD_UACC=="UPDATE"]
    @property
    def uacc_control_datasets(self) -> ProfileFrame:
        """DataFrame with all dataset definitions that have a Universal Access of ‘CONTROL’
        """
        return self._datasets.loc[self._datasets.DSBD_UACC=="CONTROL"]
    @property
    def uacc_alter_datasets(self) -> ProfileFrame:
        """DataFrame with all dataset definitions that have a Universal Access of ‘ALTER’
        """
        return self._datasets.loc[self._datasets.DSBD_UACC=="ALTER"]


    ### general resource frames


    #### cleanup reports

    @property
    def orphans(self) -> tuple:
        '''IDs on access lists with no matching USER or GROUP entities, in a tuple with 2 RuleFrames
        '''
        v = self.rules  # verify object
        return (v.load(rules = [
                (['DSACC','DSCACC'],
                 {'test': {'field':'AUTH_ID', 'fit':'ACLID'}})
                               ] )
                   .verify()
                   .drop(['FIELD_NAME','EXPECT','COMMENT','ID'],axis=1)
                   .rename({'ACTUAL':'AUTH_ID'},axis=1)
               ,
                v.load(rules = [
                (['GRACC','GRCACC'],
                 {'test': {'field':'AUTH_ID', 'fit':'ACLID'}})
                               ] )
                   .verify()
                   .drop(['FIELD_NAME','EXPECT','COMMENT','ID'],axis=1)
                   .rename({'ACTUAL':'AUTH_ID'},axis=1)
               )

    @property
    def orphans_joined(self) -> RuleFrame:
        '''IDs on access lists with no matching USER or GROUP entities, in one combined RuleFrame
        '''
        return self.rules.load(rules = [
                (['DSACC','DSCACC','GRACC','GRCACC'],
                 {'test': {'field':'AUTH_ID', 'fit':'ACLID'}})
                                          ] )\
                   .verify()\
                   .drop(['FIELD_NAME','EXPECT','COMMENT','ID'],axis=1)\
                   .rename({'ACTUAL':'AUTH_ID'},axis=1)\
                   .set_index('AUTH_ID')


class EnhancedProfileFrame():
    """Profile presentation properties that make data easier to report by adding fields to the original ProfileFrame.
    """

    ### user frames

    @property
    def connectData(self) -> ProfileFrame:
        """complete connect group information

        Combines fields from USER profiles (0205) and GROUP profiles (0102). The
        ``GPMEM_AUTH`` field shows group connect authority, whereas all other
        field names start with ``USCON``. This property should be used for most
        connect group analysis, instead of ``.connects`` and ``.groupConnect``.
        """
        warnings.warn('This property is for documentation purposes only and should be superceded by the RACF class property')
        return self._connectData.head(0)


    ### dataset frames

    @property
    def datasets(self) -> ProfileFrame:
        """unspecifiec access columns added to .datasets Frame

        Column ``IDSTAR_ACCESS`` is added by selecting records from ``.datasetAccess`` referencing ``ID(*)``. The higher
        value of ``DSBD_UACC`` and ``IDSTAR_ACCESS`` is stored in ``ALL_USER_ACCESS`` indicating the access level granted to all RACF
        defined users, except when restricted by specific access.
        """
        warnings.warn('This property is for documentation purposes only and should be superceded by the RACF class property')
        return self._datasets.head(0)


    ### general resource frames

    @property
    def generals(self) -> ProfileFrame:
        """unspecifiec access columns added to .generals Frame

        Column ``IDSTAR_ACCESS`` is added by selecting records from ``.generalAccess`` referencing ``ID(*)``. The higher
        value of ``GRBD_UACC`` and ``IDSTAR_ACCESS`` is stored in ``ALL_USER_ACCESS`` indicating the access level granted to all RACF
        defined users, except when restricted by specific access.
        """
        warnings.warn('This property is for documentation purposes only and should be superceded by the RACF class property')
        return self._generals.head(0)

    @property
    def SSIGNON(self) -> ProfileFrame: # GRSIGN
        """combined DataFrame of ``._generalSSIGNON`` and ``.generals``, copying the ``GRBD_APPL_DATA`` field to show if replay protection is available for the passticket.
        """
        return self._generalSSIGNON.join(self._generals['GRBD_APPL_DATA'])


class ProfilePublisher(ProfileSelectionFrame,ProfileAnalysisFrame,EnhancedProfileFrame):
    '''
    straight-forward presentation and easy filtered results of Profile Frames from the RACF object.
    These are hand-crafted additions to the properties automatically defined from _recordtype_info.
    '''

