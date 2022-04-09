# pyracf

## Parsing IRRDBU00 unloads like a boss

    >>> from pyracf import RACF
    >>> mysys = RACF('/path/to/irrdbu00')
    >>> mysys.parse()
    >>> mysys.status
    {'status': 'Still parsing your unload', 'lines-read': 200392, 'lines-parsed': 197269, 'lines-per-second': 63934, 'parse-time': 'n.a.'}
    >>> mysys.status
    {'status': 'Ready', 'lines-read': 7137540, 'lines-parsed': 2248149, 'lines-per-second': 145048, 'parse-time': 49.207921}
    
# Functions 

## parse

Optional argument : thread_count 

This will start one threads (default=1) parsing the unload file as specified at creation time of the instance. Other functions will not be viable before this (background)parsing is done. Current state can be inquired via the .status call.

Example:

    mysys = RACF('/path/to/irrdbu00')
    mysys.parse(thread_count=2)

## status

This will return a json with 5 key-value pairs.

Example Output:

    {
        'status': 'Ready', 
        'lines-read': 7137540, 
        'lines-parsed': 2248149, 
        'lines-per-second': 145048, 
        'parse-time': 49.207921
    }

Note: when running multiple threads, the lines-read will be incremented for every thread.

## users

This will return a dataframe with all "USBD" data from the unload.

Example:

    >>> mysys.users
    USBD_RECORD_TYPE USBD_NAME USBD_CREATE_DATE USBD_OWNER_ID  ... USBD_START_TIME USBD_END_TIME USBD_SECLABEL USBD_PHR_DATE
    0              0200  irrcerta       1999-10-20      irrcerta  ...                                                          
    1              0200  irrmulti       2000-12-02      irrmulti  ...                                                          
    2              0200  irrsitec       1999-10-20      irrsitec  ...                                                          
    3              0200     ADCDA       2007-06-01       IBMUSER  ...                                                          
    4              0200     ADCDB       2007-06-01       IBMUSER  ...                                                          
    ..              ...       ...              ...           ...  ...             ...           ...           ...           ...
    95             0200   ZOSCSRV       2016-03-22          SYS1  ...                                                          
    96             0200   ZOSMFAD       2012-12-04       IBMUSER  ...                                                          
    97             0200   ZOSUGST       2016-03-22          SYS1  ...                                                          
    98             0200  ZWESIUSR       2020-05-06       IBMUSER  ...                                                          
    99             0200  ZWESVUSR       2020-05-06       IBMUSER  ...                     
    
    [100 rows x 33 columns]  

## user(userid)

This retrieves a single user. Effectively the same as:

    mysys.users.loc[mysys.users.USBD.NAME==userid]

## groups

This will return a dataframe with all "GPBD" data from the unload.

Example:

    >>> mysys.groups
       GPBD_RECORD_TYPE GPBD_NAME GPBD_SUPGRP_ID GPBD_CREATE_DATE GPBD_OWNER_ID GPBD_UACC GPBD_NOTERMUACC GPBD_UNIVERSAL
    0              0100      ADCD           SYS1       2012-11-30       IBMUSER      NONE              NO             NO
    1              0100    BLZCFG           SYS1       2014-08-07       ADCDMST      NONE              NO             NO
    2              0100    BLZGRP           SYS1       2014-08-07       IBMUSER      NONE              NO             NO
    3              0100    BLZWRK           SYS1       2014-08-07       ADCDMST      NONE              NO             NO
    4              0100     CEAGP           SYS1       2009-11-17       IBMUSER      NONE              NO             NO
    ..              ...       ...            ...              ...           ...       ...             ...            ...
    57             0100       ZDO           SYS1       2021-05-07       IBMUSER      NONE              NO             NO
    58             0100   ZOSCGRP           SYS1       2016-03-22          SYS1      NONE              NO             NO
    59             0100   ZOSUGRP           SYS1       2016-03-22          SYS1      NONE              NO             NO
    60             0100  ZWEADMIN           SYS1       2020-05-06       IBMUSER      NONE              NO             NO
    61             0100    ZWE100           SYS1       2020-05-06       IBMUSER      NONE              NO             NO

    [62 rows x 8 columns]

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
| orphans | Returns 2 DataFrames one with orphans in dataset profile access lists, and one for generic resources | d, g = mysys.orphans |
| revoked | Returns a DataFrame  with all revoked users | mysys.revoked |
| specials | Returns a DataFrame  with all special users | mysys.specials |
| uacc_read_datasets | Returns a DataFrame  with all dataset profiles having UACC=READ | mysys.uacc_read_datasets |




