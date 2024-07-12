Data Table Properties
=====================

pyRACF dynamically creates a property for every recordtype it parses
from the IRRDBU00 unload. The properties return a DataFrame of the
recordtype with column names the same as those in the `IBM
Documentation <https://www.ibm.com/docs/en/zos/3.1.0?topic=records-irrdbu00-record-types>`__.
For instance, the unloaded basic-user-information (`record Type
200 <https://www.ibm.com/docs/en/zos/3.1.0?topic=utility-user-record-formats>`__)
will have a column name USBD_NAME to contain the “User ID as taken from
the profile name”.

The following properties directly relate to the recordtypes, and mostly
have field names starting with the value under Prefix.

..
   sphinx doesn't truncate or wrap the Property value when it exceeds the column width,
   so added _static/css/custom.css to make the table render properly.

.. _DataFrames:

.. csv-table:: Record types and properties
   :header: "Type", "Prefix", "Property", "Description"
   :widths: 11, 18, 26, 45
   :file: record_type_table.csv


Properties starting with .general are mostly related to access control
profiles that use PERMITs. General resource profiles that represent
(system) tables and switches are stored in properties with names that
reflect the application segment name (in uppercase, optionally followed
by a suffix for lists stored in the segment).

Connect information
-------------------

Connect information is stored in 3 structures in the RACF database.  These structures are represented in 3 properties:

`.connects` and `.groupConnect` present limited information, `.connects` ignores universal groups, and both lack information about group privileges.

Complete information about connections between groups and users, including connect authority, is stored in `.connectData`.

Extra fields added
------------------

Some of these properties have been extended for easier reporting:

.connectData
^^^^^^^^^^^^

Combines fields from USER profiles (0205) and GROUP profiles (0102). The
``GPMEM_AUTH`` field shows group connect authority, whereas all other
field names start with ``USCON``. This property should be used for most
connect group analysis, instead of ``.connects`` and ``.groupConnect``.

.datasets and .generals
^^^^^^^^^^^^^^^^^^^^^^^

Column ``IDSTAR_ACCESS`` is added by selecting records from
``.datasetAccess`` and ``.generalAccess`` referencing ID(\*). The higher
value of *prefix*\ \_UACC and IDSTAR_ACCESS is stored in
``ALL_USER_ACCESS`` indicating the access level granted to all RACF
defined users, except when restricted by specific access.

.groupOMVS and .userOMVS
^^^^^^^^^^^^^^^^^^^^^^^^

Column ``GPOMVS_GID`` and ``USOMVS_UID`` contain the id of the entity in 10 digits with leading zeros, making for errors in specifying a value.
A copy of the GID or UID without leading zeros is available in ``GPOMVS_GID_`` and ``USOMVS_UID_``, resp.

.CERT
^^^^^^^^

Returns a combined DataFrame of the DataFrames ``._generalCERT`` en
``.generals``, copying the ``GRBD_APPL_DATA`` and ``GRBD_UACC`` fields to show the user ID associated with the certificate and the trust level.

.KEYRING
^^^^^^^^

Returns a combined DataFrame of the DataFrames ``._generalKEYRING`` en
``.generals``, copying the ``GRBD_APPL_DATA`` field to show the user ID associated with the keyring.

.SSIGNON
^^^^^^^^

Returns a combined DataFrame of the DataFrames ``._generalSSIGNON`` en
``.generals``, copying the ``GRBD_APPL_DATA`` field to show if replay
protection is available for the passticket.

What are the field names?
--------------------------

To view column names in a DataFrame, use ``.columns``

::

   >>> r.STDATA.columns
   Index(['GRST_RECORD_TYPE', 'GRST_NAME', 'GRST_CLASS_NAME',
          'GRST_USER_ID', 'GRST_GROUP_ID', 'GRST_TRUSTED',
          'GRST_PRIVILEGED', 'GRST_TRACE'],
         dtype='object')

Data Table Indices
------------------

The data tables have index fields assigned to speed up access to entries
and to determine “is this ID present in the .users table”. Index fields
are automatically assigned (generally) as follows. Note that the table
prefix is omitted from the index names to ease table processing.

-  For tables about groups, users and data sets, the ``_NAME`` field
   refers to the profile key.
-  For general resources, ``_CLASS_NAME`` and ``_NAME`` refer to the
   resource class and the profile key, resp.
-  ``.connectData`` uses ``_GRP_ID`` and ``_NAME`` as index fields,
   representing the group name and the user ID, resp. The other two
   connect related tables use the same structure to facilitate merging
   of tables.
-  ``.datasetAccess`` and ``.datasetConditionalAccess`` use ``_NAME``,
   ``_AUTH_ID`` and ``_ACCESS`` as index fields.
-  ``.generalAccess`` and ``.generalConditionalAccess`` use
   ``_CLASS_NAME``, ``_NAME``, ``_AUTH_ID`` and ``_ACCESS`` as index
   fields.

Tables and views derived from these main tables mostly inherit the index
fields. To check the index names used in a DataFrame, use
``.index.names``

::

   >>> r.STDATA.index.names
   FrozenList(['_CLASS_NAME', '_NAME'])


Data selection methods
----------------------

The data table properties from the first section return all profiles and profile data loaded
from the RACF input source. Since they typically return more than one
entry, the property name represents a plural, such as ``.users``.  There are 2 options to
make selections:

 * use standard pandas methods such as ``.loc[ ]`` and ``.query( )``, see :ref:`pandas-methods`, or

 * use RACF specific methods such as ``.find( )``, ``.skip( )``, ``.match( )``, or their deprecated versions ``gfilter( )``, and ``rfilter( )``, see :ref:`selection-methods` for guidance and examples.

There is also a range of methods that select one entry from a specific DataFrame, when you know the name of the entry exactly, see :ref:`specific-selection-methods`.



Analytic Properties
-------------------

These properties present a subset of a DataFrame, or the result of
DataFrame intersections, to identify points of interest.

.specials
^^^^^^^^^

The ``.specials`` property returns a “USBD” DataFrame (like ``.users``) with
all users that have the ‘special attribute’ set. Effectively this is the
same as the result from

``r.users.loc[r.users['USBD_SPECIAL'] == 'YES']``

.operations
^^^^^^^^^^^

Like the ``.specials`` property but now all the users that have the
‘operations attribute’ set are returned.

.auditors
^^^^^^^^^

Returns a DataFrame with all users that have the ‘auditor attribute’

.revoked
^^^^^^^^

Returns a DataFrame with all revoked users.

.groupsWithoutUsers
^^^^^^^^^^^^^^^^^^^

Returns a DataFrame with all groups that have no user IDs connected
(empty groups).

.uacc_read_datasets
^^^^^^^^^^^^^^^^^^^

Returns a DataFrame with all dataset definitions that have a Universal
Access of ‘READ’

.uacc_update_datasets
^^^^^^^^^^^^^^^^^^^^^

Returns a DataFrame with all dataset definitions that have a Universal
Access of ‘UPDATE’

.uacc_control_datasets
^^^^^^^^^^^^^^^^^^^^^^

Returns a DataFrame with all dataset definitions that have a Universal
Access of ‘CONTROL’

.uacc_alter_datasets
^^^^^^^^^^^^^^^^^^^^

Returns a DataFrame with all dataset definitions that have a Universal
Access of ‘ALTER’

.orphans
^^^^^^^^

Returns a tuple of ``.datasetAccess`` DataFrame and ``.generalAccess``
DataFrame with entries that refer to non-existing authid’s.
