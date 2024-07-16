<a id="specific-selection-methods"></a>

# Methods to select specific entries

In addition to the data table properties, data selection methods are
available to retrieve one profile, or profiles from one class, with an
easy syntax. The parameter(s) to these methods are used as a literal
search argument, and return entries that fully match the argument(s), that means, the selection criteria have to be match the profile exactly.

### *class* pyracf.profile_publishers.ProfileSelectionFrame

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
