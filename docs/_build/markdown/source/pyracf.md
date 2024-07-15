# pyracf package

## Submodules

## pyracf.frame_filter module

### *class* pyracf.frame_filter.FrameFilter

Bases: `object`

filter routines that select or exclude records from a the 3 DataFrames classes

#### match(\*selection, show_resource=False)

dataset or general resource related records that match a given dataset name or resource.

* **Parameters:**
  * **\*selection** – for dataset Frames: a dataset name.  for general Frames: a resource name, or a class and a resource name.
    Each of these can be a str, or a list of str.
  * **show_resource** (*bool*) – True: add a column with the resource name in the output Frame
* **Returns:**
  ProfileFrame with 0 or 1 entries for one resource, several if a list of resources is given

Example:

```default
r.datasets.match('SYS1.PROCLIB')

r.datasets.match(['SYS1.PARMLIB','SYS1.PROCLIB'], show_resource=True)

r.generals.match('FACILITY', 'BPX.SUPERUSER')

r.generals.find('FACILITY',match='BPX.SUPERUSER')
```

If you have a list of resource names, you can feed this into `match()` to obtain a ProfileFrame with a matching profile for each name.
Next you concatenate these into one ProfileFrame and remove any duplicate profiles:

```default
resourceList = ['SYS1.PARMLIB','SYS1.PROCLIB']

profileList = r.datasets.match(resourceList)
```

or:

```default
profileList = pd.concat(
  [r.datasets.match(rname) for rname in resourceList]
                        ).drop_duplicates()
```

or:

```default
rlist = pd.DataFrame(resourceList, columns=['dsn'])

profileList = pd.concat(
        list(rlist.dsn.apply(r.datasets.match))
                       ).drop_duplicates()
```

and apply any of the methods on this profileList, such as:

```default
profileList.acl(resolve=True, allows='UPDATE')
```

Note: the resource name is not included in the output of acl(), so you should specify similar resources in the selection.

## pyracf.getOffsets module

## pyracf.group_structure module

### *class* pyracf.group_structure.GroupStructureTree(df, linkup_field='GPBD_SUPGRP_ID')

Bases: `dict`

dict with group names starting from SYS1 (group tree) or from (multiple) user IDs (owner tree).

Printing these objects, the tree will be formatted as Unix tree (default, or after .setformat(‘unix’) or with mainframe characters (after .setformat(‘simple’).

#### format(format='unix')

return printable tree

* **Parameters:**
  **format** – control character set to use in the tree representation.
  ‘unix’ for smart looking box characters, ‘simple’ for vertical bar and -
* **Returns:**
  printable string

#### setformat(format='unix')

set default format for next print

#### unix_format(branch=None, prefix='')

print groups, prefixed with box characters to show depth

#### simple_format(branch=None, depth=0)

print groups, prefixed with vertical bars to show depth

#### *property* tree

deprecated, the dict is now the default return value of the object

## pyracf.profile_field_rules module

rules for the pyracf.verify() service.
This module is imported from load() on a rules object.
load() expects a dict for domains and for rules, or a yaml str representing these objects.

functions:
: domains: returns the sets of values that can be expected in profile fields and qualifiers.
  rules: specifies where these domain values should be expected.

### pyracf.profile_field_rules.domains(self, pd)

generate a dict (or yaml str) with named lists of values

each domain entry contains a list, array or Series that will be used in .loc[field.isin( )] to verify valid values in profile fields.
keys of the dict are only referenced in the corresponding rules, feel free to change /extend.
self and pd are passed down to access data frames from caller.

### pyracf.profile_field_rules.rules(self, format='yaml')

generate a dict of lists/tuples, each with (list of) table ids, and one or more conditions.

key of the dict names the rule described in the dict entry.

each condition allows class, -class, profile, -profile, find, skip, match and test.

class, -class, profile and -profile are (currently) generic patterns, and select or skip profile/segment/entries.

find and skip can be used to limit the number of rows to process

match extracts fields from the profile key, the capture name should be used in subsequent fields rules.
match changes . to . and \* to \*, so for regex patterns you should use S and +? instead.

test verifies that the value occurs in one of the domains, or a (list of) literal(s).

id and rule document the test at the test level or at the field level within a test.

## pyracf.profile_filter_keywords module

### *class* pyracf.profile_filter_keywords.ProfileFilterKeywords

Bases: `object`

generation routines for keywords on find/skip.

* **Parameters:**
  * **df** ([*ProfileFrame*](#pyracf.profile_frame.ProfileFrame)) – frame to filter
  * **kwd** (*str*) – (alias) keyword found in filter command
  * **sel** (*str* *,* *list*) – selection value found in filter command
* **Returns:**
  list of field name and field values to use in loc[ ]

#### add(entry)

Add alias to map.

* **Parameters:**
  * **kwd** (*str*) – alias name to use in find/skip on ProfileFrames
  * **entry** (*str* *,* *callable*) – processor of alias

### Example

import pyracf
from pyracf.profile_filter_keywords import ProfileFilterKeywords
ProfileFilterKeywords.add(‘name’, ‘COLUMN_NAME’)

## pyracf.profile_frame module

### *class* pyracf.profile_frame.AclFrame(data=None, index: Axes | None = None, columns: Axes | None = None, dtype: Dtype | None = None, copy: bool | None = None)

Bases: `DataFrame`, [`FrameFilter`](#pyracf.frame_filter.FrameFilter)

output of the .acl() method

#### find(\*selection, \*\*kwds)

Search acl entries using GENERIC pattern on the data fields.

selection can be one or more values, corresponding to data columns of the df.
alternatively specify the field names via an alias keyword (user, auth, id or access) or column name in upper case:

```default
r.datasets.acl().find(user="IBM*")
```

specify regex using `re.compile`:

```default
r.datasets.acl().find( user=re.compile('(IBMUSER|SYS1)') )
```

#### skip(\*selection, \*\*kwds)

Exclude acl entries using GENERIC pattern on the data fields.

selection can be one or more values, corresponding to data columns of the df.
alternatively specify the field names via an alias keyword (user, auth, id or access) or column name in upper case:

```default
r.datasets.acl().skip(USER_ID="IBMUSER", ACCESS='ALTER')
```

### *class* pyracf.profile_frame.ProfileFrame(data=None, index: Axes | None = None, columns: Axes | None = None, dtype: Dtype | None = None, copy: bool | None = None)

Bases: `DataFrame`, [`FrameFilter`](#pyracf.frame_filter.FrameFilter), [`XlsWriter`](#pyracf.xls_writers.XlsWriter)

pandas frames with RACF profiles, the main properties that the RACF object provides

#### read_pickle()

#### to_pickle(path)

ensure RACFobject is not saved in pickle

#### find(\*selection, \*\*kwds)

Search profiles using GENERIC pattern on the index fields.

selection can be one or more values, corresponding to index levels of the df.
in addition(!), specify field names via an alias keyword or column name:

```default
r.datasets.find("SYS1.**",UACC="ALTER")
```

specify regex using `re.compile`:

```default
r.datasets.find(re.compile(r'SYS[12]\..*') )
```

#### skip(\*selection, \*\*kwds)

Exclude profiles using GENERIC pattern on the index fields.

selection can be one or more values, corresponding to index levels of the df
alternatively, specify field names via an alias keyword or column name:

```default
r.datasets.skip(DSBD_UACC="NONE")
```

#### gfilter(\*selection, \*\*kwds)

Search profiles using GENERIC pattern on the index fields.

selection can be one or more values, corresponding to index levels of the df

use `find()` for more options

#### rfilter(\*selection, \*\*kwds)

Search profiles using refex on the index fields.

selection can be one or more values, corresponding to index levels of the df

use `find(re.compile('pattern'))` for more options

#### stripPrefix(deep=False, prefix=None, setprefix=None)

remove table prefix from column names, for shorter expressions

* **Parameters:**
  * **deep** (*bool*) – shallow only changes column names in the returned value, deep=True changes the ProfileFrame.
  * **prefix** (*str*) – specified the prefix to remove if df._fieldPrefix is unavailable.
  * **setprefix** (*str*) – restores \_fieldPrefix in the ProfileFrame if it was removed by .merge.

Save typing with the query() function:

```default
r.datasets.stripPrefix().query("UACC==['CONTROL','ALTER']")
```

#### acl(permits=True, explode=False, resolve=False, admin=False, access=None, allows=None, sort='profile')

transform the {dataset,general}[Conditional]Access ProfileFrame into an access control list Frame

* **Parameters:**
  * **permits** (*bool*) – True: show normal ACL (with the groups identified as `-group-` in the USER_ID column).
  * **explode** (*bool*) – True: replace each groups with the users connected to the group (in the USER_ID column).
    A user ID may occur several times in USER_ID with various ACCESS levels.
  * **resolve** (*bool*) – True: show user specific permit, or the highest group permit for each user.
  * **admin** (*bool*) – True: add the users that have ability to change the profile or the groups on the ACL (in the ADMIN_ID column),
    VIA identifies the group name, AUTHORITY the RACF privilege involved.
  * **access** (*str*) – show entries that are equal to the access level specified, e.g., access=’CONTROL’.
  * **allows** (*str*) – show entries that are higher or equal to the access level specified, e.g., allows=’UPDATE’.
  * **sort** (*str*) – sort the resulting output by column: user, access, id, admin, profile.

## pyracf.profile_publishers module

### *class* pyracf.profile_publishers.ProfileSelectionFrame

Bases: `object`

Data selection methods to retrieve one profile, or profiles, from a ProfileFrame, using exact match.

These methods typically have a name referring to the singular.

The parameter(s) to these methods are used as a literal search argument, and return entries that fully match the argument(s).
Selection criteria have to match the profile exactly, generic patterns are taken as literals.

The number of selection parameters depends on the ProfileFrame, matching the number of index fields in the ProfileFrame.
When you specify a parameter as None or ‘\*\*’, the level is ignored in the selection.

The optional parameter `option='LIST'` causes a pandas Series to be returned if there is one matching profile, instead of a ProfileFrame.  This is meant for high-performance, looping applications.

#### group(group=None, option=None)

data frame with 1 record from `.groups` when the group is found, or an empty frame.

### Example

`r.group('SYS1')`

#### user(userid=None, option=None)

data frame with 1 record from `.users` when the user ID is found, or an empty frame.

### Example

`r.user('IBMUSER')`

#### connect(group=None, userid=None, option=None)

data frame with record(s) from `.connectData`, fitting the parameters exactly, or an empty frame.

### Example

`r.connect('SYS1','IBMUSER')`

If one of the parameters is written as `None`, or the second parameter is
omitted, all profiles matching the specified parameter are shown, with
one index level instead of the 2 index levels that .connectData holds.
For example, `r.connect('SYS1')` shows all users connected to SYS1,
whereas `r.connect(None, 'IBMUSER')` shows all the groups IBMUSER is
member of. Instead of `None`, you may specify `'**'`.

`connect('SYS1')` returns 1 index level with user IDs.
`connect(None,'IBMUSER')` or `connect(userid='IBMUSER')` returns 1 index level with group names.

You can find all entries in `.users` that have a group connection to SYSPROG as follows:

`r.users.loc[r.users.USBD_NAME.isin(r.connect('SYSPROG').index)]`

or

`r.users.query("_NAME in @r.connect('SYSPROG').index")`

These forms use the index structure of `.connect`, rather than the data,
giving better speed. The 2nd example references the index field
`_NAME` rather than the data column `USBD_NAME`.

#### dataset(profile=None, option=None)

data frame with 1 record from `.datasets` when a profile is found, fitting the parameters exactly, or an empty frame.

### Example

`r.dataset('SYS1.*.**')`

To show all dataset profiles starting with SYS1 use:

`r.datasets.find('SYS1.**')`

To show the dataset profile covering SYS1.PARMLIB use:

`r.datasets.match('SYS1.PARMLIB')`

To find the access control list (acl) of profiles, use the `.acl()` method on any of these selections, e.g.:

`r.dataset('SYS1.*.**').acl()`

#### datasetPermit(profile=None, id=None, access=None, option=None)

data frame with records from `.datasetAccess`, fitting the parameters exactly, or an empty frame

### Example

`r.datasetPermit('SYS1.*.**', None, 'UPDATE')`

This shows all IDs with update access on the `SYS1.*.**` profile (if this exists). To show entries from all dataset profiles starting with SYS1 use:

`r.datasetAccess.find('SYS1.**', '**', 'UPDATE')`

or

`r.datasets.find('SYS1.**').acl(access='UPDATE')`

#### datasetConditionalPermit(profile=None, id=None, access=None, option=None)

data frame with records from `.datasetConditionalAccess`, fitting the parameters exactly, or an empty frame.

### Example

`r.datasetConditionalPermit('SYS1.*.**', None, 'UPDATE')`

To show entries from all conditional permits for `ID(*)` use:

`r.datasetConditionalAccess.find('**', '*', '**')`

#### general(resclass=None, profile=None, option=None)

data frame with profile(s) from `.generals` fitting the parameters exactly, or an empty frame.

### Example

`r.general('FACILITY', 'BPX.**')`

If one of the parameters is written as `None` or `'**'`, or the second
parameter is omitted, all profiles matching the specified parameter are shown:

`r.general('UNIXPRIV')`

To show the general resource profile controlling dynamic superuser, use:

`r.general('FACILITY').match('BPX.SUPERUSER')`

To show more general resource profiles relevant to z/OS UNIX use:

`r.generals.find('FACILITY', 'BPX.**')`

#### generalPermit(resclass=None, profile=None, id=None, access=None, option=None)

data frame with records from `.generalAccess`, fitting the parameters exactly, or an empty frame.

### Example

`r.generalPermit('UNIXPRIV', None, None, 'UPDATE')`

This shows all IDs with  update access on the any UNIXPRIV profile (if this exists). To show entries from all TCICSTRN profiles starting with CICSP use:

`r.generalAccess.find('TCICSTRN', 'CICSP*')`

#### generalConditionalPermit(resclass=None, profile=None, id=None, access=None, option=None)

data frame with records from `.generalConditionalAccess` fitting the parameters exactly, or an empty frame.

### Example

`r.generalConditionalPermit('FACILITY')`

To show entries from all conditional permits for `ID(*)` use one of the following:

`r.generalConditionalPermit('**', '**', '*', '**')`

`r.generalConditionalPermit(None, None, '*', None)`

`r.generalConditionalAccess.find(None, None, '*', None)`

`r.generalConditionalAccess.find(None, None, re.compile('\*'), None)`

### *class* pyracf.profile_publishers.ProfileAnalysisFrame

Bases: `object`

These properties present a subset of a DataFrame, or the result of DataFrame intersections, to identify points of interest.

The properties do not support parameters, but you can chain a .find() or .skip() method to filter the results.

#### *property* groupsWithoutUsers *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

DataFrame with all groups that have no user IDs connected (empty groups).

#### *property* ownertree *: [GroupStructureTree](#pyracf.group_structure.GroupStructureTree)*

dict with the user IDs that own groups as key, and a list of their owned groups as values.
if a group in this list owns groups, the entry is replaced by a dict.

#### *property* grouptree *: [GroupStructureTree](#pyracf.group_structure.GroupStructureTree)*

dict starting with SYS1, and a list of groups owned by SYS1 as values.
if a group in this list owns groups, the entry is replaced by a dict.
because SYS1s superior group is blank/missing, we return the first group that is owned by “”.

#### *property* specials *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

DataFrame (like `.users`) with all users that have the ‘special attribute’ set.
Effectively this is the same as the result from:

`r.users.loc[r.users['USBD_SPECIAL'] == 'YES']`

#### *property* operations *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

DataFrame (like `.users`) with all users that have the ‘operations attribute’ set.

#### *property* auditors *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

DataFrame with all users that have the ‘auditor attribute’ set.

#### *property* revoked *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

Returns a DataFrame with all revoked users.

#### *property* uacc_read_datasets *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

DataFrame with all dataset definitions that have a Universal Access of ‘READ’

#### *property* uacc_update_datasets *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

DataFrame with all dataset definitions that have a Universal Access of ‘UPDATE’

#### *property* uacc_control_datasets *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

DataFrame with all dataset definitions that have a Universal Access of ‘CONTROL’

#### *property* uacc_alter_datasets *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

DataFrame with all dataset definitions that have a Universal Access of ‘ALTER’

#### *property* orphans *: tuple*

IDs on access lists with no matching USER or GROUP entities, in a tuple with 2 RuleFrames

Legacy code for backward comptibility.
This function demonstrates how to access columns in the raw data frames, though definitely not efficiently.
FIXED: Temporary frames are used to prevent updating the original \_datasetAccess and \_generalAccess frames.
The functionality is also, and generalized, available in RuleVerifier.

### *class* pyracf.profile_publishers.EnhancedProfileFrame

Bases: `object`

Profile presentation properties that make data easier to report by adding fields to the original ProfileFrame.

#### *property* groupOMVS *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

add column `GPOMVS_GID_` into `._groupOMVS` with leading zeros stripped from `GPOMVS_GID`.

#### *property* connectData *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

complete connect group information

Combines fields from USER profiles (0205) and GROUP profiles (0102). The
`GPMEM_AUTH` field shows group connect authority, whereas all other
field names start with `USCON`. This property should be used for most
connect group analysis, instead of `.connects` and `.groupConnect`.

#### *property* userOMVS *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

add column `USOMVS_UID_` into `._userOMVS` with leading zeros stripped from `USOMVS_UID`.

#### *property* datasets *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

unspecifiec access columns added to .datasets Frame

Column `IDSTAR_ACCESS` is added by selecting records from `.datasetAccess` referencing `ID(*)`. The higher
value of `DSBD_UACC` and `IDSTAR_ACCESS` is stored in `ALL_USER_ACCESS` indicating the access level granted to all RACF
defined users, except when restricted by specific access.

#### *property* generals *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

unspecifiec access columns added to .generals Frame

Column `IDSTAR_ACCESS` is added by selecting records from `.generalAccess` referencing `ID(*)`. The higher
value of `GRBD_UACC` and `IDSTAR_ACCESS` is stored in `ALL_USER_ACCESS` indicating the access level granted to all RACF
defined users, except when restricted by specific access.

#### *property* CERT *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

combined DataFrame of `._generalCERT` and `.generals`, copying the `GRBD_UACC` and `GRBD_APPL_DATA` fields to show if the certificate is trusted, and the associated user ID.

#### *property* KEYRING *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

combined DataFrame of `._generalKEYRING` and `.generals`, copying the `GRBD_APPL_DATA` field to show the associated user ID.

#### *property* SSIGNON *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

combined DataFrame of `._generalSSIGNON` and `.generals`, copying the `GRBD_APPL_DATA` field to show if replay protection is available for the passticket.

### *class* pyracf.profile_publishers.ProfilePublisher

Bases: [`ProfileSelectionFrame`](#pyracf.profile_publishers.ProfileSelectionFrame), [`ProfileAnalysisFrame`](#pyracf.profile_publishers.ProfileAnalysisFrame), [`EnhancedProfileFrame`](#pyracf.profile_publishers.EnhancedProfileFrame)

straight-forward presentation and easy filtered results of Profile Frames from the RACF object.
These are hand-crafted additions to the properties automatically defined from \_recordtype_info.

## pyracf.racf_functions module

### pyracf.racf_functions.generic2regex(selection, lenient='%&\*')

Change a RACF generic pattern into regex to match with text strings in pandas cells.

* **Parameters:**
  **lenient** – the characters that are (also) taken to be part of the qualifier.  use lenient=”” to match with dsnames/resources

### pyracf.racf_functions.accessAllows(level=None)

return list of access levels that allow the given access

### Example

`RACF.accessAllows('UPDATE')` returns `[,'UPDATE','CONTROL','ALTER','-owner-']`

for use in pandas `.query("ACCESS in @RACF.accessAllows('UPDATE')")`

### pyracf.racf_functions.rankedAccess(args)

translate access levels into integers, add 10 if permit is for the user ID.

could be used in .apply() but would be called for each row, so very very slow

## pyracf.rule_verify module

### *class* pyracf.rule_verify.RuleFrame(data=None, index: Axes | None = None, columns: Axes | None = None, dtype: Dtype | None = None, copy: bool | None = None)

Bases: `DataFrame`, [`FrameFilter`](#pyracf.frame_filter.FrameFilter)

Output of a verify() action

#### find(\*selection, \*\*kwds)

Search rule results using GENERIC pattern on the data fields.  selection can be one or more values, corresponding to data columns of the df.

alternatively specify the field names via an alias keyword (resclass, profile, field, actual, found, expect, fit, value or id):

`r.rules.load().verify().find(field='OWN*')`

specify selection as regex using re.compile:

`r.rules.load().verify().find( field=re.compile('(OWNER|DFLTGRP)' )`

#### skip(\*selection, \*\*kwds)

Exclude rule results using GENERIC pattern on the data fields.  selection can be one or more values, corresponding to data columns of the df

alternatively specify the field names via an alias keyword (resclass, profile, field, actual, found, expect, fit, value or id):

`r.rules.load().verify().skip(actual='SYS1')`

### *class* pyracf.rule_verify.RuleVerifier(RACFobject)

Bases: `object`

verify fields in profiles against expected values, issues are returned in a df.

rules can be passed as a dict of [tuples or lists], and a dict with domains, via parameter, or as function result from external module.
created from RACF object with the .rules property.

#### load(rules=None, domains=None, module=None, reset=False, defaultmodule='.profile_field_rules')

load rules + domains from yaml str, structure or from packaged module

* **Parameters:**
  * **rules** (*dict* *,* *str*) – dict of tuples or lists with test specifications, or yaml str field that expands into a dict of lists
  * **domains** (*dict* *,* *str*) – one or more domain in a dict(name=[entries]), or in a yaml string
  * **module** (*str*) – name of module that contains functions rules() and domains()
  * **defaultmodule** (*str*) – module name to be used if all parameters are omitted
  * **reset** (*bool*) – clear rules, domains and module in RuleVerifier object, before loading new values
* **Returns:**
  the updated object
* **Return type:**
  [RuleVerifier](#pyracf.rule_verify.RuleVerifier)

Example:

```default
r.rules.load(rules = {'test libraries':
    (['DSBD'],
     {'id': '101',
      'rule': 'Integrity of test libraries',
      'profile': 'TEST*.**',
      'test': [{'field':'UACC', 'value':['NONE','READ']},
              {'field':'WARNING', 'value':'NO'},
              {'field':'NOTIFY_ID', 'fit':'DELETE'}],
     }
    )
                     }
            ).verify()
```

#### add_domains(domains=None)

Add domains to the end of the domain list, from a dict or a yaml string value.

* **Parameters:**
  **domains** (*dict* *,* *str*) – one or more domains in a dict(name=[entries]), or in a yaml string
* **Returns:**
  The updated object
* **Return type:**
  [RuleVerifier](#pyracf.rule_verify.RuleVerifier)

Example:

```default
v = r.rules.load()

v.add_domains({'PROD_GROUPS': ['PRODA','PRODB','PRODCICS'],
               'TEST_GROUPS': ['TEST1','TEST2']})

v.add_domains({'SYS1': r.connect('SYS1').index})
```

#### get_domains(domains=None)

Get domain definitions as a dict, or one entry as a list.

* **Parameters:**
  **str** (*domains*) – name of domain entry to return as list, or None to return all
* **Returns:**
  dict or list

Example:

```default
v.get_domains() # all domains as a dict

v.get_domains('PROD_GROUPS') # one domain as a list
```

#### verify(rules=None, domains=None, module=None, reset=False, id=True, verbose=False, syntax_check=None, optimize='rows cols')

verify fields in profiles against the expected value, issues are returned in a df

* **Parameters:**
  * **id** (*bool*) – False: suppress ID column from the result frame. The values in this column are taken from the id property in rules
  * **syntax_check** (*bool*) – deprecated
  * **verbose** (*bool*) – True: print progress messages
  * **optimize** (*str*) – cols to improve join speed, rows to use pre-selection
* **Returns:**
  Result object (RuleFrame)

Example:

```default
r.rules.load().verify()
```

#### syntax_check(confirm=True)

parse rules and domains, check for consistency and unknown directives, normalize field names

specify confirm=False to suppress the message when all is OK

* **Parameters:**
  **confirm** (*bool*) – False if the success message should be suppressed, so in automated testing the result frame has .empty
* **Returns:**
  syntax messages (RuleFrame)

Example:

```default
r.rules.load().syntax_check()

if r.rules.load().syntax_check(confirm=False).empty:
    print('No syntax errors in default policy')
```

## pyracf.utils module

### pyracf.utils.deprecated(func, oldname)

Wrapper routine to add (deprecated) alias name to new routine (func), supports methods and properties.
Inspired by functools.partial()

### pyracf.utils.listMe(item)

make list in parameters optional when there is only 1 item, similar to the \* unpacking feature in assignments.
as a result you can just: for options in listMe(optioORoptions)

### pyracf.utils.readableList(iter)

print entries from a dict index into a readable list, e.g., a, b or c

### pyracf.utils.simpleListed(item)

print a string or a list of strings with just commas between values

### pyracf.utils.nameInColumns(df, name, columns=[], prefix=None, returnAll=False)

find prefixed column name in a Frame, return whole name, or all names if requested

* **Parameters:**
  * **df** – Frame to find column names, or None
  * **name** (*str* *,* *list*) – name to search for, with prefix or without, or list of names
  * **columns** (*list*) – opt. ignore df parameter, caller has already extracted column names
  * **prefix** (*str* *,* *list*) – opt. verify that column name has the given prefix(es)
  * **returnAll** (*bool*) – always return all matches in a list
* **Returns:**
  fully prefixed column name, or list of column names

## pyracf.xls_writers module

### *class* pyracf.xls_writers.XlsWriter

Bases: `object`

#### accessMatrix2xls(fileName='irrdbu00.xlsx')

create excel file with sheets for each class, lines for each profile and columns for each ID in the access control list.
runs as method on the RACF object, table(‘DSACC’) or table(‘GRACC’)

#### xls(\*\*keywords)

## Module contents

### *class* pyracf.RACF(irrdbu00=None, pickles=None, auto_pickles=False, prefix='')

Bases: [`ProfilePublisher`](#pyracf.profile_publishers.ProfilePublisher), [`XlsWriter`](#pyracf.xls_writers.XlsWriter)

#### STATE_BAD *= -1*

#### STATE_INIT *= 0*

#### STATE_PARSING *= 1*

#### STATE_CORRELATING *= 2*

#### STATE_CORRELATED *= 3*

#### STATE_READY *= 4*

#### *property* status

#### parse_fancycli(recordtypes=None, save_pickles=False, prefix='')

#### parse(recordtypes=None)

#### parse_t(thingswewant=None)

#### parsed(rname)

how many records with this name (type) were parsed

#### table(rname=None)

return table with this name (type)

#### save_pickle(df='', dfname='', path='', prefix='')

#### save_pickles(path='/tmp', prefix='')

#### load_pickles(path='/tmp', prefix='')

#### *property* rules *: [RuleVerifier](#pyracf.rule_verify.RuleVerifier)*

create a RuleVerifier instance

#### getdatasetrisk(profile='')

This will produce a dict as follows:

#### *property* ALIAS *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

general resource ALIAS group (05B0).

#### *property* CDTINFO *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

general resource CDTINFO data (05C0).

#### *property* CERTname *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

general resource certificate information (1560).

#### *property* CERTreferences *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

Certificate References (0561).

#### *property* CFDEF *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

general resource CFDEF data (05E0).

#### *property* DLFDATA *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

General Resources DLF Data (0520).

#### *property* DLFDATAjobnames *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

General Resources DLF Job Names (0521).

#### *property* DistributedIdFilter *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

Filter Data (0508).

#### *property* DistributedIdMapping *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

General Resource Distributed Identity Mapping Data (0509).

#### *property* EIM *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

general resource EIM segment (05A0).

#### *property* ICSF *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

general resource ICSF (05G0).

#### *property* ICSFsymexportCertificateIdentifier *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

general resource ICSF certificate identifier (05G2).

#### *property* ICSFsymexportKeylabel *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

general resource ICSF key label (05G1).

#### *property* ICTX *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

general resource ICTX segment (05D0).

#### *property* IDTFPARMS *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

Identity Token data (05K0).

#### *property* JES *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

JES data (05L0).

#### *property* KERB *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

general resource KERB segment (0580).

#### *property* MFA *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

Multifactor factor definition data (05H0)

#### *property* MFPOLICY *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

Multifactor Policy Definition data (05I0).

#### *property* MFPOLICYfactors *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

user Multifactor authentication policy factors (05I1).

#### *property* PROXY *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

general resource PROXY (0590).

#### *property* SESSION *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

General Resources Session Data (0510).

#### *property* SESSIONentities *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

General Resources Session Entities (0511).

#### *property* SIGVER *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

general resource SIGVER data (05F0).

#### *property* STDATA *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

Record type (0540).

#### *property* SVFMR *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

Record type (0550).

#### *property* TME *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

general resource TME data (0570).

#### *property* TMEchild *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

general resource TME child (0571).

#### *property* TMEgroup *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

general resource TME group (0573).

#### *property* TMEresource *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

general resource TME resource (0572).

#### *property* TMErole *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

general resource TME role (0574).

#### *property* connectData *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

User Connect Data (0205).

#### *property* connects *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

Group Members (0102).

#### *property* datasetAccess *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

Data Set Access (0404).

#### *property* datasetCSDATA *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

Data Set CSDATA custom fields (0431).

#### *property* datasetCategories *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

Data Set Categories (0401).

#### *property* datasetConditionalAccess *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

Data Set Conditional Access (0402).

#### *property* datasetDFP *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

Data Set DFP Data (0410).

#### *property* datasetMember *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

Data Set Member Data (0406).

#### *property* datasetTME *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

Data Set TME Data (0421).

#### *property* datasetUSRDATA *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

Data Set Installation Data (0405).

#### *property* datasetVolumes *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

Data Set Volumes (0403).

#### *property* datasets *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

Data Set Basic Data (0400).

#### *property* generalAccess *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

General Resource Access (0505).

#### *property* generalCSDATA *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

General Resources CSDA custom fields (05J1).

#### *property* generalCategories *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

General Resources Categories (0502).

#### *property* generalConditionalAccess *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

General Resources Conditional Access (0507).

#### *property* generalMembers *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

General Resource Members (0503).

#### *property* generalTAPEvolume *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

General Resource Tape Volume Data (0501).

#### *property* generalTAPEvolumes *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

General Resources Volumes (0504).

#### *property* generalUSRDATA *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

General Resource Installation Data (0506).

#### *property* generals *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

General Resource Basic Data (0500).

#### *property* groupCSDATA *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

Group CSDATA custom fields (0151).

#### *property* groupConnect *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

User Group Connections (0203).

#### *property* groupDFP *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

Group DFP Data (0110).

#### *property* groupOVM *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

Group OVM Data (0130).

#### *property* groupTME *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

Group TME Data (0141).

#### *property* groupUSRDATA *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

Group Installation Data (0103).

#### *property* groups *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

Group Basic Data (0100).

#### *property* subgroups *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

Group Subgroups (0101).

#### *property* userAssociationMapping *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

User Associated Mappings (0208).

#### *property* userCERTname *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

user certificate name (0207).

#### *property* userCICS *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

User CICS Data (0230).

#### *property* userCICSoperatorClasses *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

User CICS Operator Class (0231).

#### *property* userCICSrslKeys *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

User CICS RSL keys (0232).

#### *property* userCICStslKeys *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

User CICS TSL keys (0233).

#### *property* userCSDATA *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

user CSDATA custom fields (02G1).

#### *property* userCategories *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

User Categories (0201).

#### *property* userClasses *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

User Classes (0202).

#### *property* userDCE *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

user DCE data (0290).

#### *property* userDFP *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

User DFP data (0210).

#### *property* userDistributedIdMapping *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

User Associated Distributed Mappings (0209).

#### *property* userEIM *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

user EIM segment (02F0).

#### *property* userKERB *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

User KERB segment (02D0).

#### *property* userLANGUAGE *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

User Language Data (0240).

#### *property* userLNOTES *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

LNOTES data (02B0).

#### *property* userMFAfactor *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

user Multifactor authentication data (020A).

#### *property* userMFAfactorTags *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

user Multifactor authentication factor configuration data (1210).

#### *property* userMFApolicies *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

user Multi-factor authentication policies (020B)

#### *property* userNDS *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

NDS data (02C0).

#### *property* userNETVIEW *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

user NETVIEW segment (0280).

#### *property* userNETVIEWdomains *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

user DOMAINS (0282).

#### *property* userNETVIEWopclass *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

user OPCLASS (0281).

#### *property* userOPERPARM *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

User OPERPARM Data (0250).

#### *property* userOPERPARMscope *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

User OPERPARM Scope (0251).

#### *property* userOVM *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

user OVM data (02A0).

#### *property* userPROXY *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

user PROXY (02E0).

#### *property* userRRSFDATA *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

RRSF data (0206).

#### *property* userTSO *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

User TSO Data (0220).

#### *property* userUSRDATA *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

User Installation Data (0204).

#### *property* userWORKATTR *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

User WORKATTR Data (0260).

#### *property* users *: [ProfileFrame](#pyracf.profile_frame.ProfileFrame)*

User Basic Data (0200).

### *class* pyracf.IRRDBU(irrdbu00=None, pickles=None, auto_pickles=False, prefix='')

Bases: [`RACF`](#pyracf.RACF)
