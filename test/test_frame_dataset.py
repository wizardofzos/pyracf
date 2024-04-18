# check dataset and acl

import pytest 
import pandas as pd

def test_frame_dataset(testparms):
  r = testparms['object']
  t1 = r.dataset('SYS1.**')
  t2 = r.datasets.loc[['SYS1.**']]
  assert t1.to_records()==t2.to_records(), 'dataset function and datasets.loc must be the same'
  assert t1.shape[0]==1, 'dataset must select 1 profile only'

def test_frame_datasets(testparms):
  r = testparms['object']
  t1 = r.datasets.gfilter('SYS1.**')
  assert t1.shape[0]>1, 'datasets.gfilter must select several profiles'

def test_frame_datasets_acl(testparms):
  r = testparms['object']
  t1 = r.datasets.gfilter('SYS1.**')
  t2 = r.datasets.gfilter('SYS1.**').acl()
  assert t1.shape[0]<t2.shape[0], 'datasets.acl must generate more lines than datasets'
  assert t2.shape[1]>=5, 'datasets.acl must have 5 columns or 7'

def test_frame_datasets_acl_resolve(testparms):
  r = testparms['object']
  t1 = r.datasets.gfilter('SYS1.**').acl(explode=True)
  t2 = r.datasets.gfilter('SYS1.**').acl(resolve=True)
  assert t1.shape[0]>t2.shape[0], 'datasets.acl(explode) must generate more lines than datasets.acl(resolve)'
  assert t1.shape[1]>=5, 'datasets.acl(explode) must have 5 columns or 7'
  assert t2.shape[1]>=5, 'datasets.acl(resolve) must have 5 columns or 7'

def test_frame_datasets_acl_admin(testparms):
  r = testparms['object']
  t1 = r.datasets.gfilter('SYS1.**').acl(admin=True)
  assert t1.shape[1]>=8, 'datasets.acl(explode) must have 8 columns or 10'


