Output specification
====================

The data tables described in :ref:`DataFrames` contain many entries, and each entry will have many columns.
To find entries you can use standard pandas methods, or one of the
methods specific for the RACF tables, described in :ref:`Selection-methods`.
This chapter shows how to customize output of the entries.

A DataFrame is a pandas object that is similar to a list of dictionaries (dicts).
In fact, that is exactly how pyRACF feeds the RACF profile data into pandas.
A row in the DataFrame is a list of (named) fields, a column in the DataFrame has a name, and many values.

In a traditional DataFrame the rows are numbered, but pyRACF assigns the value of one through four columns as *index* values.
In the resulting ``ProfileFrames``, the rows are identified by the *profile key* for groups, users and data sets, *class* and *profile* for general resource profiles, *group* and *user ID* for connectData.
For access list entries, *access list ID* and *access level* are also used as *index* values.

These index values are printed in **bold** in front of the *data values* of the row.  The will (all) be printed, even when you select only a few columns of the ProfileFrame.

Selecting columns for output
----------------------------

A column in a DataFrame is similar to an entry in a dictionary (dict), in the sense that the column has a name and how you access the column.  If you wanted to print the 'brand' entry of your car dict, you would write car['brand'].
This is how you would print the name of all user IDs::

    >>> r.users['USBD_PROGRAMMER']

    _NAME
    irrcerta         CERTAUTH Anchor
    irrmulti         Criteria Anchor
    irrsitec             SITE Anchor
    ADCDA                      ADCDA
    ADCDB                      ADCDB

However, if you wanted to print 2 or more columns, pandas expects a list of field names, instead of one name::

    >>> r.users[['USBD_PROGRAMMER','USBD_LASTJOB_DATE','USBD_LASTJOB_TIME']]

                USBD_PROGRAMMER     USBD_LASTJOB_DATE   USBD_LASTJOB_TIME
    _NAME           
    irrcerta    CERTAUTH Anchor         
    irrmulti    Criteria Anchor         
    irrsitec    SITE Anchor         
    ADCDA       ADCDA               2010-05-03           16:25:32
    ADCDB       ADCDB               2009-12-14           16:53:49

You will notice a more austere layout with 1 column than with several columns. In fact, with 1 column output, the result is a ``Series``, whereas with multiple columns, the result is a ``DataFrame``.

How do we know these column names?

 * use the columns attribute of the DataFrame  ``r.users.columns``, or
 * look at the `IBM documentation <https://www.ibm.com/docs/en/zos/3.1.0?topic=utility-user-record-formats>`__

pyRACF supports all the field names for all the record types documented in this list, with the same documented column names.
For consistency and support this is great, but you may get fed-up with typing the identical field prefix for all the columns.
Don't worry, there is a fix: the ``stripPrefix`` method is available on ``ProfileFrames``, it removes the prefix in its return value::

    >>> r.users.stripPrefix()[['PROGRAMMER','LASTJOB_DATE','LASTJOB_TIME']]

                PROGRAMMER              LASTJOB_DATE    LASTJOB_TIME
    _NAME           
    irrcerta    CERTAUTH Anchor         
    irrmulti    Criteria Anchor         
    irrsitec    SITE Anchor         
    ADCDA       ADCDA                   2010-05-03      16:25:32
    ADCDB       ADCDB                   2009-12-14      16:53:49

What about the field name list, do you worry about counting quotes and commas?
Well, it is a list, and you can easily create a list from a string using the split() method, and no need for double brackets either::

    >>> r.users.stripPrefix()[ 'PROGRAMMER LASTJOB_DATE LASTJOB_TIME'.split() ]

Just remember, split() is a method that works on the str value.  And [ ] indexing works on a value, or on the result of a method, so don't add a ``.`` inbetween.

Look at the default layout for dataset profiles::

    >>> r.datasets

        DSBD_RECORD_TYPE    DSBD_NAME   DSBD_VOL    DSBD_GENERIC    DSBD_CREATE_DATE    DSBD_OWNER_ID   DSBD_LASTREF_DATE 
    _NAME                                                                                   
    ACEUSER.**      0400    ACEUSER.**              YES     2021-01-08  SYS1    2021-01-08  2021-01-08  00000   00000   ...     
    ACEV2.**        0400    ACEV2.**                YES     2021-01-18  SYS1    2021-01-18  2021-01-18  00000   00000   ...     
    ADBC10.**       0400    ADBC10.**               YES     2022-01-04  SYS1    2022-01-04  2022-01-04  00000   00000   ...     
    ADCD.S0W1.**    0400    ADCD.S0W1.**            YES     2014-02-18  SYS1    2014-02-18  2014-02-18  00000   00000   ... 
    ADCD.**         0400    ADCD.**                 YES     2012-01-10  NOTTHERE    2012-01-10  2012-01-10  00000   00000   ...     

You cannot even see the UACC field, so what about::

	>>> r.datasets.stripPrefix()['UACC IDSTAR_ACCESS ALL_USER_ACCESS OWNER_ID'.split()]

	               UACC    IDSTAR_ACCESS   ALL_USER_ACCESS     OWNER_ID
	_NAME               
	ACEUSER.**     NONE                    NONE                SYS1
	ACEV2.**       NONE    UPDATE          UPDATE              SYS1
	ADBC10.**      NONE                    NONE                SYS1
	ADCD.S0W1.**   NONE                    NONE                SYS1
	ADCD.**        READ                    READ                NOTTHERE

You can combine these output specifications with selection methods:

``r.datasets.find(ALL_USER_ACCESS='READ UPDATE CONTROL ALTER'.split()) \``
``.stripPrefix()['UACC IDSTAR_ACCESS ALL_USER_ACCESS OWNER_ID'.split()]``

or

``r.datasets.skip(ALL_USER_ACCESS='NONE') \``
``.stripPrefix()['UACC IDSTAR_ACCESS ALL_USER_ACCESS OWNER_ID'.split()]``

.. automethod:: pyracf.profile_frame.ProfileFrame.stripPrefix

Data presentation methods
-------------------------

.acl( )
^^^^^^^^

The ``.acl`` method can be used on DataFrames with dataset and general
resource profile, and on the corresponding access frames, to present
various views of the access controls defined in these profiles.

When ``.acl`` is used on ``.datasets`` or ``.generals``, normal and conditional access information is combined in the output.
When ``.acl`` is used on one of the access frame,  ``.acl`` shows just this data.

``.acl`` returns a DataFrame without the prefixes of the originating frames.

::

   >>> r.datasets.find('SYS1.**').acl()
                 NAME  VOL USER_ID AUTH_ID ACCESS
   ----------------------------------------------
              SYS1.**      -group-    SYS1  ALTER
              SYS1.**        SPROG   SPROG  ALTER
              SYS1.**        TCPIP   TCPIP   READ
         SYS1.**.PAGE      -group-    SYS1  ALTER
        SYS1.BRODCAST            *       *   READ

The default layout shows *permits* much like the output of LISTDSD,
except a column ``USER_ID`` is added. This contains the word ``-group-``
if the ``AUTH_ID`` was found in ``r.groups``.


::

   # user IDs with access on SYS1.PARMLIB (if this profile exists)
   r.dataset('SYS1.PARMLIB').acl(resolve=True)

   # permits with UPDATE on any SYS1 dataset profile
   r.datasets.find('SYS1.**').acl(access='UPDATE')

   # permits with UPDATE, CONTROL or ALTER on any SYS1 dataset profile
   r.datasets.find('SYS1.**').acl(allows='UPDATE')

   # users that can make changes to SYS1 datasets
   r.datasets.find('SYS1.**').acl(allows='UPDATE',resolve=True)

To filter the output of ``.acl()`` you can chain ``.query()`` or ``find()``,
referencing the column names like so:

::

   # access scope of IBMUSER in SYS1 data sets
   r.datasets.find('SYS1.**')\
             .acl(resolve=True)\
             .query("USER_ID=='IBMUSER'")


   # access scope of IBMUSER in SYS1 data sets
   r.datasets.find('SYS1.**')\
             .acl(resolve=True)\
             .find(user='IBMUSER')

.acl( ) syntax
^^^^^^^^^^^^^^

.. automethod:: pyracf.profile_frame.ProfileFrame.acl

.. automethod:: pyracf.profile_frame.AclFrame.find

.. automethod:: pyracf.profile_frame.AclFrame.skip


