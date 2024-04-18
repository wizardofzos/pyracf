# verify the result of parsing, not the actual content of dfs

import pytest 
import pandas as pd

externalFrames = ['ALIAS',
 'CDTINFO',
 'CERT',
 'CERTname',
 'CERTreferences',
 'CFDEF',
 'DLFDATA',
 'DLFDATAjobnames',
 'DistributedIdFilter',
 'DistributedIdMapping',
 'EIM',
 'ICSF',
 'ICSFsymexportCertificateIdentifier',
 'ICSFsymexportKeylabel',
 'ICTX',
 'IDTFPARMS',
 'JES',
 'KERB',
 'KEYRING',
 'MFA',
 'MFPOLICY',
 'MFPOLICYfactors',
 'PROXY',
 'SESSION',
 'SESSIONentities',
 'SIGVER',
 'SSIGNON',
 'STDATA',
 'SVFMR',
 'TME',
 'TMEchild',
 'TMEgroup',
 'TMEresource',
 'TMErole',
 'auditors',
 'connectData',
 'connects',
 'datasetAccess',
 'datasetCSDATA',
 'datasetCategories',
 'datasetConditionalAccess',
 'datasetDFP',
 'datasetTME',
 'datasetUSRDATA',
 'datasets',
 'generalAccess',
 'generalCSDATA',
 'generalCategories',
 'generalConditionalAccess',
 'generalMembers',
 'generalTAPEvolume',
 'generalTAPEvolumes',
 'generalUSRDATA',
 'generals',
 'genericAccess',
 'genericConditionalAccess',
 'genericMembers',
 'generics',
 'groupCSDATA',
 'groupConnect',
 'groupDFP',
 'groupOMVS',
 'groupTME',
 'groupUSRDATA',
 'groups',
 'groupsWithoutUsers',
 'installdata',
 'operations',
 'revoked',
 'specials',
 'subgroups',
 'uacc_alter_datasets',
 'uacc_control_datasets',
 'uacc_read_datasets',
 'uacc_update_datasets',
 'userAssociationMapping',
 'userCERTname',
 'userCICS',
 'userCICSoperatorClasses',
 'userCICSrslKeys',
 'userCICStslKeys',
 'userCSDATA',
 'userCategories',
 'userClasses',
 'userDFP',
 'userDistributedIdMapping',
 'userDistributedMapping',
 'userLANGUAGE',
 'userMFAfactor',
 'userMFAfactorTags',
 'userMFApolicies',
 'userNETVIEW',
 'userNETVIEWdomains',
 'userNETVIEWopclass',
 'userOMVS',
 'userOPERPARM',
 'userOPERPARMscope',
 'userRRSFDATA',
 'userTSO',
 'userUSRDATA',
 'userWORKATTR',
 'users',
]

internalFrames = ['_connectData',
 '_connects',
 '_datasetAccess',
 '_datasetCSDATA',
 '_datasetCategories',
 '_datasetConditionalAccess',
 '_datasetDFP',
 '_datasetMember',
 '_datasetTME',
 '_datasetUSRDATA',
 '_datasetVolumes',
 '_datasets',
 '_generalALIAS',
 '_generalAccess',
 '_generalCDTINFO',
 '_generalCERT',
 '_generalCERTname',
 '_generalCERTreferences',
 '_generalCFDEF',
 '_generalCSDATA',
 '_generalCategories',
 '_generalConditionalAccess',
 '_generalDLFDATA',
 '_generalDLFDATAjobnames',
 '_generalDistributedIdFilter',
 '_generalDistributedIdMapping',
 '_generalEIM',
 '_generalICSF',
 '_generalICSFsymexportCertificateIdentifier',
 '_generalICSFsymexportKeylabel',
 '_generalICTX',
 '_generalIDTFPARMS',
 '_generalJES',
 '_generalKERB',
 '_generalKEYRING',
 '_generalMFA',
 '_generalMFPOLICY',
 '_generalMFPOLICYfactors',
 '_generalMembers',
 '_generalPROXY',
 '_generalSESSION',
 '_generalSESSIONentities',
 '_generalSIGVER',
 '_generalSSIGNON',
 '_generalSTDATA',
 '_generalSVFMR',
 '_generalTAPEvolume',
 '_generalTAPEvolumes',
 '_generalTME',
 '_generalTMEchild',
 '_generalTMEgroup',
 '_generalTMEresource',
 '_generalTMErole',
 '_generalUSRDATA',
 '_generals',
 '_groupCSDATA',
 '_groupConnect',
 '_groupDFP',
 '_groupOMVS',
 '_groupOVM',
 '_groupTME',
 '_groupUSRDATA',
 '_groups',
 '_grouptreeLines',
 '_ownertreeLines',
 '_subgroups',
 '_userAssociationMapping',
 '_userCERTname',
 '_userCICS',
 '_userCICSoperatorClasses',
 '_userCICSrslKeys',
 '_userCICStslKeys',
 '_userCSDATA',
 '_userCategories',
 '_userClasses',
 '_userDCE',
 '_userDFP',
 '_userDistributedIdMapping',
 '_userEIM',
 '_userKERB',
 '_userLANGUAGE',
 '_userLNOTES',
 '_userMFAfactor',
 '_userMFAfactorTags',
 '_userMFApolicies',
 '_userNDS',
 '_userNETVIEW',
 '_userNETVIEWdomains',
 '_userNETVIEWopclass',
 '_userOMVS',
 '_userOPERPARM',
 '_userOPERPARMscope',
 '_userOVM',
 '_userPROXY',
 '_userRRSFdata',
 '_userTSO',
 '_userUSRDATA',
 '_userWORKATTR',
 '_users',
]

deprecatedFrames = [
 'genericAccess',
 'genericConditionalAccess',
 'genericMembers',
 'generics',
 'installdata',
 'userDistributedMapping',
]


methods = [
 'parsed',
 'connect',
 'dataset',
 'datasetConditionalPermit',
 'datasetPermit',
 'general',
 'generalConditionalPermit',
 'generalPermit',
 'getdatasetrisk',
 'group',
 'grouptree',
 'orphans',
 'ownertree',
 'parse',
 'parse_fancycli',
 'save_pickle',
 'save_pickles',
 'status',
 'user',
 'parse_t',
 'xls',
]

# attributes we should have
otherAttributes = [
 'STATE_BAD',
 'STATE_CORRELATING',
 'STATE_INIT',
 'STATE_PARSING',
 'STATE_READY',
 '_correlate',
 '_grouptree',
 '_ownertree',
 '_recordname_df',
 '_recordname_type',
 '_recordtype_info',
 '_records',
 '_starttime',
 '_stoptime',
 '_state',
]

# attributes that don't get created for pickles (for example), so if we find them that's fine, if we don't it's fine too
optionalAttributes = [
 'accessAllows',
 'accessKeywords',
 'generic2regex',
 'rankedAccess',
 'THREAD_COUNT',
 '_irrdbu00',
 '_parsed',
 '_unloadlines',
]

frameMethods = [
 'acl',
 'gfilter',
 'rfilter',
 'giveMeProfiles',
]


def test_frames_in_attributes(testparms):
  r = testparms['object']
  for f in externalFrames:
      if f in deprecatedFrames:
          with pytest.warns(UserWarning) as record: # should be .deprecated_call():
              assert hasattr(r,f), f'deprecated frame {f} must be an attribute'
              assert getattr(r,f).ndim==2, f'deprecated frame {f} must be a frame'
          assert record[0].message.args[0].find('deprecated')>-1, f'deprecated frame {f} without warning'
      else:
          assert hasattr(r,f), f'documented frame {f} must be an attribute'
          assert getattr(r,f).ndim==2, f'documented frame {f} must be a frame'
  for f in internalFrames:
      assert hasattr(r,f), f'internal (_) frame {f} must be an attribute'
      assert getattr(r,f).ndim==2, f'internal (_) frame {f} must be a frame'

def test_expected_attributes(testparms):
  r = testparms['object']  
  for f in externalFrames:
      assert f in dir(r),  f'expected external attribute {f} not in RACF object'
  for f in internalFrames:
      assert f in dir(r),  f'expected internal attribute {f} not in RACF object'
  for f in methods:
      assert f in dir(r),  f'expected method {f} not in RACF object'
  for f in otherAttributes:
      assert f in dir(r),  f'expected other attribute {f} not in RACF object'

def test_unexpected_attributes(testparms):
  r = testparms['object']  
  for f in dir(r):
      if f[0:2]=='__': pass
      elif f in internalFrames: pass
      elif f in externalFrames: pass
      elif f in methods: pass
      elif f in frameMethods: pass
      elif f in otherAttributes: pass
      elif f in optionalAttributes: pass
      else:
          assert not hasattr(r,f), f'unexpected attribute {f}'



