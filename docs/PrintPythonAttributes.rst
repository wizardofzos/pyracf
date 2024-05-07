Printable and python object attributes
======================================

Group Structure Properties
--------------------------

PyRACF presents two views of the RACF group tree: the link between
groups through superior groups and subgroups, and the link through OWNER
fields. These properties can be printed in two formats, the underlying
structure can also be accessed through a dictionary, with superior
levels as dict keys and the lower level groups as lists.

::

   >>> r.ownertree
   {'ADCDMST': ['BLZCFG', 'BLZWRK', 'XACFG', 'XAGUESTG', 'XASRVG'],
    'IBMUSER': ['ADCD',
     'BLZGRP',
     'CEAGP',
     'CFZADMGP',
     'CFZSRVGP',
     'CFZUSRGP',
     'CIMGP',
     'IMWEB',
     'IYU',
     'IYU0',
     'IYU0RPAN',
     'IYU0RPAW',
     'IYU000',
     'IZUADMIN',
     'IZUNUSER',
     'IZUSECAD',
     'IZUUNGRP',
     'IZUUSER',
     'STCGROUP',
     'SYSCTLG',
     {'SYS1': ['DB2',
       {'WEBGRP': ['EMPLOYEE', 'EXTERNAL']},
       'ZOSCGRP',
       'ZOSUGRP']},
     'TEST',
     'TTY',
     'USERCAT',
     'ZWEADMIN',
     'ZWE100']}

.grouptree
~~~~~~~~~~~~~~

The grouptree property starts with SYS1 and shows how subgroups descend
from SYS1.

::

   >>> print(r.grouptree)
    SYS1
    ├ ADCD
    ├ BLZCFG
    ├ BLZGRP
    ├ BLZWRK
    ├ CEAGP
    ├ CFZADMGP
    ├ CFZSRVGP
    ├ CFZUSRGP
    ├ CIMGP
    ├ IMWEB
    ├ IYU
    │ ├ IYU0
    │ │ └ IYU000
    │ ├ IYU0RPAN
    │ └ IYU0RPAW
    ├ IZUADMIN
    ├ IZUNUSER
    ├ IZUSECAD
    ├ IZUUNGRP
    ├ IZUUSER
    ├ VSAMDSET
    ├ WEBGRP
    │ ├ EMPLOYEE
    │ └ EXTERNAL
    ├ ZWEADMIN
    └ ZWE100

.ownertree
~~~~~~~~~~~~~~

The ownertree property starts with IBMUSER and all other user IDs that
are specified as OWNER of a group. It shows the groups that reference
these owners, and groups that reference those groups through OWNER, etc.

This ownership structure is critical in understanding the scope of the
group privileges: group special, group operations and group auditor.

Note, there may be several user IDs identified as starting point, these
are referred to as “breaks in the ownership tree”.

::

   >>> print(r.ownertree)
    ADCDMST
    ├ BLZCFG
    ├ BLZWRK
    ├ XACFG
    ├ XAGUESTG
    └ XASRVG
    IBMUSER
    ├ ADCD
    ├ BLZGRP
    ├ CEAGP
    ├ CFZADMGP
    ├ CFZSRVGP
    ├ CFZUSRGP
    ├ CIMGP
    ├ IMWEB
    ├ IYU
    ├ IYU0
    ├ IYU0RPAN
    ├ IYU0RPAW
    ├ IYU000
    ├ IZUADMIN
    ├ IZUNUSER
    ├ IZUSECAD
    ├ IZUUNGRP
    ├ IZUUSER
    ├ STCGROUP
    ├ SYSCTLG
    ├ SYS1
    │ ├ DB2
    │ ├ WEBGRP
    │ │ ├ EMPLOYEE
    │ │ └ EXTERNAL
    │ ├ ZOSCGRP
    │ └ ZOSUGRP
    ├ TEST
    ├ TTY
    ├ USERCAT
    ├ ZWEADMIN
    └ ZWE100

.setformat(*format*)
~~~~~~~~~~~~~~~~~~~~~~~~~~

The default format used for printing the group structure trees is
similar to the Unix ``tree`` command, and uses unicode box drawing
characters. If these characters prove difficult to process, an
alternative format can be selected. Valid format names are simple and
unix.

::

   >>> r.grouptree.setformat('simple')
   >>> print(r.grouptree)
    SYS1
    | ADCD
    | BLZCFG
    | BLZGRP
    | BLZWRK
    | CEAGP
    | CFZADMGP
    | CFZSRVGP
    | CFZUSRGP
    | CIMGP
    | IMWEB
    | IYU
    | | IYU0
    | | | IYU000
    | | IYU0RPAN
    | | IYU0RPAW
    | IZUADMIN
    | IZUNUSER
    | IZUSECAD
    | IZUUNGRP
    | IZUUSER
    | VSAMDSET
    | WEBGRP
    | | EMPLOYEE
    | | EXTERNAL
    | ZWEADMIN
    | ZWE100

.format(*format*)
~~~~~~~~~~~~~~~~~~~~~~~

``.format()`` returns the printable format of the group tree in a
``str``, suitable for further processing. The default format is similar
to the Unix ``tree`` command, and uses unicode box drawing characters.
If these characters prove difficult to process, an alternative format
can be selected. Valid format names are simple and unix.

::

   >>> r.grouptree.format('simple')
    SYS1
    | ADCD
    | BLZCFG
    | BLZGRP
    | BLZWRK
    | CEAGP
    | CFZADMGP
    | CFZSRVGP
    | CFZUSRGP
    | CIMGP
    | IMWEB
    | IYU
    | | IYU0
    | | | IYU000
    | | IYU0RPAN
    | | IYU0RPAW
    | IZUADMIN
    | IZUNUSER
    | IZUSECAD
    | IZUUNGRP
    | IZUUSER
    | VSAMDSET
    | WEBGRP
    | | EMPLOYEE
    | | EXTERNAL
    | ZWEADMIN
    | ZWE100

Status Properties
-----------------

.status
~~~~~~~~~~~

The ``.status`` property returns a dict with the current state of the
class object.

::

   >>> r.status
   {
       'status': current_state, 
       'input-lines': lines_in_irrdbu00_unload, 
       'lines-read': lines_read, 
       'lines-parsed': lines_parsed, 
       'lines-per-second': lines_per_second, 
       'parse-time': total_parse_time
   }

The status field can have the following values:

+--------------------------------+-------------------------------------+
| Status                         | Meaning                             |
+================================+=====================================+
| Initial Object                 | RACF class has been instantiated,   |
|                                | input-lines has a value             |
+--------------------------------+-------------------------------------+
| Error                          | Something went wrong                |
+--------------------------------+-------------------------------------+
| Still parsing your unload      | pyRACF is busy parsing your input,  |
|                                | lines-parsed shows progress         |
+--------------------------------+-------------------------------------+
| Optimizing tables              | Parsing is done, pyRACf is now      |
|                                | creating indexes etc. for faster    |
|                                | lookups                             |
+--------------------------------+-------------------------------------+
| Ready                          | All done, you can start querying.   |
+--------------------------------+-------------------------------------+

.parsed(*table name*)
~~~~~~~~~~~~~~~~~~~~~~~~~

The ``.parsed`` method returns the number of records retrieved from the
RACF input source, for a given table name or prefix. See :ref:`DataFrames`
for valid prefix values.

::

   >>> r.parsed('USBD')
   100

This way you can test if data was collected that would be needed for a
report. Alternatively, you can use the ``.empty`` property of the
DataFrame.

::

   >>> r.users.empty
   False
