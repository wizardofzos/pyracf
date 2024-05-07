Release notes
=============

Summary of changes
------------------

0.8.7 (fixes for pickles, pytest, wiki)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- grouptree and ownertree are now properties, no longer callables
- accept '\*' as a literal value in gfilter( )
- r.connect('SYS1') and r.connect(None,'IBMUSER') return one level index
- less contentious column name ALL_USER_ACCESS replaces EFFECTIVE_UACC
- speed up single profile methods 
- Single value selections return dataframe with columns again
- giveMeProfiles, generic2regex are now 'internal' (\_) functions


0.8.5 (fixes for pickles, pytest, wiki)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- parse_fancycli now creates empty data frames for pickles it could not find
- index added to data frames from old pickles, not for pickles that already have index fields
- pytest framework for QA in development cycle, initial tests ensure attributes are the same with all 3 methods to obtain RACF profiles
- wiki https://github.com/wizardofzos/pyracf/wiki

0.8.3 (tree print format for grouptree and ownertree)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- msys.grouptree and msys.ownertree are now properties instead of callables
  print as unix tree or simple format, e.g. print(msys.ownertree)
  default format looks like unix tree, change with msys.ownertree.setformat('simple')
  dict structure accessible through .tree attribute
- .connect('group') and .connect(None,'user') return a (single level) Index with user IDs, resp., groups, connected to the given entity
  this helps with queries that test group membership
- add IDSTAR\_ACCESS and ALL\_USER\_ACCESS to .datasets and .generals with, resp., permitted access on ID(\*) and the higher value of UACC and IDSTAR_ACCESS.
- fixed: correlate also builds internal tables from saved pickles

0.8.2 (property for most application segments)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- application segments for dataset, group and user entities are avaible with entity prefix, e.g., msys.userTSO, msys.datasetDFP, msys.groupOMVS
- system related application segments from general resources are published without prefix, e.g., msys.STDATA or msys.MFA
- old properties msys.installdata and msys.userDistributedMappings are replaced by userUSRDATA and userDistributedIdMappings
- most of these properties are automatically generated

0.8.0 (acl, gfilter, rfilter methods)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- selection method gfilter (supports RACF generic patterns) and rfilter (for regex patterns)
  supports as many parameters as there are index columns in the frame
- reporting method acl, produces frame with access list, may be used on the entity frames or on the access frames
- internal frames _connectByGroup and _connectByUser, as alternate index on connectData
- internal frames _grouptreeLines and _ownertreeLines that return all groups up until SYS1 (or upto a user ID)
- correlate() invoked automatically by parse() and fancycli()

0.7.1 (General instead of Generic)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- fixed: Generic should be General resource profiles, variables and methods renamed
- Mapping between IRRDBU00 record types and variables centralized in a dict
- global constants related to record types removed
- parsed records internally stored by (decimal) record type, instead of by name
- add method to retrieve parsed record count for given name
- \_offsets now a RACF class attribute
- fixed: pickles with a prefix were selected when loading pickles with no prefix
- fixed: status property crashed when used before parse() method used, math.floor call is now conditional
- fixed: record type '0260' in offset.json was malformed
- updated offsets.json from https://www.ibm.com/docs/en/SSLTBW_3.1.0/com.ibm.zos.v3r1.icha300/format.htm etc
- getOffsets.py to update the json model
- fixed: RACF documentation contains incorrect record type 05k0
- all known record types parsed and loaded into DataFrames
- index columns assigned to all DataFrames, assigned by new correlate() method
- new method correlate() to increase speed of subsequent data access, used after parse() or loading of pickles
- new selection methods similar to user() and group(), that work on index fields.
    when a parameter is given as None or '\*\*', elements matching the other parameters are returned:
    datasetPermit and datasetConditionalPermit, with parameters profile(), id() and access() 
    generalPermit and generalConditionalPermit, with parameters resclass(), profile(), id() and access()
    connect with parameters group() and user()
- added GPMEM_AUTH to connectData frame, consolidating all connect info into one line 

0.6.4 (Add 0209)
^^^^^^^^^^^^^^^^

- Added 0209 recordtype to parser. (userDistributedMapping)

0.6.3 (Add fields)
^^^^^^^^^^^^^^^^^^

- Added missing USBD_LEG_PWDHIST_CT, USBD_XPW_PWDHIST_CT, USBD_PHR_ALG, USBD_LEG_PHRHIST_CT, USBD_XPW_PHRHIST_CT, USBD_ROAUDIT and USBD_MFA_FALLBACK to Users dataframe

0.6.2 (Fix XLSX Creation)
^^^^^^^^^^^^^^^^^^^^^^^^^

- With newer versions of XlsxWriter there's no more .save(). Changed to .close()
- Pinned pandas and XlsxWriter versions in setup.py 

0.6.1 (Bug free?)
^^^^^^^^^^^^^^^^^

- XLS generation fully functional again (also for z/VM unloads)
- Oprhan detection working again
- Conditional Dataset Access Records now parsing correctly
- Conditional Dataset Access now correctly pickled :)
- Fixed parsing of GRCACC records (had misparsed AUTH_ID)
- Conditional Generic (General) Records now with correct column name (GRCACC_CLASS_NAME)
  
0.5.4 (Even more recordtypes!!)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- new property: genericConditionalAccess. Will show GRCACC records.
- Fixed some nasty 'default recordtypes' bugs
  
0.5.0 (Pickle FTW!)
^^^^^^^^^^^^^^^^^^^

- new function: save_pickles(path=path, prefix=prefix). Will save all parsed dataframes as pickles (/path/\_prefix\_\*RECORDTYPE\*.pickle)
- Can now initialize RACF object from pickle-folder/prefix. To reuse earlier saves pickle files. See examples below
- parse_fancycli now has two optional arguments (save_pickles and prefix) to also save pickle files after parsing to the directory as specified in save_pickles. The prefix argument is only useed with save\_pickles isn't False

0.4.5 (Fix Community Update Bug, thanks @Martydog)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Group Connections now actually usable :\)

0.4.4
^^^^^^

- Internal constants for all recordtypes
- Improved 'parse_fancycli()'

0.4.3 (Community Update, thanks @Martydog)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Add User Group Connections record 203 
- Add User Installation Data record 204

0.4.2
^^^^^^

- Now XLS generation has more checks (fails gracefully if not all required records parsed, works when only genericAccess parsed)
- Same for Orphan detection
- Recordtype 0503 (General Resource Members/genericMembers) added
