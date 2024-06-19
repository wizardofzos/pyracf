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
    ''' print entries from a dict index into a readable list, e.g., a, b or c '''
    return list(iter)[0] if len(iter)==1 else ' or '.join([', '.join(list(iter)[0:-1]),list(iter)[-1]])

def simpleListed(item):
    ''' print a string or a list of strings with just commas between values '''
    return item if type(item)==str else ','.join(item)

def nameInColumns(df,name,columns=[],prefix=None,returnAll=False):
    '''find prefixed column name in a Frame, return whole name, or all names if requested

    args:
        df: Frame to find column names, or None
        name (str, list): name to search for, with prefix or without, or list of names
        columns (list): opt. ignore df parameter, caller has already extracted column names
        prefix (str, list): opt. verify that column name has the given prefix(es)
        returnAll (bool): always return all matches in a list

    returns:
        fully prefixed column name, or list of column names
    '''
    if len(columns)==0:
        columns = df.columns

    if type(name)==str:
        if name in columns:
            found = [name]
        else:
            found = [cname for cname in columns if cname.split('_',1)[1]==name]
    elif type(name)==list:
        returnAll = True  # if a list of names is given, return a list
        found = [cname for cname in columns if cname in name or cname.split('_',1)[1] in name]

    if prefix:
        if type(prefix)==str:
            found = [cname for cname in found if cname.split('_',1)[0] == prefix]
        else:
            found = [cname for cname in found if cname.split('_',1)[0] in prefix]
    
    if returnAll:
        return found
    elif len(found)==1:
        return found[0]
    else:
        raise ValueError(f"field {name} matches {len(found)} column names: {simpleListed(found)}")

