pyRACF background
=================

pyRACF was written for the sole purpose of being able to work with RACF
confugurations from a python runtime.

At its core pyRACF converts every recordtype from an IRRDBU00-unload
into its own Panda DataFrame. These DataFrames can be saved as ‘pickle-files’
in order to work with the same data without having to parse the IRRDBU00-unload again.

Using the python interactive shells, pyRACF allows you to
make queries on your RACF database and explore its structure.

For instance, there’s a function called ``.revoked()`` that will
instantly return a dataframe of user records (recordtype 200,
USBD) containing all the users that have been revoked.
