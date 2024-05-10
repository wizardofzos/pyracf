# rule verify 

import pytest 

def test_rules_object(testparms):
  r = testparms['object']
  assert hasattr(r,'rules'), f'RACF object must have "rules"'
  
  for f in ['_domains', '_module', '_rules', '_RACFobject']:
      assert f in dir(r.rules), f'rule object must have a {f} attribute'      
  for f in ['add_domains', 'load', 'syntax_check', 'verify']:
      assert f in dir(r.rules), f'rule object must have a {f} method'     
      
def test_rules_domains(testparms):
  r = testparms['object']
  assert not r.rules._domains, 'initial domains list must be empty' 
  assert r.rules.load()._domains, 'domains must be loadable'

  t = r.rules.load()
  for f in ['SPECIAL', 'USER', 'GROUP', 'DELETE', 'ID', 'ACLID', 'RACFVARS', 'CATEGORY', 'SECLEVEL', 'SECLABEL', 'USERQUAL']:
      assert f in t._domains, f'domain list must have {f} entry'

  t.add_domains({'SYS1':r.connect('SYS1').index})
  for f in ['SYS1']:
      assert f in t._domains, f'must be able to add an entry to domains'
      
  with pytest.raises(TypeError):
      t.add_domains({'TEST1':['A','B']} , {'TEST2':[]}), 'only 2 simple parameters on the add_domain method'

  assert len(t._domains)==12, f'must be able to add entries to domains, and not lose original domains'
      
def test_rules_syntax(testparms):
  r = testparms['object']
  t = r.rules
  with pytest.raises(TypeError):
      assert t.syntax_check(), 'syntax_check() does not load a policy, but should require a prior load()'
  assert t.load().syntax_check(confirm=False).empty, 'syntax_check() must return OK message for default policy'

  assert t.load(rules = [ (['GRACC','GRCACC'], {'test': {'field':'AUTH_ID', 'fit':'ACLID'}}) ] ).syntax_check(confirm=False).empty,  'syntax_check() must return OK message for custom policy'

  assert not t.load(rules = [ (['GRACC'], {'test': {'field':'XXX_ID', 'fit':'ACLID'}}) ] ).syntax_check(confirm=False).empty,  'syntax_check() must return error messages'
  assert not t.load(rules = [ (['GRACC'], {'test': {'field':'AUTH_ID', 'noooooo':'ACLID'}}) ] ).syntax_check(confirm=False).empty,  'syntax_check() must return error messages'

  with pytest.warns(UserWarning) as record: # should be RACF object does not have a table :
      t.load(rules = [ (['GRBLAA'], {'test': {'field':'AUTH_ID', 'fit':'ACLID'}}) ] ).syntax_check(confirm=False)
      assert record[0].message.args[0].find('does not have a table')>-1, f'syntax_check shoulld identify incorrect table name'

def test_rules_orphans(testparms):
  r = testparms['object']
  t = r.orphans
  assert len(t)==2, 'orphans produces a list with 2 entries'

def test_rules_report(testparms):
  r = testparms['object']
  t = r.rules.verify()
  
  left = t.columns
  right = ['CLASS', 'PROFILE', 'FIELD_NAME', 'EXPECT', 'ACTUAL', 'COMMENT', 'ID']
  for i in range(7):
      assert left[i]==right[i], f'column {right[i]} in verify() result table'
  for f in ['pick','skip','_frameFilter']:
      assert f in dir(t), f'verify() frame must have {f} method'

