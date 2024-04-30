import warnings 

def deprecated(func,oldname):
    ''' Wrapper routine to add (deprecated) alias name to new routine (func), supports methods and properties. 
        Inspired by functools.partial() '''
    def deprecated_func(*arg,**keywords):
        if hasattr(func,"__name__"):  # normal function object
            newroutine = func
        else:  # property object
            newroutine = func.fget
        warnings.warn(f"{oldname} is deprecated and will be removed, use {newroutine.__name__} instead.")
        return newroutine(*arg,**keywords)
    deprecated_func.func = func
    return deprecated_func

def listMe(item):
    ''' make list in parameters optional when there is only 1 item, similar to the * unpacking feature in assignments.
    as a result you can just: for options in listMe(optioORoptions)  '''
    return item if type(item)==list else [item]

def readableList(iter):
    '''' print entries from a dict index into a readable list, e.g., a, b or c '''
    return list(iter)[0] if len(iter)==1 else ' or '.join([', '.join(list(iter)[0:-1]),list(iter)[-1]])

def simpleListed(item):
    ''' print a string or a list of strings with just commas between values '''
    return item if type(item)==str else ','.join(item)


