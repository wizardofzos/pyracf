## conftest.py is a special file name
## we use it to load the parameter file and RACF unload
## the testparms fixture is referenced in test modules by name (testparms), but because conftest.py is not a test the files are only read once

import pytest
import time
import toml
import warnings
from pyracf import RACF


# several ways to load the DFs
# load the data only the first time, and save the RACF object in testparm with my name.  next calls we just put the RACF object in 'object'
def normalParse(testparm):
    if 'normalParsed' not in testparm:
        r = RACF(testparm['unload'])
        r.parse()
        while r._state != RACF.STATE_READY:
            print(r.status)
            time.sleep(0.5)
        r.status
        testparm.update({'normalParsed':r})
    testparm.update({'object':testparm['normalParsed']})
    return testparm

def fancyParse(testparm):
    if 'fancyParsed' not in testparm:
        r = RACF(testparm['unload'])
        r.parse_fancycli(save_pickles=testparm['pickledir'], prefix=testparm['pickleprefix'])
        r.status
        testparm.update({'fancyParsed':r})
    testparm.update({'object':testparm['fancyParsed']})
    return testparm

def fromPickles(testparm):
    if 'fromPickles' not in testparm:
        r = RACF(pickles=testparm['pickledir'], prefix=testparm['pickleprefix'])
        r.status
        testparm.update({'fromPickles':r})
    testparm.update({'object':testparm['fromPickles']})
    return testparm


# This code will run once before all tests in the directory
with open('testparm.toml', 'r') as f:
     testparm = toml.load(f)

# testparms (with an s) is called once for each source, in each testmember
# we run each testmember with 3 different sources, yield returns testparm with the current source in testparm['object']
sources = [normalParse,fancyParse,fromPickles]
@pytest.fixture(autouse=True,scope="package",params=sources)
def testparms(request):
    yield request.param(testparm)

