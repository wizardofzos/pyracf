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
    domains.update({'RACFVARS':self.generals.loc['RACFVARS'].index})
    domains.update({'CATEGORY':self.generalMembers['GRMEM_MEMBER'].gfilter('SECDATA','CATEGORY').values})
    domains.update({'SECLEVEL':self.generalMembers['GRMEM_MEMBER'].gfilter('SECDATA','SECLEVEL').values})
    domains.update({'SECLABEL':self.generals.loc['SECLABEL'].index})
    domains.update({'USERQUAL':self.users.index.union(domains['RACFVARS'])})
    return domains
    
# list of tuples, each with (list of) table ids and conditions.
# each condition allows fields, class, notclass, profile, notprofile and match.
# class, notclass, profile and notprofile are (cuurently) generic patterns.
# match extracts fields from the profile key, the name should be used in subsequent fields rules.
# fields test if the value occurs in one of the domains, or a (list of) literal(s).

def _rules(self):
    rules = [
        # orphan permits
        (['DSACC','DSCACC','DSMEM','GRACC','GRCACC'],
         {'fields':[
            {'name':'AUTH_ID', 'expect':'ACLID'},
            ]
         }
        ),
        # DFP resower must be user of group
        (['DSDFP'],
         {'fields':
            {'name':'RESOWNER_ID', 'expect':'ID'},
         }
        ),
        # notify on dataset and resource profiles must be user, owner must be user or group
        (['DSBD','GRBD'],
         {'fields':[
            {'name':'NOTIFY_ID', 'expect':'USER'},
            {'name':'OWNER_ID', 'expect':'ID'}
            ]
         }
        ),
        # general resource profile key qualifiers
        ('GRBD',[
         # surrogate profiles must refer to user ID or RACFVARS
         {'class':'SURROGAT',
          'match':'(id).SUBMIT',
          'fields':
              {'name':'id', 'expect':'USERQUAL'}        
         },
         {'class':'SURROGAT',
          'match':'BPX.(type).(user)',
          'fields':
              {'name':'user', 'expect':'USERQUAL'}        
         }]
        ),
        # classes that do not support PERMIT
        (['GRACC','GRCACC'],
         {'class':['CDT','CFIELD','RACFVARS','SECDATA','STARTED','UNIXMAP'],
          'fields':[
            {'name':'AUTH_ID', 'expect':'DELETE'},
            ]
         }
        ),
        # orphan users in filters and maps
        (['GRFLTR','GRDMAP'],
         {'fields':
            {'name':'USER', 'expect':'USER'}
         }
        ),
        # orphans in STARTED profiles
        ('GRST',
         {'fields':[
            {'name':'USER_ID', 'expect':'USER', 'or':'=NODATA'},
            {'name':'GROUP_ID', 'expect':'GROUP', 'or':'=NODATA'}
            ]
         }
        ),
        # users should have valid default group and owner
        ('USBD',
         {'fields':[
            {'name':'DEFGRP_ID', 'expect':'GROUP'},
            {'name':'OWNER_ID', 'expect':'ID'}
            ]
         }
        ),
        # valid CATEGORY, SECLEVEL and SECLABEL
        (['DSCAT','GRCAT','GRMEM','USCAT'],
         {'notclass':['SECDATA','SECLABEL'],
          'fields':[
            {'name':'CATEGORY', 'expect':'CATEGORY'},
            ]
         }
        ),
        (['DSBD','GRBD','GRMEM','USBD'],
         {'notclass':['SECDATA','SECLABEL'],
          'fields':[
            {'name':'SECLEVEL', 'expect':'SECLEVEL', 'or':'000'},
            ]
         }
        ),
        (['DSBD','GRBD','USBD','USTSO'],
         {'fields':[
            {'name':'SECLABEL', 'expect':'SECLABEL'},
            ]
         }
        )
    ]
    return rules
