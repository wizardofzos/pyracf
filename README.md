# pyracf

PyRACF is a module to easily parse and query the setup of any RACF database. It consumes the IRRDBU00 unload and creates "Panda DataFrames" for every 'recordtype'. See https://www.ibm.com/docs/en/zos/2.1.0?topic=records-irrdbu00-record-types and https://www.ibm.com/docs/en/zos/2.5.0?topic=records-record-formats-produced-by-database-unload-utility for a description of these records. The DataFrames will have the same 'fieldnames' as described in the docs.

## Parsing IRRDBU00 unloads like a boss

    >>> from pyracf import RACF
    >>> mysys = RACF('/path/to/irrdbu00')
    >>> mysys.parse()
    >>> mysys.status
    {'status': 'Still parsing your unload', 'lines-read': 200392, 'lines-parsed': 197269, 'lines-per-second': 63934, 'parse-time': 'n.a.'}
    >>> mysys.status
    {'status': 'Ready', 'lines-read': 7137540, 'lines-parsed': 2248149, 'lines-per-second': 145048, 'parse-time': 49.207921}
    

## All functions

| Function/Property | Explanation | Example |
|---|---|---|
| auditors | Returns DataFrame with all user having the auditor bit switched on | mysys.auditors |
| connects | Returns DataFrame with all user to group connects | mysys.connects |
| datasetAccess | Returns DataFrame with all Accesslists for all dataset profiles | mysys.datasetsAccess |
| datasets | Returns DataFrame with all datasetprofiles | mysys.datasets |
| genericAccess | Returns DataFrame with with all accesslists for generic resource profiles | mysys.genericAccess
| generics | Returns DataFrame with with all generic resource profiles | mysys.generics 
| group | Returns DataFrame with with one dataset profile only | mysys.group('SYS1') |
| groups | Returns DataFrame with all group data | mysys.groups |
| operations | Returns a DataFrame  with all operations users | mysys.operations |
| orphans | Returns 2 DataFrames one with orphans in dataset profile access lists, and one for generic resources | d, g = mysys.orphans |
| revoked | Returns a DataFrame  with all revoked users | mysys.revoked |
| specials | Returns a DataFrame  with all special users | mysys.specials |
| status | Returns JSON with parsing status | mysys.status |
| uacc_read_datasets | Returns a DataFrame  with all dataset profiles having UACC=READ | mysys.uacc_read_datasets |
| xls | Creates an XLSX with all permits per class | mysys.xls(fileName='myxls.xlsx') |

# Example use-case

Get all users that have not logged in (on?) since January 1st 2022. And print userID and last logon...

    import time
    from pyracf import RACF

    mysys = RACF('/path/to/irrdbu00')
    mysys.parse()
    while mysys.status['status'] != 'Ready':
        time.sleep(5)
    selection = mysys.users.loc[mysys.users.USBD_LASTJOB_DATE<="2022-01-01"][['USBD_NAME','USBD_LASTJOB_DATE']]
    for user in selection.values:
      print(f"Userid {user[0]}, last active: {user[1]})

Create a neat XLSX

    from pyracf import RACF
    mysys = RACF('/path/to/irrdbu00')
    mysys.parse()
    while mysys.status['status'] != 'Ready':
        time.sleep(5)
    mysys.xls('/path/to/my.xlsx')


# Contribute to PyRACF

If you've some additions and/or bugfixes, feel free to [fork](https://github.com/wizardofzos/pyracf/fork) this repository, make your additions and fire a pull request.




