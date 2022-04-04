# pyracf

## parsing IRRDBU00 unloads like a boss

    >>> from pyracf import RACF
    >>> mysys = RACF('/path/to/irrdbu00')
    >>> mysys.parse()
    >>> mysys.users().info()
    <class 'pandas.core.frame.DataFrame'>
    RangeIndex: 100 entries, 0 to 99
    Data columns (total 33 columns):
    #   Column             Non-Null Count  Dtype 
    ---  ------             --------------  ----- 
    0   USBD_RECORD_TYPE   100 non-null    object
    1   USBD_NAME          100 non-null    object
    2   USBD_CREATE_DATE   100 non-null    object
    3   USBD_OWNER_ID      100 non-null    object
    4   USBD_ADSP          100 non-null    object
    5   USBD_SPECIAL       100 non-null    object
    6   USBD_OPER          100 non-null    object
    7   USBD_REVOKE        100 non-null    object
    8   USBD_GRPACC        100 non-null    object
    9   USBD_PWD_INTERVAL  100 non-null    object
    10  USBD_PWD_DATE      100 non-null    object
    11  USBD_PROGRAMMER    100 non-null    object
    12  USBD_DEFGRP_ID     100 non-null    object
    13  USBD_LASTJOB_TIME  100 non-null    object
    14  USBD_LASTJOB_DATE  100 non-null    object
    15  USBD_AUDITOR       100 non-null    object
    16  USBD_NOPWD         100 non-null    object
    17  USBD_OIDCARD       100 non-null    object
    18  USBD_REVOKE_CNT    100 non-null    object
    19  USBD_SECLEVEL      100 non-null    object
    20  USBD_REVOKE_DATE   100 non-null    object
    21  USBD_RESUME_DATE   100 non-null    object
    22  USBD_ACCESS_SUN    100 non-null    object
    23  USBD_ACCESS_MON    100 non-null    object
    24  USBD_ACCESS_TUE    100 non-null    object
    25  USBD_ACCESS_WED    100 non-null    object
    26  USBD_ACCESS_THU    100 non-null    object
    27  USBD_ACCESS_FRI    100 non-null    object
    28  USBD_ACCESS_SAT    100 non-null    object
    29  USBD_START_TIME    100 non-null    object
    30  USBD_END_TIME      100 non-null    object
    31  USBD_SECLABEL      100 non-null    object
    32  USBD_PHR_DATE      100 non-null    object
    dtypes: object(33)

