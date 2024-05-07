Load RACF data
==============

Unload a RACF database
----------------------

In order to work with RACF-unloads you’ll first need an IRRDBU00-unload.
You can create this with the following JCL

::

   //UNLOAD   EXEC PGM=IRRDBU00,PARM=NOLOCKINPUT
   //SYSPRINT   DD SYSOUT=*
   //INDD1    DD   DISP=SHR,DSN=PATH.TO.YOUR.RACFDB
   //OUTDD    DD   DISP=(,CATLG,DELETE),
   //              DSN=SYS1.RACFDB.FLATFILE,
   //              DCB=(RECFM=VB,LRECL=4096),
   //              SPACE=(CYL,(50,150),RLSE)

For more information on IRRDBU00 head on over to the `IBM
Documentation <https://www.ibm.com/docs/en/zos/2.5.0?topic=database-using-racf-unload-utility-irrdbu00>`__.

Once you have your RACF database in IRRDBU00 format, send this over to
the workstation where pyRACF is installed.

.. _Parsing:

Parsing
-------

::

   >>> from pyracf import RACF
   >>> r = RACF(irrdbu00='/path/to/irrdbu00')

At this point in time, pyRACF is aware of your unload file, you can
check this via

::

   >>> r.status
   {'status': 'Initial Object', 'input-lines': 7137540, 'lines-read': 0, 'lines-parsed': 0, 'lines-per-second': 'n.a.', 'parse-time': 'n.a.'}

Once you tell pyRACF to start parsing your unload (via the ``.parse()``
function) you can check the status via the ``.status`` property again
and again, until it’s done.

::

   >>> r.parse()
   >>> r.status
   {'status': 'Still parsing your unload', 'input-lines': 7137540, 'lines-read': 894700, 'lines-parsed': 894696, 'lines-per-second': 599275, 'parse-time': 'n.a.'}
   >>> r.status
   {'status': 'Ready', 'input-lines': 7137540, 'lines-read': 7137540, 'lines-parsed': 7137533, 'lines-per-second': 205447, 'parse-time': 34.741466}

As you can see above, the status will be ``Ready`` once all the records
have been parsed and the Panda DataFrames have been built.

A typical parse-block therefore mostly looks something like this:

::

   >>> from pyracf import RACF
   >>> import time
   >>> r = RACF(irrdbu00='/path/to/irrdbu00')
   >>> r.parse()
   >>> while r.status['status'] != "Ready":
   ...   print('Parsing...')
   ...   time.sleep(10)
   ...
   Parsing...
   Parsing...
   >>> r.status()
   {'status': 'Ready', 'input-lines': 7137540, 'lines-read': 7137540, 'lines-parsed': 7137533, 'lines-per-second': 211951, 'parse-time': 33.6753}

Fancy Parsing
-------------

For a command-line interface the pyRACF module has a
``.parse_fancycli()`` method that will implement the above loop in a
somewhat graphical manner. It will show you all the record types that
are selected for parsing and give you a nice overview at the end.

::

   >>> r = RACF(irrdbu00='/path/to/irrdbu00')
   >>> r.parse_fancycli()
   24-04-07 16:53:28 - parsing pyracf/irrdbu00
   24-04-07 16:53:28 - selected recordtypes: 0100,0101,...
   24-04-07 16:53:55 - progress: ▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉ (100.00%)
   24-04-07 16:54:07 - recordtype 0100 -> 23991 records parsed
   24-04-07 16:54:07 - recordtype 0101 -> 23990 records parsed
   ...
   24-04-07 16:54:07 - total parse time: 38.597577 seconds
