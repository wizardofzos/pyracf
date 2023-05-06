# pyracf

## PyRACF: A Python module for analyzing RACF security

PyRACF is a powerful Python module that simplifies the parsing and querying of any RACF database, providing an efficient and intuitive way to analyze security setups on IBM Z systems. By consuming the IRRDBU00 unload, PyRACF generates "Panda DataFrames" for each 'recordtype', which allow for seamless manipulation and analysis of the data.

Pandas is a powerful data manipulation library in Python that allows for easy querying of the DataFrames generated by PyRACF. With Pandas, you can perform complex queries on the security data to extract meaningful insights into the security posture of your system.

PyRACF's support for saving and loading pickle files makes it easier than ever to work with large RACF datasets, giving you the ability to perform comprehensive analyses of your security setup.

For more information on the various records, please refer to the [IBM documentation](https://www.ibm.com/docs/en/zos/2.1.0?topic=records-irrdbu00-record-types) on IRRDBU00 record types and the [record formats](https://www.ibm.com/docs/en/zos/2.5.0?topic=records-record-formats-produced-by-database-unload-utility) produced by the database unload utility. The DataFrames generated by PyRACF feature the same 'fieldnames' as outlined in the documentation, ensuring consistency and accuracy in your analyses.

To get started with PyRACF, install it using `pip install pyracf` or explore the source code on [GitHub](https://github.com/wizardofzos/pyracf/releases/latest). Use PyRACF to take control of your security data and protect your IBM Z systems from threats.


## Updates

### 0.6.2 (Fix XLSX Creation)
- With newer versions of XlsxWriter there's no more .save(). Changed to .close()
- Pinned pandas and XlsxWriter versions in setup.py 

### 0.6.1 (Bug free?)
- XLS generation fully functional again (also for z/VM unloads)
- Oprhan detection working again
- Conditional Dataset Access Records now parsing correctly
- Conditional Dataset Access now correctly pickled :)
- Fixed parsing of GRCACC records (had misparsed AUTH_ID)
- Conditional Generic (General) Records now with correct column name (GRCACC_CLASS_NAME)
  
### 0.5.4 (Even more recordtypes!!)
- new property: genericConditionalAccess. Will show GRCACC records.
- Fixed some nasty 'default recordtypes' bugs
  
### 0.5.0 (Pickle FTW!)

- new function: save_pickles(path=path, prefix=prefix). Will save all parsed dataframes as pickles (/path/_prefix_*RECORDTYPE*.pickle)
- Can now initialize RACF object from pickle-folder/prefix. To reuse earlier saves pickle files. See examples below
- parse_fancycli now has two optional arguments (save_pickles and prefix) to also save pickle files after parsing to the directory as specified in save_pickles. The prefix argument is only useed with save_pickles isn't False

### 0.4.5 (Fix Community Update Bug, thanks @Martydog)

- Group Connections now actually usable :)
### 0.4.4

- Internal constants for all recordtypes
- Improved 'parse_fancycli()'

### 0.4.3 (Community Update, thanks @Martydog)

- Add User Group Connections record 203 
- Add User Installation Data record 204

### 0.4.2

- Now XLS generation has more checks (fails gracefully if not all required records parsed, works when only genericAccess parsed)
- Same for Orphan detection
- Recordtype 0503 (General Resource Members/genericMembers) added
  
## Parsing IRRDBU00 unloads like a boss

    >>> from pyracf import RACF
    >>> mysys = RACF('/path/to/irrdbu00')
    >>> mysys.parse()
    >>> mysys.status
    {'status': 'Still parsing your unload', 'lines-read': 200392, 'lines-parsed': 197269, 'lines-per-second': 63934, 'parse-time': 'n.a.'}
    >>> mysys.status
    {'status': 'Ready', 'lines-read': 7137540, 'lines-parsed': 2248149, 'lines-per-second': 145048, 'parse-time': 49.207921}
    
### Using Pickle Files

    >>> from pyracf import RACF
    >>> mysys = RACF('/path/to/irrdbu00')
    >>> mysys.parse_fancycli(save_pickles='/tmp/pickles', prefix='mysys-')
    >>> hash(mysys.groups.values.tobytes())
    -8566685915584060910

Then later, you don't need to parse the same unload again, just do:

    >>> from pyracf import RACF
    >>> mysys = RACF(pickles='/tmp/pickles', prefix='mysys-')
    >>> hash(mysys.groups.values.tobytes())
    -8566685915584060910


## All functions

| Function/Property | Explanation | Example |
|---|---|---|
| auditors | Returns DataFrame with all user having the auditor bit switched on | mysys.auditors |
| connects | Returns DataFrame with all user to group connects | mysys.connects |
| datasetAccess | Returns DataFrame with all Accesslists for all dataset profiles | mysys.datasetsAccess |
| datasets | Returns DataFrame with all datasetprofiles | mysys.datasets |
| genericAccess | Returns DataFrame with with all accesslists for generic resource profiles | mysys.genericAccess
| genericConditionalAccess | Returns DataFrame with with all conditional accesslists for generic resource profiles | mysys.genericConditionalAccess
| generics | Returns DataFrame with with all generic resource profiles | mysys.generics 
| group | Returns DataFrame with with one dataset profile only | mysys.group('SYS1') |
| groupConnect | Returns DataFrame with with user group connection records (0203 recordtype) | mysys.groupConnect |
| groups | Returns DataFrame with all group data | mysys.groups |
| installdata | Returns DataFrame with with user installation data (0204 recordtype) | mysys.installdata |
| operations | Returns a DataFrame  with all operations users | mysys.operations |
| orphans | Returns 2 DataFrames one with orphans in dataset profile access lists, and one for generic resources | d, g = mysys.orphans |
| parse | parses the unload. optional specify recordtypes | mysys.parse(recordtypes=['0200']) |
| parse_fancycli | parses the unload with a fancy cli status update. optional recordtypes can be specified | mysys.parse_fancycli(recorddtypes=['0200']) |
| revoked | Returns a DataFrame  with all revoked users | mysys.revoked |
| save_pickles | Saves all parsed types as pickle files | mysys.save_pickles(path='/tmp', prefix='mysys-') |
| specials | Returns a DataFrame  with all special users | mysys.specials |
| status | Returns JSON with parsing status | mysys.status |
| uacc_read_datasets | Returns a DataFrame  with all dataset profiles having UACC=READ | mysys.uacc_read_datasets |
| xls | Creates an XLSX with all permits per class | mysys.xls(fileName='myxls.xlsx') |

# Example use-case

Get all users that have not logged in (on?) since January 1st 2022. And print userID and last logon...

    import time
    from pyracf import IRRDBU

    mysys = IRRDBU('/path/to/irrdbu00')
    mysys.parse()
    while mysys.status['status'] != 'Ready':
        time.sleep(5)
    selection = mysys.users.loc[mysys.users.USBD_LASTJOB_DATE<="2022-01-01"][['USBD_NAME','USBD_LASTJOB_DATE']]
    for user in selection.values:
      print(f"Userid {user[0]}, last active: {user[1]}")

Create a neat XLSX

    import time
    from pyracf import IRRDBU
    mysys = IRRDBU('/path/to/irrdbu00')
    mysys.parse()
    while mysys.status['status'] != 'Ready':
        time.sleep(5)
    mysys.xls('/path/to/my.xlsx')

# Updates 

In this version we introduced IRRRDBU as an alternative to RACF. Examples have been updated. The RACF class from previous version is still available, but you're advised to change this to IRRDBU, as future version will have another user of the RACF class.

# Contribute to PyRACF

If you've some additions and/or bugfixes, feel free to [fork](https://github.com/wizardofzos/pyracf/fork) this repository, make your additions and fire a pull request.




