# Verify RACF profiles using Rules

Administrative changes to RACF profiles may leave some fields in an undesirable state, be it through mistake or malice.
Though finding such undesirable values takes time, they should be corrected quickly to minimize impact but also to address the cause of the mishap.
Fixing long after the fact makes it difficult to find the cause since human memory is typically inaccurate.

Using ProfileFrames and python code it is possible to write algorithms that spot specific errors and inconsistencies, but such code can be complex and lengthy.
Verifying for a multitude of possible inconsistencies results in more code than an auditor (or even a security analyst) can inspect.

The approach in the `RuleVerifier` package is to split the high level policy specification from the code that interacts with ProfileFrames.
The policy specification states the desirable values of profile fields, the underlying *verifier* checks the individual Frames with reusable code.

## Running a verification

Several common requirements for RACF administration have been combined in a module `profile_field_rules.py`, that can be easily run as a *default* policy.
This produces a DataFrame with orphan permits, notify and owner values, permits in profiles that should not have any permits issued, incorrect users and groups used in STARTED profiles, etc.

You first create a RuleVerifier instance from a RACF object `r` like so:

```default
from pyracf.rule_verify import RuleVerifier
v = RuleVerifier(r)
```

This can be shortened by relying on the `rules` property in the RACF object:

```default
v = r.rules
```

The RuleVerifier instance needs a policy to run against the contents of the RACF objects.  You can use the `load` method to add rules, domains, or pre-built modules with those.
In the absence of parameters, `profile_field_rules.py` is loaded:

```default
v.load()
```

This returns a modified RuleVerifier instance, but does not change the instance itself.  You must either assign the returned value to save the modified instance or, more likely, execute one of the methods available:

```default
>>> v.load().syntax_check()
      field   value   comment
0     rules   OK      No problem found in rules

>>> v.load().verify()
      CLASS       PROFILE                     FIELD_NAME      EXPECT     ACTUAL      RULE                                             ID

  0   dataset     DSN710.ARCHLOG2.A0000008    DSACC_AUTH_ID   ACLID      DSN1MSTR    orphan permits

  1   dataset     DSN710.ARCHLOG2.B0000008    DSACC_AUTH_ID   ACLID      DSN1MSTR    orphan permits

181   JESSPOOL    &JESNODE.LEN*.*.*.*.*       id              USERQUAL   LEN*        2nd qualifier in JESSPOOL should be a user ID

182   SURROGAT    BPX.SRV.**                  user            USERQUAL   **          surrogate profiles must refer to user ID or RA...

355   STARTED     DCEKERN.**                  GRST_GROUP_ID   GROUP      DCEGRP      orphans in STARTED profiles

356   STARTED     DCEPWDD.**                  GRST_GROUP_ID   GROUP      DCEGRP      orphans in STARTED profiles

357   STARTED     DCESECD.**                  GRST_GROUP_ID   GROUP      DCEGRP      orphans in STARTED profiles
```

`syntax_check` merely looks at the policy and checks that no illegal components are used.  `verify` checks a number of ProfileFrames and lists (possible) problems in a DataFrame.  Columns in the Frame are:

CLASS
: The class of the general resource profile, or *user*, *group* or *dataset*.

PROFILE
: The key of the profile where the issue was spotted.

FIELD_NAME
: The name documented in the [IBM Documentation](https://www.ibm.com/docs/en/zos/3.1.0?topic=records-irrdbu00-record-types).
  This also identifies the prefix of the ProfileFrame, or the table name (DSACC, GRST, etc).

EXPECT
: The `domain` name for the field, or the literal values, as stated in the `rule`.  ACLID is a domain that includes all user IDs, group names and \*.

ACTUAL
: The actual value found in the field, this would be the value that conflicts with the `rule`.

RULE
: Descriptive name of the `rule`.

ID
: Optional numeric or character identifier of the `rule`.

The DataFrame can be further manipulated using `find` and `skip` methods using the (uppercase) column headers, or (lowercase) aliases of the columns.
For example, select all issues with JESPOOL and SURROGAT profiles, and save these in a comma separated file:

```default
v.load().verify().find(resclass=['JESSPOOL','SURROGAT']).to_csv('/tmp/issues_for_sysprog.csv')
```

## Rules example

Rules are processed as a python dictionary, using the dictionary keys as directive and parameter names, and the dictionary values as criteria and parameters.
To improve readability, you can use yaml to write and store rules, but keep in mind that yaml aggressively interprets parameter values as bool, int or float values, unless you add quotes around the value.
See [The yaml document from hell](https://ruudvanasseldonk.com/2023/01/11/the-yaml-document-from-hell).

If the `load` method finds a `dict` type parameter, it uses the dict as a rules or domains value.  If it receives a `str` type, it converts this from yaml to dict before using it.
We will use yaml to illustrate the structure of rules.

Suppose we want to test the permits on data set and general resource profiles, to verify that the IDs (still) exist.
We would process the dataset access (DSACC) and general resource access (GRACC) tables, test the value of DSACC_AUTH_ID and GRACC_AUTH_ID to see if these are (valid) Access Control List IDs (ACLID).
Instead of writing the whole field name, we leave off the prefix because the remainder is the same in those two tables.  The following would accomplish the *orphan permit* test:

```default
testPermits = '''
permits must refer to existing users or groups:
  - [DSACC,GRACC]
  - test:
      field: AUTH_ID
      fit: ACLID
'''
v.load(rules=testPermits).verify()
```

The first line in the *multi-line string* contains the rule description, written as the key of the dict entry (that’s what the `:` at the end of the line is for).

The value of the dict entry is a list (array).  The first element of the list is either a str with the table name (field prefix), or a list of str when multiple tables should be processed.
The other elements of the list describe test criteria: tests and selections that limit where the test should be performed.

In this example, the test applies to the *prefix* \_AUTH_ID field and checks that the value *fits* the ACLID `domain`. See [Domains example](#domains) below for other domains.

We can also apply two rules in one verify:

```default
testAccess = '''
dataset permits must refer to existing users or groups:
  - DSACC
  - test:
    field: AUTH_ID
    fit: ACLID

no update access to data sets through UACC:
  - DSBD
  - test:
      field: UACC
      value: [NONE,READ]
'''
v.load(rules=testAccess).verify()
```

Each rule starts with the (key) rule description, followed by the table name. The rules apply to different tables. The second rule verifies that the UACC of dataset profiles does not exceed READ.

So far, the test commands were not preceded by selections, so they apply to all entries in the specified table. We expand the first rule with a similar restriction to access for `ID(*)`.
This is accomplished by adding a new entry to the end of the list, this time with a find and a test directive:

```default
testAccess = '''
access to data sets through permits:
  - DSACC
  - test:
      field: AUTH_ID
      fit: ACLID
  - find:
      field: AUTH_ID
      value: '*'
    test:
      field: ACCESS
      value: [NONE,READ]

no update access to data sets through UACC:
  - DSBD
  - test:
      field: UACC
      value: [NONE,READ]
'''
v.load(rules=testAccess).verify()
```

The first rule now contains two test criteria.  The first applies to all DSACC entries, the second only to entries where AUTH_ID contains an asterisk.
For these `ID(*)` entries, the same test is applied as to the UACC value.

Lets add a test for the WARNING flag in the profile (Basic Data):

```default
testAccess = '''
access to data sets through permits:
  - DSACC
  - test:
      field: AUTH_ID
      fit: ACLID
  - find:
      field: AUTH_ID
      value: '*'
    test:
      field: ACCESS
      value: [NONE,READ]
no update access to data sets through UACC:
  - DSBD
  - test:
      - field: UACC
        value: [NONE,READ]
      - field: WARNING
        value: 'NO'
        rule: Warning mode must be disabled
'''
v.load(rules=testAccess).verify()
```

The test directive now contains a list of field-value criteria, so two fields are checked for each entry.
This also demonstrate that rule descriptions can be specified at the rule **or** at the test level.

Finally, an optional directive `id` can be specified at the same level as the test directive, or in the field criteria:

```default
testAccess = '''
access to data sets through permits:
  - DSACC
  - id: 1.1
    test:
      field: AUTH_ID
      fit: ACLID
  - id: 1.2
    find:
      field: AUTH_ID
      value: '*'
    test:
      field: ACCESS
      value: [NONE,READ]
no update access to data sets through UACC:
  - DSBD
  - id: 1.3
    test:
      - field: UACC
        value: [NONE,READ]
      - field: WARNING
        value: 'NO'
        id: 1.4
        rule: Warning mode must be disabled
'''
v.load(rules=testAccess).verify()
```

And you can filter the verify results using the `find` method, like so:

```default
v.load(rules=testAccess).verify().find(ID=1.4)
```

## Rules syntax

Rules are a dictionary (dict), the description of the rule is the key of a dict entry.  Normally, yaml ignores entries with a duplicate description, however, RulesVerifier issues a warning and creates a unique key.

The entry value is a list, the first element of the list identifies the table or tables this rule works on.  The table name is identified by the *Prefix* value shown in [Record types and properties](DataFrames.md#dataframes).
The table name can also be a dynamic table created with the `save` directive.

Subsequent list elements are test criteria.

Test criteria are a dict.  The keys of the criteria dict are referred to as directives.  An output directive is required, that is `save` or `test`, all others are optional.

### class, -class

Applies only to tables starting with GR, select or exclude entries of the specified general resource class.  Patterns are not supported.  Provides fast selection.

### profile, -profile

Select or exclude profiles (keys) that match the generic pattern given.  Provides fast selection.

### match, -match

Select or exclude profiles that provide the best match with the given data set name or general resource name.  For example:

```default
match: SYS1.PROCLIB
```

or a list:

```default
match:
  - SYS1.PROCLIB
  - SYS1.USER.PROCLIB
```

or:

```default
class: FACILITY
match: BPX.SUPERUSER
```

If the match value contains parentheses, the value extracted from the corresponding qualifier in the profile key will be stored in a new field named by the string within the parentheses, and can be used in the `find`, `skip` and `test` directives.  For example:

```default
- class: SURROGAT
  match: (id).SUBMIT
  test:
    field: id
    fit: USERQUAL
```

### find, skip

Select or exclude profiles using field names.  These directives accept one field criterium, or several in a list.  If more than one criterium is given, the criteria must all match, in other words, they act as AND conditions.
For example, this excludes all permits to SYS1 with ALTER access:

```default
skip:
  - field: AUTH_ID
    value: SYS1
  - field: ACCESS
    value: ALTER
```

If an OR condition is needed, you can specify additional `find` and `skip` directives with arbitrary characters after the 4 fixed letters, for example:

```default
find_s:
  field: SPECIAL
  value: 'YES'
find_o:
  field: OPER
  value: 'YES'
find_a:
  field: AUDITOR
  value: 'YES'
find_roa:
  field: ROAUDIT
  value: 'YES'
```

Parameters in the `find` and `skip` criteria:

field
: Field name, with or without prefix.  You can specify field names from the current table, joined table, or dynamic fields from the `match` directive.

value
: The value the field should have, or a list of values.  Be careful to add quotes around YES, NO, ON, OFF, FAIL, FALSE and TRUE.  Patterns are not supported.
  If `fit` and `value` are both specified, the field value matches if it is either in the domain, or it matches the value.

fit
: The name of a domain entry, the current field value must be a member of the domain for `find`, or not for `skip`.

eq
: Field name, with or without prefix, to compare with the value of `field`, for example, to select groups where owner and superior group are equal.

ne
: Field name, with or without prefix, to compare with the value of `field`, for example, to select DSACC records where the user ID on the ACL is not the same as the hight level qualifier.

### join

Retrieve additional data fields from another table.  The target table will be accessed through its index.  The table name is a *Prefix*, or a dynamic table name defined with the `save` directive.
If the `on` parameter is omitted, a match with the current index value will be found, for example to add segment data to a base definitions table:

```default
specials should not have root:
  - USBD
  - id: 101
    join: USOMVS
    find:
      field: SPECIAL
      value: 'YES'
    test:
      field: UID
      value: '0000000000'
      action: 'FAIL'

specials should not also have group special:
  - USBD
  - id: 102
    join:
      table: USCON
      how: inner
    find:
      field: SPECIAL
      value: 'YES'
    test:
      field: GRP_SPECIAL
      value: 'NO'

specials must be connected to RACFADM:
  - USBD
  - id: 103
    join:
      table: USCON
      how: left
    find:
      - field: SPECIAL
        value: 'YES'
      - field: GRP_ID
        value: RACFADM
    test:
      - field: GRP_SPECIAL
        value: 'NO'
      - field: USCON_REVOKE
        value: 'NO'
```

Parameters of the `join` directive:

> Name of the target table

or a dict with keys:

table
: Name of the target table.

on
: Field name in the current table to use for lookup in the target table.  When omitted, the index field of the current table is used.

how
: Join method, ‘left’, ‘right’, ‘outer’, ‘inner’, or ‘cross’.
  See [pandas documentation](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.join.html) for the use of join methods.

`join` can also reference a saved table, for example, to match user IDs in *permits* with a dynamic list of user IDs, see [below](#save-join).

### save

Save the result of the current selection as a local (within this verify() run) table name, so a subsequent rule can refer to the saved results by name.
All results of the directives in the current rule are saved, except the `test` directive and the matched (dynamic) field values.
Saving rule results may reduce processing time, especially when the results were derived from a `match` operation.
`save` is denied if the rule reads from multiple tables.

An example where the APF data set names were used to select profiles, and the 3rd rule uses these profiles to verify corresponding records with access list info.
Note how field names in the 3rd rule include the table prefix to prevent name clashes:

```default
APF library updates must be controlled:
- DSBD
- match:
       - SYS1.LINKLIB
       - TEST.APFLOAD
       - TEST.USERAPF
  save: APF_profiles
  test:
    - field: UACC
      value:
        - NONE
        - READ
    - field: IDSTAR_ACCESS
      value:
        - NONE
        - READ
    - field: WARNING
      value: 'NO'

APF library updates must be logged:
- APF_profiles
- test:
    - field: AUDIT_LEVEL
      value: [ALL,SUCCESS]
    - field: AUDIT_OKQUAL
      value: [READ,UPDATE]

APF library update must be limited to sysprogs:
- APF_profiles
- join: DSACC
  find:
    - field: DSACC_ACCESS
      value: [UPDATE,CONTROL,ALTER]
  test:
    field: DSACC_AUTH_ID
    value:
      - SYS1
      - SYSPROG
```

<a id="save-join"></a>

The saved table can also be used in a `join` directive, for example, to select entries from a list built in a previous rule:

```default
Users with special:
- USBD
- find:
    field: SPECIAL
    value: 'YES'
  -profile: IBMUSER
  save: Special_users

Specials should have no DATASET permit ALTER:
- DSACC
- join:
    table: Special_users
    on: AUTH_ID
    how: inner
  find:
    field: ACCESS
    value: ALTER
  test:
    field: AUTH_ID
    value: ''
```

### test

Perform test on field values in the selected profiles.
The directive requires one field criterium specifying the expected value(s), or several criteria in a list.  If more than one criterium is given, the criteria must all match, in other words, they act as AND conditions.

Parameters in the `test` directive:

field
: Field name, with or without prefix.  You can specify field names from the current table, joined table, or dynamic fields from the `match` directive.

value
: The value the field should have, or a list of values.  Be careful to add quotes around YES, NO, ON, OFF, FAIL, FALSE and TRUE.  Patterns are not supported.
  If `fit` and `value` are both specified, the field value matches if it is either in the domain, or it matches the value.

fit
: The name of a domain entry, the current field value must be a member of the domain for `find`, or not for `skip`.

eq
: Field name, with or without prefix, to compare with the value of `field`, for example, to check if owner and superior group are equal.

ne
: Field name, with or without prefix, to compare with the value of `field`, for example, to check if the user ID on the ACL is not the same as the hight level qualifier.

action
: Reverse the result of the field test by specifying action: ‘FAILURE’, ‘FAIL’, ‘F’, or ‘V’.

### id

The rule can be identified with a str, int or float value.  This can be specified as a directive, or as a parameter in the `test` directive.

### rule

An overriding rule description can be specified as a directive, or as a parameter in the `test` directive.

<a id="domains"></a>

## Domains example

Domains are processed as a python dictionary, using the dictionary keys as the domain name and the dictionary values as members of the domain.  The value must be a list-like object.
To improve readability, you can use yaml to write and store domains.

If the `load` method finds a `dict` type parameter, it uses the dict as a rules or domains value.  If it receives a `str` type, it converts this from yaml to dict before using it.

The default policy module `profile_field_rules.py` introduces some useful domains:

USER
: List of all RACF defined user IDs.

GROUP
: List of all RACF defined group names.

ID
: The `union` of USER and GROUP, giving IDs that could be used as, for example, OWNER of a profile.

SPECIALID
: Special values that can be used in (some) PERMITs and profile qualifiers: `*`, `&RACUID`, and `&RACGRP`.

ACLID
: The `union` of ID and SPECIALID, providing a domain to use for verifying PERMITs.

RACFVARS
: The RACFVARS profile keys, e.g., `&RACLNDE`.

USERQUAL
: The `union` of USER and RACFVARS, used to check profile qualifiers that should contain a (configuarable) user ID.

CATEGORY, SECLEVEL, SECLABEL
: List of categories, security levels and security labels defined in their relevant general resource profiles.

DELETE
: An empty domain, to ascertain a field is empty.

These domain names may be used with the `fit` parameter in `find`, `skip` and `test` directives, like so:

```default
testNotify = '''
NONOTIFY should be used on all profiles:
  - [DSBD,GRBD]
  - test:
      field: NOTIFY_ID
      fit: DELETE
'''
v.load(rules=testNotify).verify()
```

or:

```default
testNotify = '''
NOTIFY only works for user IDs that have not been deleted:
  - [DSBD,GRBD]
  - test:
      field: NOTIFY_ID
      fit: USER
'''
v.load(rules=testNotify).verify()
```

In addition to the pre-defined domains, you can add your own using list-like objects as values:

```default
v.add_domains('''
CICS_REGIONS:
    - CICPRODA
    - CICPRODB
    - CICSTEST
''')

v.add_domains({'PROD_GROUPS': ['PRODA','PRODB','PRODCICS'],
               'TEST_GROUPS': ['TEST1','TEST2']})

v.add_domains({'SYS1': r.connect('SYS1').index})

v.add_domains({'omvs_root_group': r.connect(user='OMVSKERN').index})
```

The third example shows how the `connect` attribute can be used to populate a domain with user IDs, the last example retrieves group names from a user ID.

Note: the parameter for `add_domains` is a dict and replaces identically named entries in the domain map with no warning.

You can use the `get_domains` method to extract one or all domain entries from the verify instance:

```default
v.get_domains()  # get a dict of all domains
v.get_domains('SECLABEL')  # get 1 domain in a list
```

## Verify access controls on APF libraries

If you have a list of critical data set names, for example, APF libraries, you can find the corresponding profiles as follows, and create a domain of these critical profiles:

```default
apfLibraries = ['SYS1.LINKLIB', 'TEST.APFLOAD', 'TEST.USERAPF']
apfProfiles = r.datasets.match(apfLibraries)
v.add_domains({'APF profiles': apfProfiles.index})
```

You can do the same with the built-in yaml support:

```default
v.add_domains('''
APF libraries:
   - SYS1.LINKLIB
   - TEST.APFLOAD
   - TEST.USERAPF
''')
v.add_domains({'APF profiles': r.datasets.match(v.get_domains('APF libraries')).index})
```

Next, you can use this domain to select dataset profiles and access list entries that *fit* the profiles in this domain, and apply tests:

```default
v.load(rules='''
APF library update must be controlled and logged:
  - [DSBD]
  - find:
      - field: NAME
        fit: APF profiles
    test:
      - field: UACC
        value:
          - NONE
          - READ
      - field: WARNING
        value: 'NO'
      - field: AUDIT_LEVEL
        value: [ALL,SUCCESS]
      - field: AUDIT_OKQUAL
        value: [READ,UPDATE]

APF library update must be limited to sysprogs:
  - [DSACC]
  - find:
      - field: NAME
        fit: APF profiles
      - field: ACCESS
        value: [UPDATE,CONTROL,ALTER]
    test:
      field: AUTH_ID
      value:
        - SYS1
        - SYSPROG
  ''')

v.verify()
```

## Identify orphans in access control lists

The default policy module `profile_field_rules.py` contains a rule to find orphans in dataset and general resource profiles.  This verification can also be called stand-alone and with a reduced output frame, with the following code:

```default
from pyracf.rule_verify import RuleVerifier

orphans = RuleVerifier(r)\
  .load(rules = {'orphan permits':
                (['DSACC','DSCACC','GRACC','GRCACC'],
                 {'test': {'field':'AUTH_ID', 'fit':'ACLID'}}) } )\
  .verify()\
  .drop(['FIELD_NAME','EXPECT','RULE','ID'],axis=1)\
  .rename({'ACTUAL':'AUTH_ID'},axis=1)\
  .set_index('AUTH_ID')
```

This produces a frame `orphans` by orphan ID, with class and profile key, ready to generate `PERMIT DELETE` commands.

## Methods and classes for RuleVerifier

### *class* pyracf.rule_verify.RuleFrame(data=None, index: Axes | None = None, columns: Axes | None = None, dtype: Dtype | None = None, copy: bool | None = None)

Bases: `DataFrame`, [`FrameFilter`](source/pyracf.md#pyracf.frame_filter.FrameFilter)

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
  [RuleVerifier](source/pyracf.md#pyracf.rule_verify.RuleVerifier)

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
  [RuleVerifier](source/pyracf.md#pyracf.rule_verify.RuleVerifier)

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
