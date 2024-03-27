''' rules for the pyracf.verify() service.
This file is imported from __init__.py and used in verify()

domains provides the sets of values that can be expected in profile fields and qualifiers.
rules specifies where these domain values should be expected.
'''

# dict returns a list, array or Series that will be used in .loc[field.isin( )] to verify valid values in profile fields.
# keys of the dict are only those referenced in the corresp. rules.

def _domains(self,pd):
    domains = {
        'SPECIAL':pd.Index(['*','&RACUID','&RACGRP'],name='_NAME'),
        'USER':self.users.index,
        'GROUP':self.groups.index,
        'DELETE':['']
    }
    domains.update({'ID':self.users.index.union(self.groups.index)})
    domains.update({'ACLID':domains['SPECIAL'].union(domains['ID'])})
    domains.update({'RACFVARS':self.generals.gfilter('RACFVARS').index.get_level_values(1)})
    domains.update({'CATEGORY':self.generalMembers['GRMEM_MEMBER'].gfilter('SECDATA','CATEGORY').values})
    domains.update({'SECLEVEL':self.generalMembers['GRMEM_MEMBER'].gfilter('SECDATA','SECLEVEL').values})
    domains.update({'SECLABEL':self.generals.gfilter('SECLABEL').index.get_level_values(1)})
    domains.update({'USERQUAL':self.users.index.union(domains['RACFVARS'])})
    return domains


def _rules(self, format='yaml'):

    if format=='yaml':

        # YAML definition, should generate a list of lists, each table entry is identified by - -
        # the values with commas in the table ID line is a string for YAML, but interpreted as a list in the verify() function
        # list of lists, each with (list of) table ids, and one or more conditions.
        # each condition allows class, -class, profile, -profile, match and field.
        # class, -class, profile and -profile are (currently) generic patterns, and select or skip profile/segment/entries.
        # match extracts fields from the profile key, the name should be used in subsequent fields rules.
        # field test if the value occurs in one of the domains, or a (list of) literal(s).

        return '''

- - DSACC, DSCACC, DSMEM, GRACC, GRCACC
  - field:
      name: AUTH_ID
      expect: ACLID
      comment: orphan permits

- - DSDFP
  - field:
    - name: RESOWNER_ID
      expect: ID
      comment: DFP resower must be user or group

- - DSBD, GRBD
  - field:
    - name: NOTIFY_ID
      expect: USER
      comment: notify on dataset and resource profiles must be user
    - name: OWNER_ID
      expect: ID
      comment: owner must be user or group

# general resource profile key qualifiers
- - GRBD
  - class: DIGTRING
    match: (id).
    field:
      name: id
      expect: USER
      comment: DIGTRING is associated with a user ID
  - class: JESSPOOL
    match: '&RACLNDE.(id).'
    field:
      name: id
      expect: USERQUAL
      comment: JESSPOOL is associated with a user ID
  - class: SURROGAT
    match: (id).SUBMIT
    field:
      name: id
      expect: USERQUAL
      comment: surrogate profiles must refer to user ID or RACFVARS
  - class: SURROGAT
    match: BPX.(type).(user)
    field:
      name: user
      expect: USERQUAL
      comment: surrogate profiles must refer to user ID or RACFVARS

- - GRACC, GRCACC
  - class: CDT, CFIELD, NODES, RACFVARS, SECDATA, STARTED, UNIXMAP
    field:
    - name: AUTH_ID
      expect: DELETE
      comment: class does not support PERMIT

- - GRFLTR, GRDMAP
  - field:
      name: USER
      expect: USER
      comment: orphan users in filters and maps

- - GRST
  - field:
    - name: USER_ID
      expect: USER
      or: =NODATA
      comment: orphans in STARTED profiles
    - name: GROUP_ID
      expect: GROUP
      or: =NODATA
      comment: orphans in STARTED profiles

- - USBD
  - field:
    - name: DEFGRP_ID
      expect: GROUP
      comment: users should have valid default group and owner
    - name: OWNER_ID
      expect: ID
      comment: users should have valid default group and owner

- - DSCAT, GRCAT, GRMEM, USCAT
  - -class: SECDATA, SECLABEL
    field:
    - name: CATEGORY
      expect: CATEGORY
      comment: valid CATEGORY (except in SECDATA and SECLABEL profiles where the internal values are used)

- - DSBD, GRBD, GRMEM, USBD
  - -class: SECDATA, SECLABEL
    field:
    - name: SECLEVEL
      expect: SECLEVEL
      or: '000'
      comment: valid CATEGORY, SECLEVEL and SECLABEL (except in SECDATA and SECLABEL profiles where the internal values are used)

- - DSBD, GRBD, USBD, USTSO
  - field:
    - name: SECLABEL
      expect: SECLABEL
      comment: valid CATEGORY, SECLEVEL and SECLABEL

'''

    else:
        # list of tuples, each with (list of) table ids, and one or more conditions.
        # each condition allows class, -class, profile, -profile, match and field.
        # class, -class, profile and -profile are (currently) generic patterns, and select or skip profile/segment/entries.
        # match extracts fields from the profile key, the name should be used in subsequent fields rules.
        # field test if the value occurs in one of the domains, or a (list of) literal(s).

        return [
            # orphan permits
            (['DSACC','DSCACC','DSMEM','GRACC','GRCACC'],
             {'field':
                {'name':'AUTH_ID', 'expect':'ACLID'},
             }
            ),
            # DFP resower must be user or group
            (['DSDFP'],
             {'field':[
                {'name':'RESOWNER_ID', 'expect':'ID'},
                ]
             }
            ),
            # notify on dataset and resource profiles must be user, owner must be user or group
            (['DSBD','GRBD'],
             {'field':[
                {'name':'NOTIFY_ID', 'expect':'USER'},
                {'name':'OWNER_ID', 'expect':'ID'}
                ]
             }
            ),
            # general resource profile key qualifiers
            ('GRBD',
             # DIGTRING is associated with a user ID
             {'class':'DIGTRING',
              'match':'(id).',
              'field':
                  {'name':'id', 'expect':'USER'}
             },
             # JESSPOOL is associated with a user ID
             {'class':'JESSPOOL',
              'match':'&RACLNDE.(id).',
              'field':
                  {'name':'id', 'expect':'USERQUAL'}
             },
             # surrogate profiles must refer to user ID or RACFVARS
             {'class':'SURROGAT',
              'match':'(id).SUBMIT',
              'field':
                  {'name':'id', 'expect':'USERQUAL'}
             },
             {'class':'SURROGAT',
              'match':'BPX.(type).(user)',
              'field':
                  {'name':'user', 'expect':'USERQUAL'}
             }
            ),
            # classes that do not support PERMIT
            (['GRACC','GRCACC'],
             {'class':['CDT','CFIELD','NODES','RACFVARS','SECDATA','STARTED','UNIXMAP'],
              'field':[
                {'name':'AUTH_ID', 'expect':'DELETE'},
                ]
             }
            ),
            # orphan users in filters and maps
            (['GRFLTR','GRDMAP'],
             {'field':
                {'name':'USER', 'expect':'USER'}
             }
            ),
            # orphans in STARTED profiles
            ('GRST',
             {'field':[
                {'name':'USER_ID', 'expect':'USER', 'or':'=NODATA'},
                {'name':'GROUP_ID', 'expect':'GROUP', 'or':'=NODATA'}
                ]
             }
            ),
            # users should have valid default group and owner
            ('USBD',
             {'field':[
                {'name':'DEFGRP_ID', 'expect':'GROUP'},
                {'name':'OWNER_ID', 'expect':'ID'}
                ]
             }
            ),
            # valid CATEGORY, SECLEVEL and SECLABEL
            (['DSCAT','GRCAT','GRMEM','USCAT'],
             {'-class':['SECDATA','SECLABEL'],
              'field':[
                {'name':'CATEGORY', 'expect':'CATEGORY'},
                ]
             }
            ),
            (['DSBD','GRBD','GRMEM','USBD'],
             {'-class':['SECDATA','SECLABEL'],
              'field':[
                {'name':'SECLEVEL', 'expect':'SECLEVEL', 'or':'000'},
                ]
             }
            ),
            (['DSBD','GRBD','USBD','USTSO'],
             {'field':[
                {'name':'SECLABEL', 'expect':'SECLABEL'},
                ]
             }
            )
        ]

