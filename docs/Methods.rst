Methods to use on DataFrames
============================

The data tables described in :ref:`DataFrames` present many entries.
To find entries you can use standard pandas methods, or one of the
methods specific for the RACF tables, relying on the index structure of
these DataFrames. The result of these selections is another DataFrame.

In the examples below, ``r`` is a RACF object created from
:ref:`parsing`.

Selection Methods
-----------------

The data tables are designed with an index to allow fast access and
merging, but also provide easy to use selection capabilities. Depending
on the entity type or RACF attribute stored in the table, one or more
fields are assigned as index fields. These same index fields, in the
same order, can be used with the following selection methods.

.gfilter(*mask*, *mask*, ... )
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``.gfilter`` method emulates RACF generic filtering as implemented
by the ``SEARCH FILTER( )`` TSO command. The generic characters ``*``
and ``%`` in these masks apply to the values in the RACF fields,
ignoring the meaning of those characters in the profile field.

However, ``'*'`` looks for a single ``*`` in the field, such as with
``ID(*)``. A value of ``'**'`` or ``None`` in a parameter means that any
value is acceptable.

To select all data set profiles that start with SYS, you write

::

   >>> r.datasets.gfilter('SYS*.**')
   SYSCSF.*.**
   SYSHSM.**
   SYS1.BRODCAST
   SYS1.DFQP*
   SYS1.DFQ*
   SYS1.HRF*
   SYS1.V%%%%%%.**
   SYS1.**.PAGE
   SYS1.**
   SYS2.RACFDS
   SYS2.RACFDS.BACKUP
   SYS2.**

For general resource profiles, you specify the class name and the
profile key, as literals or patterns, for example

::

   # all FACILITY profiles starting with BPX
   r.generals.gfilter('FACILITY', 'BPX.**')    
   
   # all general resource profiles starting with BPX
   r.generals.gfilter('**', 'BPX.**')          
   
   # all UNIXPRIV profiles
   r.generals.gfilter('UNIXPRIV')              

For PERMITs, the ID and ACCESS values are available for selection too:

::

   # dataset profiles where IBMUSER is permitted
   r.datasetAccess.gfilter('**', 'IBMUSER')     
   
   # IDs with UPDATE PERMIT on a SYS1 dataset profile    
   r.datasetAccess.gfilter('SYS1.**', None, 'UPDATE')
   
   # dataset where ID(*) has conditional access   
   r.datasetConditionalAccess.gfilter(None, '*')    

   # UPDATE on a UNIXPRIV profile
   r.generalAccesss.gfilter('UNIXPRIV', '**', '**', 'UPDATE')   

For group and user profiles, only one parameter is needed. Two
parameters can be given for connect information:

::

   r.groups.gfilter('CSF*')
   
   r.users.gfilter('IBM*')

   # users connected to SYS1, SYS2, etc.
   r.connectData.gfilter('SYS%')   
   
   # groups connected to PROD user IDs
   r.connectData.gfilter('**', '%%%%PROD')   

Note: to check the index names defined in a DataFrame, use
``.index.names``

::

   >>> r.STDATA.index.names
   FrozenList(['_CLASS_NAME', '_NAME'])

If there is no matching value, an empty DataFrame will be produced.

.rfilter(*regex*, *regex*, ... )
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``.rfilter`` method provides regular expression matching to the
index fields of the DataFrame. Remember that ``*`` and ``.`` in these
patterns have a special significance, so prefix them with ``\`` if you
want to search for ``*`` and ``.`` in the RACF fields.

::

   # SYS1 and SYS2 profiles 
   r.datasets.rfilter('SYS[12]\..*')   
   
   # dataset where ID(*) has conditional access
   r.datasetConditionalAccess.rfilter(None, '\*')
   
   # user IDs with ADM anywhere
   r.users.rfilter('.*ADM')         
   
   # groups ending in USER   
   r.groups.rfilter('\S+USER$')        

.. _pandas-methods:

Pandas Methods
--------------

Data tables can also be processed with `standard methods documented for
pandas <https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html>`__.

.loc[*value*, *value*, ... ]
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The exact value is looked up in the index field(s). This method is very
fast, but an ugly ``KeyError`` is issued when there is no exact match.
``.gfilter`` also uses the index fields, but suppresses the
``KeyError``.

If there is one match, the result is given in a Series. To ensure the
result is passed back as a DataFrame, you can double up the square
brackets.

::

   >>> r.users.loc['IBMUSER']
   ... Series object

   >>> r.users.loc[['IBMUSER']]
   ... DataFrame

If the data table has more than one index field, and only one value is
given in ``.loc[ ]``, a DataFrame is produced with all entries for the
value given.

::

   >>> r.STDATA.loc['STARTED']
   ... DataFrame

   >>> r.STDATA.loc['STARTED','ASCH.*']
   GRST_RECORD_TYPE       0540
   GRST_NAME            ASCH.*
   GRST_CLASS_NAME     STARTED
   GRST_USER_ID         START2
   GRST_GROUP_ID              
   GRST_TRUSTED             NO
   GRST_PRIVILEGED          NO
   GRST_TRACE               NO
   Name: (STARTED, ASCH.*), dtype: object

   >>> r.STDATA.loc[[('STARTED','ASCH.*')]]
   ... DataFrame

By design, you specify index values as literals from the first level up,
as in the previous examples. However, if you have to search the table
for a value on, say, the third level and show any values found on the
first two levels, you cannot just type ``None`` in those levels.
Instead, you can use a “select anything” generator, enclose all
selections in parentheses, and ensure that this tuple only acts on
``axis=0`` by adding a comma at the end. This is how you would find all
permits to ID(*) in general resource profiles:

::

   r.generalAccess.loc[(slice(None),slice(None),'*'),]

This is exactly what ``.gfilter('**','**','*')`` would do, but more like
a RACF person thinks.

Note: - .loc uses square brackets to specify the index value(s). - if a
table has more than one index field, you may specify one or several, as
long as they are in the right order. - if a table has more than one
index field and you use the double brackets method, specify the index
values as a tuple.

.loc[*bit array*]
^^^^^^^^^^^^^^^^^^

The bit array variant of ``.loc[ ]`` can be used to search any of the
fields in the table. The field names must be qualified with the table
name, like so:

::

   # IBM anywhere in the programmer name field
   r.users.loc[ (r.users.USBD_PROGRAMMER.str.contains('IBM')) ]    

   # trusted and privileged started tasks
   r.STDATA.loc[ (r.STDATA.GRST_TRUSTED=='YES')
               | (r.STDATA.GRST_PRIVILEGED=='YES') ]   

   # permits given to user IDs
   r.datasetAccess.loc[ r.datasetAccess.DSACC_AUTH_ID.isin(r.users.index) ]   

   # orphan permits
   r.datasetAccess.loc[
        ~ ( (r.datasetAccess.DSACC_AUTH_ID.isin(r.users.index) ) 
          | (r.datasetAccess.DSACC_AUTH_ID.isin(r.groups.index) )
          | (r.datasetAccess.DSACC_AUTH_ID=='*' ) ) 
   ]         

Note: - .loc uses square brackets to specify the selection. - yes, you
have to enter the full names of the data table inside the brackets. -
use ``.r.users.columns`` to find the name of the columns in a table. -
.loc[ ] with one array is somewhat intuitive, with two or more arrays,
each selection must be captured in parentheses, and the groups combined
with the logical operators ``&``, ``|`` and ``~``.

.query(*query string*)
^^^^^^^^^^^^^^^^^^^^^^

The ``.query`` method makes it easier to search for records with values
in specific fields, but documentation about the detailed syntax is hard
to find. Here are some
`examples <https://pythonmldaily.com/posts/pandas-dataframe-query-method-syntax-options>`__
and `some more <https://www.google.com/search?q=pandas+query+method>`__.
Also, you must write your query with two levels of quotes, one to
enclose the query and another to specify literal strings. At least you
do not have to refer to the table name in the query.

Like most methods, the result of one ``.query()`` can be passed (or
chained) into another. The ``\`` serves as a continuation mark, like
``,`` in JCL and Rexx.

::

   # privileged users
   r.users.query("USBD_SPECIAL=='YES' or USBD_OPER=='YES'" +
                 " or USBD_AUDITOR=='YES' or USBD_ROAUDIT=='YES'")\
          .query("USBD_REVOKE=='YES'")

   # datasets with UACC>READ
   r.datasets.query("DSBD_UACC==['UPDATE','CONTROL','ALTER']")  

You can also correlate fields in one table with entries in another
table.

::

   # system special user forgot to remove themselves from OWNER( )
   r.datasets.query("DSBD_OWNER_ID in @r.specials.index")   

You can find all entries in .users that have a group connection to
SYSPROG as follows. This references the user ID in index field
``r.users._NAME`` with the IDs connected to SYSPROG via the index:

::

   r.users.query("_NAME in @r.connect('SYSPROG').index")

Query gives us access to the index field in the table, so we don’t have
to remember it’s called \_NAME:

::

   r.users.query("index in @r.connect('SYSPROG').index")

You can also chain operators, for example to select the class of
profiles first, considering that index based .loc[] is very fast and
chaining it before query() drastically reduces the number entries
query() has to test.

::

   # conditional permission for operator commands from (SDSF etc) console
   r.generalConditionalAccess.loc['OPERCMDS']\
                             .query("GRCACC_CATYPE=='CONSOLE'")

Data presentation methods
-------------------------

.acl(permits=True, explode=False, resolve=False, admin=False, access=None, allows=None, sort="profile")
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``.acl`` method can be used on DataFrames with dataset and general
resource profile, and on the corresponding access frames, to present
various views of the access controls defined in these profiles.

When ``.acl`` is used on ``.datasets`` or ``.generals``, normal and conditional access information is combined in the output.
When ``.acl`` is used on one of the access frame,  ``.acl`` shows just this data.

``.acl`` returns a DataFrame without the prefixes of the originating frames.

::

   >>> r.datasets.gfilter('SYS1.**').acl()
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

permits=[ True | False ]
""""""""""""""""""""""""""

Show permits found in the profiles, with annotation if an ``AUTH_ID`` is
a group name.

explode=[ False | True ]
""""""""""""""""""""""""""

Replace each group in ``AUTH_ID`` with the user IDs connected to the
group, put the result in ``USER_ID``. A user ID may occur several times
in ``USER_ID`` with various ``ACCESS`` levels.

resolve=[ False | True ]
""""""""""""""""""""""""""

Show the ``ACCESS`` level that RACF would allow for each user ID in
``USER_ID`` with one of the originating group names in ``AUTH_ID``. A
user ID will only occur once in ``USER_ID`` for each profile.

admin=[ False | True ]
""""""""""""""""""""""""""

Shows the user IDs with the authority to issue RACF commands that change
the profile, or any of the permitted groups. The privilege that allows
the change is listed in ``AUTHORITY`` and the object or entity involved
can be found in ``VIA``.

access=[ None | 'NONE' | 'READ' | 'UPDATE' | 'CONTROL' | 'ALTER' ]
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Show only permits of the given access level. The value must be a quoted
string. Specify None (without quotes) to show all permits.

allows=[ None | 'NONE' | 'READ' | 'UPDATE' | 'CONTROL' | 'ALTER' ]
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Show permits that include/permit the given access level. The value must
be a quoted string. Specify None (without quotes) to show all permits.

sort=[ 'profile' | 'user' | 'id' | 'access' | 'admin' ]
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Sort the output by the given column value. The sort field must be a
quoted string.

::

   # user IDs with access on SYS1.PARMLIB (if this profile exists)
   r.dataset('SYS1.PARMLIB').acl(resolve=True)  
   
   # permits with UPDATE on any SYS1 dataset profile
   r.datasets.gfilter('SYS1.**').acl(access='UPDATE')  

   # permits with UPDATE, CONTROL or ALTER on any SYS1 dataset profile
   r.datasets.gfilter('SYS1.**').acl(allows='UPDATE')  
   
   # users that can make changes to SYS1 datasets
   r.datasets.gfilter('SYS1.**').acl(allows='UPDATE',resolve=True)  

To filter the output of ``.acl()`` you can chain ``.query()``,
referencing the column names like so:

::

   # access scope of IBMUSER in SYS1 data sets
   r.datasets.gfilter('SYS1.**')\
             .acl(resolve=True)\
             .query("USER_ID=='IBMUSER'")   
