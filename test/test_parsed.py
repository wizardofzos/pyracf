# verify the result of parsing, not the actual content of dfs

import pytest 

def test_status(testparms):
  assert testparms['object'].status['status']=='Ready'

def test_parsed_records(testparms):
  r = testparms['object']
  assert r.parsed('USBD')>0, 'group records were loaded'
  assert r.parsed('GRBD')>0, 'general resource records were loaded'
  with pytest.raises(KeyError):
    r.parsed('0100')>0, 'old-fashioned references to record types should not work'

