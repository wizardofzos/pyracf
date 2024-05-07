Data Table Properties
=====================

pyRACF dynamically creates a property for every recordtype it parses
from the IRRDBU00 unload. The properties return a DataFrame of the
recordtype with column names the same as those in the `IBM
Documentation <https://www.ibm.com/docs/en/zos/3.1.0?topic=records-irrdbu00-record-types>`__.
For instance, the unloaded basic-user-information (`record Type
200 <https://www.ibm.com/docs/en/zos/3.1.0?topic=utility-user-record-formats>`__)
will have a column name USBD_NAME to contain the “User ID as taken from
the profile name”.

The following properties directly relate to the recordtypes, and mostly
have field names starting with the value under Prefix.

..
   sphinx doesn't truncate or wrap the Property value when it exceeds the column width,
   so added _static/css/custom.css to make the table render properly.
   and, sigh, github does not seem to support a csv from a file, so we copy the csv inline.

.. _DataFrames:

.. csv-table:: Record types and properties
   :header: "Type", "Prefix", "Property", "Description"
   :widths: 11, 18, 26, 45

	0100,GPBD,groups,Group Basic Data
	0101,GPSGRP,subgroups,Group Subgroups
	0102,GPMEM,connects,Group Members
	0103,GPINSTD,groupUSRDATA,Group Installation Data
	0110,GPDFP,groupDFP,Group DFP Data
	0120,GPOMVS,groupOMVS,Group OMVS Data
	0130,GPOVM,,Group OVM Data
	0141,GPTME,groupTME,Group TME Data
	0151,GPCSD,groupCSDATA,Group CSDATA custom fields
	0200,USBD,users,User Basic Data
	0201,USCAT,userCategories,User Categories
	0202,USCLA,userClasses,User Classes
	0203,USGCON,groupConnect,User Group Connections
	0204,USINSTD,groupConnect,User Installation Data
	0205,USCON,connectData,User Connect Data
	0206,USRSF,userRRSFDATA,RRSF data
	0207,USCERT,userCERTname,user certificate name
	0208,USNMAP,userAssociationMapping,User Associated Mappings
	0209,USDMAP,userAssociationMapping,User Associated Distributed Mappings
	020A,USMFA,userMFAfactor,user Multifactor authentication data
	020B,USMPOL,userMFApolicies,user Multi-factor authentication policies
	0210,USDFP,userDFP,User DFP data
	0220,USTSO,userTSO,User TSO Data
	0230,USCICS,userCICS,User CICS Data
	0231,USCOPC,userCICSoperatorClasses,User CICS Operator Class
	0232,USCRSL,userCICSrslKeys,User CICS RSL keys
	0233,USCTSL,userCICStslKeys,User CICS TSL keys
	0240,USLAN,userLANGUAGE,User Language Data
	0250,USOPR,userOPERPARM,User OPERPARM Data
	0251,USOPRP,userOPERPARMscope,User OPERPARM Scope
	0260,USWRK,userWORKATTR,User WORKATTR Data
	0270,USOMVS,userOMVS,User Data
	0280,USNETV,userNETVIEW,user NETVIEW segment
	0281,USNOPC,userNETVIEWopclass,user OPCLASS
	0282,USNDOM,userNETVIEWdomains,user DOMAINS
	0290,USDCE,,user DCE data
	02A0,USOVM,,user OVM data
	02B0,USLNOT,,LNOTES data
	02C0,USNDS,,NDS data
	02D0,USKERB,,User KERB segment
	02E0,USPROXY,,user PROXY
	02F0,USEIM,,user EIM segment
	02G1,USCSD,userCSDATA,user CSDATA custom fields
	1210,USMFAC,userMFAfactorTags,user Multifactor authentication factor configuration data
	0400,DSBD,datasets,Data Set Basic Data
	0401,DSCAT,datasetCategories,Data Set Categories
	0402,DSCACC,datasetConditionalAccess,Data Set Conditional Access
	0403,DSVOL,,Data Set Volumes
	0404,DSACC,datasetAccess,Data Set Access
	0405,DSINSTD,datasetUSRDATA,Data Set Installation Data
	0406,DSMEM,,Data Set Member Data
	0410,DSDFP,datasetDFP,Data Set DFP Data
	0421,DSTME,datasetTME,Data Set TME Data
	0431,DSCSD,datasetCSDATA,Data Set CSDATA custom fields
	0500,GRBD,datasetCSDATA,General Resource Basic Data
	0501,GRTVOL,generalTAPEvolume,General Resource Tape Volume Data
	0502,GRCAT,generalCategories,General Resources Categories
	0503,GRMEM,generalCategories,General Resource Members
	0504,GRVOL,generalTAPEvolumes,General Resources Volumes
	0505,GRACC,generalTAPEvolumes,General Resource Access
	0506,GRINSTD,generalUSRDATA,General Resource Installation Data
	0507,GRCACC,generalUSRDATA,General Resources Conditional Access
	0508,GRFLTR,DistributedIdFilter,Filter Data
	0509,GRDMAP,DistributedIdMapping,General Resource Distributed Identity Mapping Data
	0510,GRSES,SESSION,General Resources Session Data
	0511,GRSESE,SESSIONentities,General Resources Session Entities
	0520,GRDLF,DLFDATA,General Resources DLF Data
	0521,GRDLFJ,DLFDATAjobnames,General Resources DLF Job Names
	0530,GRSIGN,DLFDATAjobnames,SSIGNON data
	0540,GRST,STDATA,STARTED Class
	0550,GRSV,SVFMR,Systemview
	0560,GRCERT,CERT,Certificate Data
	1560,CERTN,CERTname,general resource certificate information
	0561,CERTR,CERTreferences,Certificate References
	0562,KEYR,KEYRING,Key Ring Data
	0570,GRTME,TME,general resource TME data
	0571,GRTMEC,TMEchild,general resource TME child
	0572,GRTMER,TMEresource,general resource TME resource
	0573,GRTMEG,TMEgroup,general resource TME group
	0574,GRTMEE,TMErole,general resource TME role
	0580,GRKERB,KERB,general resource KERB segment
	0590,GRPROXY,PROXY,general resource PROXY
	05A0,GREIM,EIM,general resource EIM segment
	05B0,GRALIAS,ALIAS,general resource ALIAS group
	05C0,GRCDT,CDTINFO,general resource CDTINFO data
	05D0,GRICTX,ICTX,general resource ICTX segment
	05E0,GRCFDEF,CFDEF,general resource CFDEF data
	05F0,GRSIG,SIGVER,general resource SIGVER data
	05G0,GRCSF,ICSF,general resource ICSF
	05G1,GRCSFK,ICSFsymexportKeylabel,general resource ICSF key label
	05G2,GRCSFC,ICSFsymexportCertificateIdentifier,general resource ICSF certificate identifier
	05H0,GRMFA,MFA,Multifactor factor definition data
	05I0,GRMFP,MFPOLICY,Multifactor Policy Definition data
	05I1,GRMPF,MFPOLICYfactors,user Multifactor authentication policy factors
	05J1,GRCSD,generalCSDATA,General Resources CSDA custom fields
	05K0,GRIDTP,IDTFPARMS,Identity Token data
	05L0,GRJES,JES,JES data


Properties starting with .general are mostly related to access control
profiles that use PERMITs. General resource profiles that represent
(system) tables and switches are stored in properties with names that
reflect the application segment name (in uppercase, optionally followed
by a suffix for lists stored in the segment).

Connect information
-------------------

Connect information is stored in 3 structures in the RACF database.  These structures are represented in 3 properties:

`.connects` and `.groupConnect` present limited information, `.connects` ignores universal groups, and both lack information about group privileges.

Complete information about connections between groups and users, including connect authority, is stored in `.connectData`.

Extra fields added
------------------

Some of these properties have been extended for easier reporting:

.connectData
^^^^^^^^^^^^

Combines fields from USER profiles (0205) and GROUP profiles (0102). The
``GPMEM_AUTH`` field shows group connect authority, whereas all other
field names start with ``USCON``. This property should be used for most
connect group analysis, instead of ``.connects`` and ``.groupConnect``.

.datasets and .generals
^^^^^^^^^^^^^^^^^^^^^^^

Column ``IDSTAR_ACCESS`` is added by selecting records from
``.datasetAccess`` and ``.generalAccess`` referencing ID(\*). The higher
value of *prefix*\ \_UACC and IDSTAR_ACCESS is stored in
``ALL_USER_ACCESS`` indicating the access level granted to all RACF
defined users, except when restricted by specific access.

.SSIGNON
^^^^^^^^

Returns a combined DataFrame of the DataFrames ``._generalSSIGNON`` en
``.generals``, copying the ``GRBD_APPL_DATA`` field to show if replay
protection is available for the passticket.

To view column names in a DataFrame, use ``.columns``

::

   >>> r.STDATA.columns
   Index(['GRST_RECORD_TYPE', 'GRST_NAME', 'GRST_CLASS_NAME', 'GRST_USER_ID',
          'GRST_GROUP_ID', 'GRST_TRUSTED', 'GRST_PRIVILEGED', 'GRST_TRACE'],
         dtype='object')

Data Table Indices
------------------

The data tables have index fields assigned to speed up access to entries
and to determine “is this ID present in the .users table”. Index fields
are automatically assigned (generally) as follows. Note that the table
prefix is omitted from the index names to ease table processing.

-  For tables about groups, users and data sets, the ``_NAME`` field
   refers to the profile key.
-  For general resources, ``_CLASS_NAME`` and ``_NAME`` refer to the
   resource class and the profile key, resp.
-  ``.connectData`` uses ``_GRP_ID`` and ``_NAME`` as index fields,
   representing the group name and the user ID, resp. The other two
   connect related tables use the same structure to facilitate merging
   of tables.
-  ``.datasetAccess`` and ``.datasetConditionalAccess`` use ``_NAME``,
   ``_AUTH_ID`` and ``_ACCESS`` as index fields.
-  ``.generalAccess`` and ``.generalConditionalAccess`` use
   ``_CLASS_NAME``, ``_NAME``, ``_AUTH_ID`` and ``_ACCESS`` as index
   fields.

Tables and views derived from these main tables mostly inherit the index
fields. To check the index names used in a DataFrame, use
``.index.names``

::

   >>> r.STDATA.index.names
   FrozenList(['_CLASS_NAME', '_NAME'])

Data selection methods
----------------------

The data table properties from the first section return all profiles and profile data loaded
from the RACF input source. Since they typically return more than one
entry, the property name represents a plural, such as ``.users``. To
make selections you have to use methods such as ``.loc[ ]``,
``.query( )``, ``.gfilter( )`` or ``rfilter( )``, see :ref:`selection-methods` for guidance and examples.

In addition to the data table properties, data selection methods are
available to retrieve one profile, or profiles from one class, with an
easy syntax. The parameter(s) to these methods are used as a literal
search argument, and return entries that fully match the argument(s), that means, the selection criteria have to be match the profile exactly.
These properties typically have a name referring to the singular.

.group(*groupname*)
^^^^^^^^^^^^^^^^^^^

Returns a data frame with 1 record from ``.groups`` when the group is found,
or an empty frame. For example, ``r.group('SYS1')``

.user(*userid*)
^^^^^^^^^^^^^^^

Returns a data frame with 1 record from ``.users`` when the user ID is
found, or an empty frame. For example, ``r.user('IBMUSER')``

.connect(*groupname*, *userid*)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Returns a data frame with record(s) from ``.connectData``, fitting the
parameters exactly, or an empty frame. For example,
``r.connect('SYS1','IBMUSER')``

If one of the parameters is written as ``None``, or the second parameter is
omitted, all profiles matching the specified parameter are shown, with
one index level instead of the 2 index levels that .connectData holds.
For example, ``r.connect('SYS1')`` shows all users connected to SYS1,
whereas ``r.connect(None, 'IBMUSER')`` shows all the groups IBMUSER is
member of. Instead of ``None``, you may specify ``'**'``.

You can find all entries in .users that have a group connection to
SYSPROG as follows:

::

   r.users.loc[r.users.USBD_NAME.isin(r.connect('SYSPROG').index)]

or

::

   r.users.query("_NAME in @r.connect('SYSPROG').index")

These forms use the index structure of ``.connect``, rather than the data,
giving better speed. The 2nd example references the index field
``_NAME`` rather than the data column ``USBD_NAME``.

.dataset(*key*)
^^^^^^^^^^^^^^^

Returns a data frame with 1 record from ``.datasets`` when a profile is
found, fitting the parameters exactly, or an empty frame. For example,
``r.dataset('SYS1.*.**')``

To show all dataset profiles starting with SYS1 use
``r.datasets.gfilter('SYS1.**')``

.datasetPermit(*key*, *id*, *access*)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Returns a data frame with records from ``.datasetAccess``, fitting the
parameters exactly, or an empty frame. For example,
``r.datasetPermit('SYS1.*.**', None, 'UPDATE')`` shows all IDs with
update access on the SYS1.\*.\*\* profile (if this exists).

To show entries from all dataset profiles starting with SYS1 use
``r.datasetAccess.gfilter('SYS1.**', '**', 'UPDATE')``

or

``r.datasets.gfilter('SYS1.**').acl(access='UPDATE')``


.datasetConditionalPermit(*key*, *id*, *access*)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Returns a data frame with records from ``.datasetConditionalAccess``,
fitting the parameters exactly, or an empty frame. For example,
``r.datasetConditionalPermit('SYS1.*.**', None, 'UPDATE')``

To show entries from all conditional permits for ID(\*) use
``r.datasetConditionalAccess.gfilter('**', '*', '**')``

.general(*resclass*, *key*)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Returns a data frame with profile(s) from ``.generals`` fitting the
parameters exactly, or an empty frame. For example,
``r.general('FACILITY', 'BPX.**')``

If one of the parameters is written as ``None`` or ``'**'``, or the second
parameter is omitted, all profiles matching the specified parameter are
shown. For example, ``r.general('UNIXPRIV')``

To show general resource profiles relevant to z/OS UNIX use
``r.generals.gfilter('FACILITY', 'BPX.**')``

.generalPermit(*resclass*, *key*, *id*, *access*)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Returns a data frame with records from ``.generalAccess``, fitting the
parameters exactly, or an empty frame. For example,
``r.generalPermit('UNIXPRIV', None, None, 'UPDATE')`` shows all IDs with
update access on the any UNIXPRIV profile (if this exists).

To show entries from all TCICSTRN profiles starting with CICSP use
``r.generalAccess.gfilter('TCICSTRN', 'CICSP*')``

.generalConditionalPermit(*resclass*, *key*, *id*, *access*)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Returns a data frame with records from ``.generalConditionalAccess`` fitting
the parameters exactly, or an empty frame. For example,
``r.generalConditionalPermit('FACILITY')``

To show entries from all conditional permits for ID(\*) use one of the following

``r.generalConditionalPermit('**', '**', '*', '**')``

``r.generalConditionalPermit(None, None, '*', None)``

``r.generalConditionalAccess.gfilter(None, None, '*', None)``

``r.generalConditionalAccess.rfilter(None, None, '\*', None)``

Analytic Properties
-------------------

These properties present a subset of a DataFrame, or the result of
DataFrame intersections, to identify points of interest.

.specials
^^^^^^^^^

The ``.specials`` property returns a “USBD” DataFrame (like ``.users``) with
all users that have the ‘special attribute’ set. Effectively this is the
same as the result from

``r.users.loc[r.users['USBD_SPECIAL'] == 'YES']``

.operations
^^^^^^^^^^^

Like the ``.specials`` property but now all the users that have the
‘operations attribute’ set are returned.

.auditors
^^^^^^^^^

Returns a DataFrame with all users that have the ‘auditor attribute’

.revoked
^^^^^^^^

Returns a DataFrame with all revoked users.

.groupsWithoutUsers
^^^^^^^^^^^^^^^^^^^

Returns a DataFrame with all groups that have no user IDs connected
(empty groups).

.uacc_read_datasets
^^^^^^^^^^^^^^^^^^^

Returns a DataFrame with all dataset definitions that have a Universal
Access of ‘READ’

.uacc_update_datasets
^^^^^^^^^^^^^^^^^^^^^

Returns a DataFrame with all dataset definitions that have a Universal
Access of ‘UPDATE’

.uacc_control_datasets
^^^^^^^^^^^^^^^^^^^^^^

Returns a DataFrame with all dataset definitions that have a Universal
Access of ‘CONTROL’

.uacc_alter_datasets
^^^^^^^^^^^^^^^^^^^^

Returns a DataFrame with all dataset definitions that have a Universal
Access of ‘ALTER’

.orphans
^^^^^^^^

Returns a tuple of ``.datasetAccess`` DataFrame and ``.generalAccess``
DataFrame with entries that refer to non-existing authid’s.
