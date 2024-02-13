import importlib.resources
import json
import pandas as pd 

import math

# No mess with my header lines
import pandas.io.formats.excel
pandas.io.formats.excel.ExcelFormatter.header_style = None

import threading
import time
from datetime import datetime

import xlsxwriter

import os
import glob

import warnings 

class StoopidException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

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

class RACF:
    
    # Our states
    STATE_BAD     = -1
    STATE_INIT    =  0
    STATE_PARSING =  1
    STATE_READY   =  2

    # keep track of names used for a record type
    _recordtype_info = {
    '0100': {'name':'GPBD', 'df':'_groups'},
    '0101': {'name':'GPSGRP', 'df':'_subgroups'},
    '0102': {'name':'GPMEM', 'df':'_connects'},
    '0120': {'name':'GPOMVS', 'df':'_groupOMVS'},
    '0200': {'name':'USBD', 'df':'_users'},
    '0203': {'name':'USGCON', 'df':'_groupConnect'},
    '0204': {'name':'USINSTD', 'df':'_installdata'},
    '0205': {'name':'USCON', 'df':'_connectData'},
    '0209': {'name':'USDMAP', 'df':'_userDistributedMapping'},
    '0220': {'name':'USTSO', 'df':'_userTSO'},
    '0270': {'name':'USOMVS', 'df':'_userOMVS'},
    '0400': {'name':'DSBD', 'df':'_datasets'},
    '0402': {'name':'DSCACC', 'df':'_datasetConditionalAccess'},
    '0404': {'name':'DSACC', 'df':'_datasetAccess'},
    '0500': {'name':'GRBD', 'df':'_generals'},
    '0503': {'name':'GRMEM', 'df':'_generalMembers'},
    '0505': {'name':'GRACC', 'df':'_generalAccess'},
    '0507': {'name':'GRCACC', 'df':'_generalConditionalAccess'}
    }

    _recordname_type = {}    # {'GPBD': '0100', ....}
    _recordname_df = {}      # {'GPBD': '_groups', ....}
    for (rtype,rinfo) in _recordtype_info.items():
        _recordname_type.update({rinfo['name']: rtype})
        _recordname_df.update({rinfo['name']: rinfo['df']})
    
    # load irrdbu00 field definitions, save offsets in _recordtype_info
    # strictly speaking only needed for parse() function, but also not limited to one instance.
    with importlib.resources.open_text("pyracf", "offsets.json") as file:
        _offsets = json.load(file)
    for offset in _offsets:
        rtype = _offsets[offset]['record-type']
        if rtype in _recordtype_info.keys():
          _recordtype_info[rtype].update({"offsets": _offsets[offset]["offsets"]})


    def __init__(self, irrdbu00=None, pickles=None, prefix=''):

        self._state = self.STATE_INIT

        if not irrdbu00 and not pickles:
            self._state = self.STATE_BAD
        else:
            if not pickles:
                self._irrdbu00 = irrdbu00
                self._state    = self.STATE_INIT
                self._unloadlines = sum(1 for _ in open(self._irrdbu00, errors="ignore"))

        if pickles:
            # Read from pickles dir
            picklefiles = glob.glob(f'{pickles}/{prefix}*.pickle')
            self._starttime = datetime.now()
            self._records = {}
            self._unloadlines = 0
            
            for pickle in picklefiles:
                fname = os.path.basename(pickle)
                recordname = fname.replace(prefix,'').split('.')[0]
                if recordname in RACF._recordname_type:
                    recordtype = RACF._recordname_type[recordname]
                    dfname = RACF._recordname_df[recordname]
                    setattr(self, dfname, pd.read_pickle(pickle))
                    recordsRetrieved = len(getattr(self, dfname))
                    self._records[recordtype] = {
                      "seen": recordsRetrieved,
                      "parsed": recordsRetrieved
                    }
                    self._unloadlines += recordsRetrieved
            self._state = self.STATE_READY
            self._stoptime = datetime.now()

        else:
            # Running threads
            self.THREAD_COUNT = 0

            # list of parsed record-types
            self._records = {}

            # list with parsed records, ready to be imported into df
            self._parsed = {}
            for rtype in RACF._recordtype_info:
                self._parsed[rtype] = []

    @property
    def status(self):
        seen = 0
        parsed = 0
        start  = "n.a."
        stop   = "n.a."
        speed  = "n.a."
        parsetime = "n.a."

        for r in self._records:
            seen += self._records[r]['seen']
            parsed += self._records[r]['parsed']

        if self._state == self.STATE_BAD:
            status = "Error"
        elif self._state == self.STATE_INIT:
            status = "Initial Object"
        elif self._state == self.STATE_PARSING:
            status = "Still parsing your unload"
            start  = self._starttime
            speed  = math.floor(seen/((datetime.now() -self._starttime).total_seconds()))
        elif self._state == self.STATE_READY:
            status = "Ready"
            speed  = math.floor(seen/((self._stoptime - self._starttime).total_seconds()))
            parsetime = (self._stoptime - self._starttime).total_seconds()
        else:
            self._state == "Limbo"     
        return {'status': status, 'input-lines': self._unloadlines, 'lines-read': seen, 'lines-parsed': parsed, 'lines-per-second': speed, 'parse-time': parsetime}

    def parse_fancycli(self, recordtypes=_recordtype_info.keys(), save_pickles=False, prefix=''):
        print(f'{datetime.now().strftime("%y-%m-%d %H:%M:%S")} - parsing {self._irrdbu00}')
        self.parse(recordtypes=recordtypes)
        print(f'{datetime.now().strftime("%y-%m-%d %H:%M:%S")} - selected recordtypes: {",".join(recordtypes)}')
        while self._state != self.STATE_READY:
            progress =  math.floor(((sum(r['seen'] for r in self._records.values() if r)) / self._unloadlines) * 63)
            pct = (progress/63) * 100 # not as strange as it seems:)
            done = progress * '▉'
            todo = (63-progress) * ' '
            print(f'{datetime.now().strftime("%y-%m-%d %H:%M:%S")} - progress: {done}{todo} ({pct:.2f}%)'.center(80), end="\r")
            time.sleep(0.5)
        # make completed line always show 100% :)
        print(f'{datetime.now().strftime("%y-%m-%d %H:%M:%S")} - progress: {63*"▉"} ({100:.2f}%)'.center(80))
        for r in recordtypes:
            print(f'{datetime.now().strftime("%y-%m-%d %H:%M:%S")} - recordtype {r} -> {self._records[r]["parsed"]} records parsed')
        print(f'{datetime.now().strftime("%y-%m-%d %H:%M:%S")} - total parse time: {(self._stoptime - self._starttime).total_seconds()} seconds')
        if save_pickles:
            self.save_pickles(path=save_pickles,prefix=prefix)
            print(f'{datetime.now().strftime("%y-%m-%d %H:%M:%S")} - Pickle files saved to {save_pickles}')

    def parse(self, recordtypes=_recordtype_info.keys()):
        pt = threading.Thread(target=self.parse_t,args=(recordtypes,))
        pt.start()
        return True

    def parse_t(self, thingswewant=_recordtype_info.keys()):
        # TODO: make this multiple threads (per record-type?)
        if self.THREAD_COUNT == 0:
            self._starttime = datetime.now()
            self._state = self.STATE_PARSING
        self.THREAD_COUNT += 1
        # TODO: Complete all record-types. Fix offsets.json !
        with open(self._irrdbu00, 'r', encoding="utf-8", errors="replace") as infile:
            for line in infile:
                r = line[:4]
                if r in self._records:
                    self._records[r]['seen'] += 1
                else:
                    self._records[r] = {'seen': 1, 'parsed': 0}
                if r in thingswewant:
                    offsets = RACF._recordtype_info[r]["offsets"]
                    if offsets:
                        irrmodel = {}
                        for model in offsets:
                            start = int(model['start'])
                            end   = int(model['end'])
                            name  = model['field-name']
                            value = line[start-1:end].strip()
                            irrmodel[name] = str(value) 
                        self._parsed[r].append(irrmodel)
                        self._records[r]['parsed'] += 1
        # all models parsed :)

        for (rtype,rinfo) in RACF._recordtype_info.items():
            if rtype in thingswewant:
                setattr(self, rinfo['df'], pd.DataFrame.from_dict(self._parsed[rtype]))

        self.THREAD_COUNT -= 1
        if self.THREAD_COUNT == 0:
            self._state = self.STATE_READY         
            self._stoptime = datetime.now()
        return True

    def parsed(self, rname):
        """ how many records with this name (type) were parsed """
        return self._records[RACF._recordname_type[rname]]['parsed']
        
    def save_pickle(self, df='', dfname='', path='', prefix=''):
        # Sanity check
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        
        df.to_pickle(f'{path}/{prefix}{dfname}.pickle')


    def save_pickles(self, path='/tmp', prefix=''):
        # Sanity check
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        # Is Path there ?
        if not os.path.exists(path):
            madedir = os.system(f'mkdir -p {path}')
            if madedir != 0:
                raise StoopidException(f'{path} does not exist, and cannot create')
        # Let's save the pickles
        for (rtype,rinfo) in RACF._recordtype_info.items():
            if rtype in self._records and self._records[rtype]['parsed']>0:
                self.save_pickle(df=getattr(self, rinfo['df']), dfname=rinfo['name'], path=path, prefix=prefix)
            else:
                # todo: ensure consistent data, delete old pickles that were not saved
                pass

    @property
    def users(self):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        try:
            return self._users
        except:
            raise StoopidException('No USBD records parsed!')
        
    
    def user(self, userid=None):
        if not userid:
            raise StoopidException('userid not specified...')
        return self._users.loc[self._users.USBD_NAME==userid]


    @property
    def connectData(self):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._connectData

    @property
    def userDistributedMapping(self):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._userDistributedMapping


    @property
    def specials(self):
        return self._users.loc[self._users['USBD_SPECIAL'] == 'YES']

    @property
    def operations(self):
        return self._users.loc[self._users['USBD_OPER'] == 'YES']

    @property
    def auditors(self):
        return self._users.loc[self._users['USBD_AUDITOR'] == 'YES']

    @property
    def revoked(self):
        return self._users.loc[self._users['USBD_REVOKE'] == 'YES']

    @property
    def groups(self, query=None):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._groups
    
    def group(self, group=None):
        if not group:
            raise StoopidException('group not specified...')
        return self._groups.loc[self._groups.GPBD_NAME==group]

    @property
    def groupConnect(self):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._groupConnect

    @property
    def installdata(self):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._installdata

    @property
    def datasets(self):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._datasets

    @property
    def datasetConditionalAccess(self):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._datasetConditionalAccess

    @property
    def connects(self):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._connects

    @property
    def subgroups(self):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._subgroups

    @property
    def datasetAccess(self):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._datasetAccess

    @property
    def uacc_read_datasets(self):
        return self._datasets.loc[self._datasets.DSBD_UACC=="READ"]

    @property
    def generals(self, query=None):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._generals

    generics = property(deprecated(generals,"generics"))

    @property
    def generalMembers(self, query=None):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._generalMembers    

    genericMembers = property(deprecated(generalMembers,"genericMembers"))

    @property
    def generalAccess(self, query=None):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._generalAccess

    genericAccess = property(deprecated(generalAccess,"genericAccess"))
    
    @property
    def generalConditionalAccess(self):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._generalConditionalAccess

    genericConditionalAccess = property(deprecated(generalConditionalAccess,"genericConditionalAccess"))
    
    @property
    def userOMVS(self, query=None):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._userOMVS

    @property
    def groupOMVS(self, query=None):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._groupOMVS        

    @property
    def userTSO(self, query=None):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._userTSO    
        
    @property
    def orphans(self):
        
        if self.parsed("DSACC") + self.parsed("GRACC") == 0:
            raise StoopidException('No dataset/general access records parsed! (PEBKAM/ID-10T error)')
            
        datasetOrphans = None
        generalOrphans = None

        if self.parsed("DSACC") > 0:
            self._datasetAccess = self._datasetAccess.assign(inGroups=self._datasetAccess.DSACC_AUTH_ID.isin(self._groups.GPBD_NAME))
            self._datasetAccess = self._datasetAccess.assign(inUsers=self._datasetAccess.DSACC_AUTH_ID.isin(self._users.USBD_NAME))
            datasetOrphans = self._datasetAccess.loc[(self._datasetAccess['inGroups'] == False) & (self._datasetAccess['inUsers'] == False) & (self._datasetAccess['DSACC_AUTH_ID'] != "*") & (self._datasetAccess['DSACC_AUTH_ID'] != "&RACUID")]
        
        if self.parsed("GRACC") > 0:
                self._generalAccess = self._generalAccess.assign(inGroups=self._generalAccess.GRACC_AUTH_ID.isin(self._groups.GPBD_NAME))
                self._generalAccess = self._generalAccess.assign(inUsers=self._generalAccess.GRACC_AUTH_ID.isin(self._users.USBD_NAME))
                generalOrphans =  self._generalAccess.loc[(self._generalAccess['inGroups'] == False) & (self._generalAccess['inUsers'] == False) & (self._generalAccess['GRACC_AUTH_ID'] != "*") & (self._generalAccess['GRACC_AUTH_ID'] != "&RACUID")]

        return datasetOrphans, generalOrphans

    def xls(self,fileName='irrdbu00.xlsx'):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')

        if self.parsed("DSACC") + self.parsed("GRACC") == 0:
            raise StoopidException('No dataset/general access records parsed! (PEBKAM/ID-10T error)')

        writer = pd.ExcelWriter(f'{fileName}', engine='xlsxwriter')
        accessLevelFormats = {
                    'N': writer.book.add_format({'bg_color': 'silver'}),
                    'E': writer.book.add_format({'bg_color': 'purple'}),
                    'R': writer.book.add_format({'bg_color': 'yellow'}),
                    'U': writer.book.add_format({'bg_color': 'orange'}),
                    'C': writer.book.add_format({'bg_color': 'red'}),
                    'A': writer.book.add_format({'bg_color': 'red'}),
                    'D': writer.book.add_format({'bg_color': 'cyan'}), 
                    'T': writer.book.add_format({'bg_color': 'orange'}),
                }

        accessLevels = {
                    'NONE': 'N',
                    'EXECUTE': 'E',
                    'READ': 'R',
                    'UPDATE': 'U',
                    'CONTROL': 'C',
                    'ALTER': 'A',
                    'NOTRUST': 'D',
                    'TRUST': 'T'
                }

        format_br = writer.book.add_format({})
        format_br.set_rotation(90)
        format_nr = writer.book.add_format({})
        format_center = writer.book.add_format({})
        format_center.set_align('center')
        format_center.set_align('vcenter')

        ss = datetime.now()

        classes = self.generalAccess.groupby(['GRACC_CLASS_NAME'])
        for c in classes.groups:
            s = datetime.now()
            authIDsInClass = list(self.generalAccess.loc[self.generalAccess.GRACC_CLASS_NAME==c]['GRACC_AUTH_ID'].unique())
            profilesInClass = list(self.generalAccess.loc[self.generalAccess.GRACC_CLASS_NAME==c]['GRACC_NAME'].unique())
            longestProfile = 0
            for p in profilesInClass:
                if len(p) > longestProfile:
                    longestProfile = len(p)
            newdata = {}
            newdata['Profiles'] = []
            for id in authIDsInClass:
                newdata[id] = [None] * len(profilesInClass)
            classdata = classes.get_group(c)
            profiles = classdata.groupby(['GRACC_NAME'])
            for i,p in enumerate(profiles.groups):
                profiledata = profiles.get_group(p)
                newdata['Profiles'].append(p)
                users = profiledata.groupby(['GRACC_AUTH_ID'])
                for u in users.groups:
                    useraccess = users.get_group(u)['GRACC_ACCESS'].values[0]
                    newdata[u][i] = accessLevels[useraccess]
            df1 = pd.DataFrame(newdata)
            df1.to_excel(writer, sheet_name=c, index=False)
            worksheet = writer.sheets[c]
            worksheet.set_row(0, 64, format_br)
            worksheet.set_column(1, len(authIDsInClass)+1, 2, format_center )
            worksheet.set_column(0, 0, longestProfile + 2 )
            worksheet.write(0, 0, 'Profile', format_nr)

            shared_strings = sorted(worksheet.str_table.string_table, key=worksheet.str_table.string_table.get)
            for i in range(len(authIDsInClass)+1):
                for j in range(len(profilesInClass)+1):
                    if i>0 and j>0:
                        rdict = worksheet.table.get(j,None)
                        centry = rdict.get(i,None)
                        if centry:
                            value = shared_strings[centry.string]
                            worksheet.write(j, i, value, accessLevelFormats[value])

        if self.parsed("DSBD") > 0:
            ss = datetime.now()
            profilesInClass = list(self.datasetAccess['DSACC_NAME'].unique())
            authIDsInClass = list(self.datasetAccess['DSACC_AUTH_ID'].unique())
            authids = 0
            longestProfile = 0
            for p in profilesInClass:
                if len(p) > longestProfile:
                    longestProfile = len(p)
            newdata = {}
            newdata['Profiles'] = []
            for id in authIDsInClass:
                    newdata[id] = [None] * len(profilesInClass)
            profiles = self.datasetAccess.groupby(['DSACC_NAME'])
            for i,p in enumerate(profiles.groups):
                profiledata = profiles.get_group(p)
                newdata['Profiles'].append(p)
                users = profiledata.groupby(['DSACC_AUTH_ID'])
                for u in users.groups:
                    useraccess = users.get_group(u)['DSACC_ACCESS'].values[0]
                    newdata[u][i] = accessLevels[useraccess]

            df1 = pd.DataFrame(newdata)
            df1.to_excel(writer, sheet_name='DATASET', index=False)
            worksheet = writer.sheets['DATASET']
            worksheet.set_row(0, 64, format_br)
            worksheet.set_column(1, len(authIDsInClass)+1, 2, format_center )
            worksheet.set_column(0, 0, longestProfile + 2 )
            worksheet.write(0, 0, 'Profile', format_nr)

            shared_strings = sorted(worksheet.str_table.string_table, key=worksheet.str_table.string_table.get)
            for i in range(len(authIDsInClass)+1):
                for j in range(len(profilesInClass)+1):
                    if i>0 and j>0:
                        rdict = worksheet.table.get(j,None)
                        centry = rdict.get(i,None)
                        if centry:
                            value = shared_strings[centry.string]
                            worksheet.write(j, i, value, accessLevelFormats[value])

        writer.close()   

    def ownertree(self):
        if self._ownertree != None:
            return self._ownertree
        else:
            # get all owners... (group or user)
            self._ownertree = {}
            owners = self.groups.groupby('GPBD_OWNER_ID')
            for owner in owners.groups.keys():
                if owner not in self._ownertree:
                    self._ownertree[owner] = []
                    for group in owners.get_group(owner)['GPBD_NAME'].values:
                        self._ownertree[owner].append(group)
            # now we gotta condense it :)
            return self._ownertree
            for supgrp in self._ownertree:
                for subgrp in self._ownertree[supgrp]:
                    if subgrp in self._ownertree.values:
                        self._ownertree[supgrp].remove(subgrp)
                        self._ownertree[supgrp].append(self._ownertree[subgrp])
            return self._ownertree

    def getdatsetrisk(self, profile=''):
        '''This will produce a dict as follows:
      
        '''
        try:
            if self.parsed("GPBD") == 0 or self.parsed("USCON") == 0 or self.parsed("USBD") == 0 or self.parsed("DSACC") == 0 or self.parsed("DSBD") == 0:
                raise StoopidException("Need to parse DSACC and DSBD first...")
        except:
            raise StoopidException("Need to parse DSACC, USCON, USBD, GPBD and DSBD first...")
        
        d = self.datasets.loc[self.datasets.DSBD_NAME==profile]
        if len(d) == 0:
            raise Exception('Profile not here...')
        
        owner = d['DSBD_OWNER_ID'].values[0]
        accesslist = {}
        accessmanagers = {}
        dsacc = self.datasetAccess.groupby('DSACC_NAME')
        peraccess = dsacc.get_group(profile).groupby('DSACC_ACCESS')
        for access in ['NONE','EXECUTE','READ','UPDATE','CONTROL','ALTER']:
            accesslist[access] = []
            accessmanagers[access] = []
            if access in peraccess.groups.keys():
                a = peraccess.get_group(access)['DSACC_AUTH_ID'].values
                for id in a:
                    if len(self.user(id)) == 1:
                        accesslist[access].append(id)
                    else:
                        if len(self.group(id)) == 1:
                            g = self.connectData.loc[self.connectData.USCON_GRP_ID==id]
                            for user,grp_special in g[['USCON_NAME','USCON_GRP_SPECIAL']].values:
                                accesslist[access].append(user)
                                # But suppose this user is group_special here?
                                if grp_special=='YES':
                                    accessmanagers[access].append(user)
                            # And wait a minute... this groups owner, can also add people to the group?
                            gowner = self.group(id)['GPBD_OWNER_ID'].values[0]
                            if len(self.user(gowner)) == 1:
                                accessmanagers[access].append(gowner)
                            else:
                                gg = self.connectData.loc[self.connectData.USCON_GRP_ID==gowner]
                                for user,grp_special in gg[['USCON_NAME','USCON_GRP_SPECIAL']].values:
                                    if grp_special=='YES':
                                        accessmanagers[access].append(user)
                # clean up doubles...
            accessmanagers[access] = list(set(accessmanagers[access]))
            accesslist[access] = list(set(accesslist[access]))

        y = {
            'owner': owner,
            'accessmanagers': accessmanagers,
            'uacc': d['DSBD_UACC'].values[0],
            'permits': accesslist
        }

        return y

class IRRDBU(RACF):
    pass

