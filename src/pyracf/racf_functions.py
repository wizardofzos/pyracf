accessKeywords = [' ','NONE','EXECUTE','READ','UPDATE','CONTROL','ALTER','-owner-']

def generic2regex(selection, lenient='%&*'):
    ''' Change a RACF generic pattern into regex to match with text strings in pandas cells.  use lenient="" to match with dsnames/resources '''
    if selection in ('**',''):
        return '.*$'
    else:
        return selection.replace('*.**','`dot``ast`')\
                .replace('.**',r'\`dot``dot``ast`')\
                .replace('*',r'[\w@#$`lenient`]`ast`')\
                .replace('%',r'[\w@#$]')\
                .replace('.',r'\.')\
                .replace('`dot`','.')\
                .replace('`ast`','*')\
                .replace('`lenient`',lenient)\
                +'$'

def accessAllows(level=None):
    ''' return list of access levels that allow the given access, e.g.
    RACF.accessAllows('UPDATE') returns [,'UPDATE','CONTROL','ALTER','-owner-']
    for use in pandas .query("ACCESS in @RACF.accessAllows('UPDATE')")
    '''
    return accessKeywords[accessKeywords.index(level):]

def rankedAccess(args):
    ''' translate access levels into integers, add 10 if permit is for the user ID. 
    could be used in .apply() but would be called for each row, so very very slow '''
    (userid,authid,access) = args
    accessNum = accessKeywords.index(access)
    return accessNum+10 if userid==authid else accessNum
