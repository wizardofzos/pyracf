# check general and acl

import pytest 
import pandas as pd

def test_frame_general(testparms):
  r = testparms['object']
  t1 = r.general('FACILITY','BPX.SUPERUSER')
  t2 = r.generals.loc[[('FACILITY','BPX.SUPERUSER')]]
  t3 = r.general('FACILITY')
  t4 = r.general(None,'BPX.SUPERUSER')
  t5 = r.general(None,'BPX.NOTTHERE')
  assert t1.to_records()==t2.to_records(), 'general function and generals.loc must be the same'
  assert t1.shape[0]==1, 'general must select 1 profile only'
  assert t3.shape[0]>1, 'when only class is specified, general must select several profiles'
  assert t4.shape[0]>=1, 'when only profile is specified, general must select matching profiles'
  assert t5.shape[0]==0, 'missing profiles must generate an empty frame'

def test_frame_generals(testparms):
  r = testparms['object']
  t1 = r.generals.gfilter('FACI*','BPX.**')
  assert t1.shape[0]>1, 'generals.gfilter must select several profiles'

def test_frame_general_anyclass(testparms):
  r = testparms['object']
  t1 = r.generals.gfilter('FACILITY','I*.**')
  t2 = r.generals.gfilter(None,'I*.**')
  assert t1.shape[0]<t2.shape[0], 'generals.gfilter must select more profiles when the class is not specified'

def test_frame_generals_acl(testparms):
  r = testparms['object']
  t1 = r.generals.gfilter('UNIXPRIV')
  t2 = r.generals.gfilter('UNIXPRIV').acl()
  assert t1.shape[0]<t2.shape[0], 'generals.acl must generate more lines than generals'
  assert t2.shape[1]>=5, 'generals.acl must have 5 columns, 5 or more'

