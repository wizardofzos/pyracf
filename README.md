# pyracf

## Parsing IRRDBU00 unloads like a boss

    >>> from pyracf import RACF
    >>> mysys = RACF('/path/to/irrdbu00')
    >>> mysys.parse()
    >>> mysys.status
    {'status': 'Still parsing your unload', 'lines-read': 200392, 'lines-parsed': 197269, 'lines-per-second': 63934, 'parse-time': 'n.a.'}
    >>> mysys.status
    {'status': 'Ready', 'lines-read': 7137540, 'lines-parsed': 2248149, 'lines-per-second': 145048, 'parse-time': 49.207921}
    
## Functions 

### parse

Optional argument : thread_count 

This will start one threads (default=1) parsing the unload file as specified at creation time of the instance. Other functions will not be viable before this (background)parsing is done. Current state can be inquired via the .status call.

Example:

    mysys = RACF('/path/to/irrdbu00')
    mysys.parse(thread_count=2)

### status

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

