# test the special connect() method, esp. how it drops index fields

def test_connect_1(testparms):
  r = testparms['object']
  connect_sys1 = r.connect('SYS1')
  assert connect_sys1.index.names==['_NAME']
  assert connect_sys1.shape[0]>4, 'at least 5 user connected to SYS1'
  assert connect_sys1.shape[1]>10, 'this many columns'


def test_connect_2(testparms):
  r = testparms['object']
  connect_user = r.connect('**','IBMUSER')
  assert connect_user.index.names==['_GRP_ID']
  assert connect_user.shape[0]>2, 'at least 2 connect groups in IBMUSER'


def test_connect_3(testparms):
  r = testparms['object']
  connect_combo = r.connect('SYS1','IBMUSER')
  assert connect_combo.index.names==['_GRP_ID','_NAME']
  assert connect_combo.shape[0]==1, 'should be only 1 connect SYS1<->IBMUSER'


