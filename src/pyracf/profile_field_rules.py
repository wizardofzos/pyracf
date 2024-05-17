'''rules for the pyracf.verify() service.
This module is imported from load() on a rules object.
load() expects a dict for domains, list for rules, or a yaml str representing these objects.

functions:
    domains: returns the sets of values that can be expected in profile fields and qualifiers.
    rules: specifies where these domain values should be expected.
'''

def domains(self,pd):
    '''generate a dict (or yaml str) with named lists of values

     each domain entry contains a list, array or Series that will be used in .loc[field.isin( )] to verify valid values in profile fields.
     keys of the dict are only referenced in the corresponding rules, feel free to change /extend.
     self and pd are passed down to access data frames from caller.
     '''

    _domains = {
        'SPECIAL':pd.Index(['*','&RACUID','&RACGRP'],name='_NAME'),
        'USER':self._RACFobject.users.index,
        'GROUP':self._RACFobject.groups.index,
        'DELETE':['']
    }
    _domains.update({'ID':self._RACFobject.users.index.union(self._RACFobject.groups.index)})
    _domains.update({'ACLID':_domains['SPECIAL'].union(_domains['ID'])})
    _domains.update({'RACFVARS':self._RACFobject.generals.find('RACFVARS').index.get_level_values(1)})
    _domains.update({'CATEGORY':self._RACFobject.generalMembers.find('SECDATA','CATEGORY')['GRMEM_MEMBER'].values})
    _domains.update({'SECLEVEL':self._RACFobject.generalMembers.find('SECDATA','SECLEVEL')['GRMEM_MEMBER'].values})
    _domains.update({'SECLABEL':self._RACFobject.generals.find('SECLABEL').index.get_level_values(1)})
    _domains.update({'USERQUAL':self._RACFobject.users.index.union(_domains['RACFVARS'])})
    return _domains


def rules(self, format='yaml'):
    '''generate a list of lists/tuples, each with (list of) table ids, and one or more conditions.

    each condition allows class, -class, profile, -profile, find, skip, match and test.

    class, -class, profile and -profile are (currently) generic patterns, and select or skip profile/segment/entries.

    find and skip can be used to limit the number of rows to process

    match extracts fields from the profile key, the capture name should be used in subsequent fields rules.
    match changes . to \\. and * to \\*, so for regex patterns you should use \\S and +? instead.

    test verifies that the value occurs in one of the domains, or a (list of) literal(s).

    id and rule document the test at the test level or at the field level within a test.
    '''

    if format=='yaml':
        ''' YAML definition, should generate a list of lists, each table section starts with - - '''

        return r'''

- - [DSACC, DSCACC, DSMEM, GRACC, GRCACC]
  - test:
      field: AUTH_ID
      fit: ACLID
    rule: orphan permits

- - DSDFP
  - test:
    - field: RESOWNER_ID
      fit: ID
    rule: DFP resower must be user or group

- - [DSBD, GRBD]
  - test:
    - field: NOTIFY_ID
      fit: USER
      rule: notify on dataset and resource profiles must be user
    - field: OWNER_ID
      fit: ID
      rule: owner must be user or group

# general resource profile key qualifiers
- - GRBD
  - class: DIGTRING
    match: (id).
    test:
      field: id
      fit: USER
    rule: DIGTRING should be associated with a user ID
  - class: JESSPOOL
    match: '\S+?.(id).\S+'
    test:
      field: id
      fit: USERQUAL
      value: ['*','+MASTER+']
    rule: 2nd qualifier in JESSPOOL should be a user ID
  - class: SURROGAT
    match: (id).SUBMIT
    test:
      field: id
      fit: USERQUAL
  - class: SURROGAT
    match: BPX.(type).(user)
    test:
      field: user
      fit: USERQUAL
    rule: surrogate profiles must refer to user ID or RACFVARS

- - [GRACC, GRCACC]
  - class: [CDT, CFIELD, NODES, RACFVARS, SECDATA, STARTED, UNIXMAP]
    test:
    - field: AUTH_ID
      fit: DELETE
    rule: class does not support PERMIT

- - [GRFLTR, GRDMAP]
  - test:
      field: USER
      fit: USER
    rule: orphan users in filters and maps

- - GRST
  - test:
    - field: USER_ID
      fit: USER
      value: =MEMBER
    - field: GROUP_ID
      fit: GROUP
      value: =MEMBER
    rule: orphans in STARTED profiles

- - USBD
  - test:
    - field: DEFGRP_ID
      fit: GROUP
    - field: OWNER_ID
      fit: ID
    rule: users should have valid default group and owner

- - [DSCAT, GRCAT, GRMEM, USCAT]
  - -class: [SECDATA, SECLABEL]
    test:
    - field: CATEGORY
      fit: CATEGORY
    rule: valid CATEGORY (except in SECDATA and SECLABEL profiles where the internal values are used)

- - [DSBD, GRBD, GRMEM, USBD]
  - -class: [SECDATA, SECLABEL]
    test:
    - field: SECLEVEL
      fit: SECLEVEL
      value: '000'
    rule: valid SECLEVEL (except in SECDATA and SECLABEL profiles where the internal values are used)

- - [DSBD, GRBD, USBD, USTSO]
  - test:
    - field: SECLABEL
      fit: SECLABEL
    rule: valid SECLABEL

    '''

    else:
        ''' list of tuples/lists, native format. tuples used to help identify the table sections '''

        return [
            # orphan permits
            (['DSACC','DSCACC','DSMEM','GRACC','GRCACC'],
             {'test':
                {'field':'AUTH_ID', 'fit':'ACLID'},
             }
            ),
            # DFP resower must be user or group
            (['DSDFP'],
             {'test':[
                {'field':'RESOWNER_ID', 'fit':'ID'},
                ]
             }
            ),
            # notify on dataset and resource profiles must be user, owner must be user or group
            (['DSBD','GRBD'],
             {'test':[
                {'field':'NOTIFY_ID', 'fit':'USER'},
                {'field':'OWNER_ID', 'fit':'ID'}
                ]
             }
            ),
            # general resource profile key qualifiers
            ('GRBD',
             # DIGTRING is associated with a user ID
             {'class':'DIGTRING',
              'match':'(id).',
              'test':
                  {'field':'id', 'fit':'USER'}
             },
             # 2nd qualifier in JESSPOOL should be a user ID
             {'class':'JESSPOOL',
              'match':r'\S+?.(id).\S+',
              'test':
                  {'field':'id', 'fit':'USERQUAL', 'value': ['*','+MASTER+']}
             },
             # surrogate profiles must refer to user ID or RACFVARS
             {'class':'SURROGAT',
              'match':'(id).SUBMIT',
              'test':
                  {'field':'id', 'fit':'USERQUAL'}
             },
             {'class':'SURROGAT',
              'match':'BPX.(type).(user)',
              'test':
                  {'field':'user', 'fit':'USERQUAL'}
             }
            ),
            # classes that do not support PERMIT
            (['GRACC','GRCACC'],
             {'class':['CDT','Ctest','NODES','RACFVARS','SECDATA','STARTED','UNIXMAP'],
              'test':[
                {'field':'AUTH_ID', 'fit':'DELETE'},
                ]
             }
            ),
            # orphan users in filters and maps
            (['GRFLTR','GRDMAP'],
             {'test':
                {'field':'USER', 'fit':'USER'}
             }
            ),
            # orphans in STARTED profiles
            ('GRST',
             {'test':[
                {'field':'USER_ID', 'fit':'USER', 'value':'=MEMBER'},
                {'field':'GROUP_ID', 'fit':'GROUP', 'value':'=MEMBER'}
                ]
             }
            ),
            # users should have valid default group and owner
            ('USBD',
             {'test':[
                {'field':'DEFGRP_ID', 'fit':'GROUP'},
                {'field':'OWNER_ID', 'fit':'ID'}
                ]
             }
            ),
            # valid CATEGORY, SECLEVEL and SECLABEL
            (['DSCAT','GRCAT','GRMEM','USCAT'],
             {'-class':['SECDATA','SECLABEL'],
              'test':[
                {'field':'CATEGORY', 'fit':'CATEGORY'},
                ]
             }
            ),
            (['DSBD','GRBD','GRMEM','USBD'],
             {'-class':['SECDATA','SECLABEL'],
              'test':[
                {'field':'SECLEVEL', 'fit':'SECLEVEL', 'value':'000'},
                ]
             }
            ),
            (['DSBD','GRBD','USBD','USTSO'],
             {'test':[
                {'field':'SECLABEL', 'fit':'SECLABEL'},
                ]
             }
            )
        ]

