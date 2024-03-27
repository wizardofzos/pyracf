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
    
# list of tuples, each with (list of) table ids, and one or more conditions.
# each condition allows class, -class, profile, -profile, match and field.
# class, -class, profile and -profile are (currently) generic patterns.
# match extracts fields from the profile key, the name should be used in subsequent fields rules.
# field test if the value occurs in one of the domains, or a (list of) literal(s).

def _rules(self):
    rules = [
        # orphan permits
        (['DSACC','DSCACC','DSMEM','GRACC','GRCACC'],
         {'field':[
            {'name':'AUTH_ID', 'expect':'ACLID'},
            ]
         }
        ),
        # DFP resower must be user of group
        (['DSDFP'],
         {'field':
            {'name':'RESOWNER_ID', 'expect':'ID'},
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
         {'class':['CDT','CFIELD','RACFVARS','SECDATA','STARTED','UNIXMAP'],
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
    return rules
