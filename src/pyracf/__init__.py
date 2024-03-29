import importlib.resources
import json
import yaml
import math
import pandas as pd 

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

    # keep track of names used for a record type, "index" must be a list of field names
    _recordtype_info = {
    '0100': {'name':'GPBD', 'df':'_groups'},
    '0101': {'name':'GPSGRP', 'df':'_subgroups'},
    '0102': {'name':'GPMEM', 'df':'_connects', "index":["GPMEM_NAME","GPMEM_MEMBER_ID"]},
    '0103': {'name':'GPINSTD', 'df':'_groupUSRDATA'},
    '0110': {'name':'GPDFP', 'df':'_groupDFP'},
    '0120': {'name':'GPOMVS', 'df':'_groupOMVS'},
    '0130': {'name':'GPOVM', 'df':'_groupOVM'},
    '0141': {'name':'GPTME', 'df':'_groupTME'},
    '0151': {'name':'GPCSD', 'df':'_groupCSDATA'},
    '0200': {'name':'USBD', 'df':'_users'},
    '0201': {'name':'USCAT', 'df':'_userCategories'},
    '0202': {'name':'USCLA', 'df':'_userClasses'},
    '0203': {'name':'USGCON', 'df':'_groupConnect', "index":["USGCON_GRP_ID","USGCON_NAME"]},
    '0204': {'name':'USINSTD', 'df':'_userUSRDATA'},
    '0205': {'name':'USCON', 'df':'_connectData', "index":["USCON_GRP_ID","USCON_NAME"]},
    '0206': {'name':'USRSF', 'df':'_userRRSFdata'},
    '0207': {'name':'USCERT', 'df':'_userCERTname'},
    '0208': {'name':'USNMAP', 'df':'_userAssociationMappings'},
    '0209': {'name':'USDMAP', 'df':'_userDistributedMapping'},
    '020A': {'name':'USMFA', 'df':'_userMFAfactor'},
    '020B': {'name':'USMPOL', 'df':'_userMFApolicies'},
    '0210': {'name':'USDFP', 'df':'_userDFP'},
    '0220': {'name':'USTSO', 'df':'_userTSO'},
    '0230': {'name':'USCICS', 'df':'_userCICS'},
    '0231': {'name':'USCOPC', 'df':'_userCICSoperatorClasses'},
    '0232': {'name':'USCRSL', 'df':'_userCICSrslKeys'},
    '0233': {'name':'USCTSL', 'df':'_userCICStslKeys'},
    '0240': {'name':'USLAN', 'df':'_userLANGUAGE'},
    '0250': {'name':'USOPR', 'df':'_userOPERPARM'},
    '0251': {'name':'USOPRP', 'df':'_userOPERPARMscope'},
    '0260': {'name':'USWRK', 'df':'_userWORKATTR'},
    '0270': {'name':'USOMVS', 'df':'_userOMVS'},
    '0280': {'name':'USNETV', 'df':'_userNETVIEW'},
    '0281': {'name':'USNOPC', 'df':'_userNETVIEWopclass'},
    '0282': {'name':'USNDOM', 'df':'_userNETVIEWdomains'},
    '0290': {'name':'USDCE', 'df':'_userDCE'},
    '02A0': {'name':'USOVM', 'df':'_userOVM'},
    '02B0': {'name':'USLNOT', 'df':'_userLNOTES'},
    '02C0': {'name':'USNDS', 'df':'_userNDS'},
    '02D0': {'name':'USKERB', 'df':'_userKERB'},
    '02E0': {'name':'USPROXY', 'df':'_userPROXY'},
    '02F0': {'name':'USEIM', 'df':'_userEIM'},
    '02G1': {'name':'USCSD', 'df':'_userCSDATA'},
    '1210': {'name':'USMFAC', 'df':'_user-MFAfactorTags'},
    '0400': {'name':'DSBD', 'df':'_datasets'},
    '0401': {'name':'DSCAT', 'df':'_datasetCategories'},
    '0402': {'name':'DSCACC', 'df':'_datasetConditionalAccess', "index":["DSCACC_NAME","DSCACC_AUTH_ID","DSCACC_ACCESS"]},
    '0403': {'name':'DSVOL', 'df':'_datasetVolumes'},
    '0404': {'name':'DSACC', 'df':'_datasetAccess', "index":["DSACC_NAME","DSACC_AUTH_ID","DSACC_ACCESS"]},
    '0405': {'name':'DSINSTD', 'df':'_datasetUSRDATA'},
    '0406': {'name':'DSMEM', 'df':'_datasetMember'},
    '0410': {'name':'DSDFP', 'df':'_datasetDFP'},
    '0421': {'name':'DSTME', 'df':'_datasetTME'},
    '0431': {'name':'DSCSD', 'df':'_datasetCSDATA'},
    '0500': {'name':'GRBD', 'df':'_generals'},
    '0501': {'name':'GRTVOL', 'df':'_generalTAPEvolume'},
    '0502': {'name':'GRCAT', 'df':'_generalCategories'},
    '0503': {'name':'GRMEM', 'df':'_generalMembers'},
    '0504': {'name':'GRVOL', 'df':'_generalVolumes'},
    '0505': {'name':'GRACC', 'df':'_generalAccess', "index":["GRACC_CLASS_NAME","GRACC_NAME","GRACC_AUTH_ID","GRACC_ACCESS"]},
    '0506': {'name':'GRINSTD', 'df':'_generalUSRDATA'},
    '0507': {'name':'GRCACC', 'df':'_generalConditionalAccess', "index":["GRCACC_CLASS_NAME","GRCACC_NAME","GRCACC_AUTH_ID","GRCACC_ACCESS"]},
    '0508': {'name':'GRFLTR', 'df':'_generalFILTER'},
    '0509': {'name':'GRDMAP', 'df':'_generalDistributedMapping'},
    '0510': {'name':'GRSES', 'df':'_generalSESSION'},
    '0511': {'name':'GRSESE', 'df':'_generalSESSIONentities'},
    '0520': {'name':'GRDLF', 'df':'_generalDLF'},
    '0521': {'name':'GRDLFJ', 'df':'_generalDLFjob-names'},
    '0530': {'name':'GRSIGN', 'df':'_generalSSIGNON'},
    '0540': {'name':'GRST', 'df':'_generalSTARTED'},
    '0550': {'name':'GRSV', 'df':'_generalSYSTEMVIEW'},
    '0560': {'name':'GRCERT', 'df':'_generalCERT'},
    '0561': {'name':'CERTR', 'df':'_generalCERTreferences'},
    '0562': {'name':'KEYR', 'df':'_general-KEYRING'},
    '0570': {'name':'GRTME', 'df':'_generalTME'},
    '0571': {'name':'GRTMEC', 'df':'_generalTMEchild'},
    '0572': {'name':'GRTMER', 'df':'_generalTMEresource'},
    '0573': {'name':'GRTMEG', 'df':'_generalTMEgroup'},
    '0574': {'name':'GRTMEE', 'df':'_generalTMErole'},
    '0580': {'name':'GRKERB', 'df':'_generalKERB'},
    '0590': {'name':'GRPROXY', 'df':'_generalPROXY'},
    '05A0': {'name':'GREIM', 'df':'_generalEIM'},
    '05B0': {'name':'GRALIAS', 'df':'_generalALIAS'},
    '05C0': {'name':'GRCDT', 'df':'_generalCDTINFO'},
    '05D0': {'name':'GRICTX', 'df':'_generalICTX'},
    '05E0': {'name':'GRCFDEF', 'df':'_generalCFDEF', "index":["GRCFDEF_CLASS","GRCFDEF_NAME"]},
    '05F0': {'name':'GRSIG', 'df':'_generalSIGVER'},
    '05G0': {'name':'GRCSF', 'df':'_generalICSF'},
    '05G1': {'name':'GRCSFK', 'df':'_generalICSFkeylabel'},
    '05G2': {'name':'GRCSFC', 'df':'_generalICSFcertificateIdentifier'},
    '05H0': {'name':'GRMFA', 'df':'_generalMFAfactor'},
    '05I0': {'name':'GRMFP', 'df':'_generalMFApolicy'},
    '05I1': {'name':'GRMPF', 'df':'_generalMFApolicyFactors'},
    '05J1': {'name':'GRCSD', 'df':'_generalCSDATA'},
    '05K0': {'name':'GRIDTP', 'df':'_generalIDTFPARMS'},
    '05L0': {'name':'GRJES', 'df':'_generalJESDATA'},
    '1560': {'name':'CERTN', 'df':'_generalCERTNAME'}
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

    _grouptree          = None  # dict with lists
    _ownertree          = None  # dict with lists
    _grouptreeLines     = None  # df with all supgroups up to SYS1
    _ownertreeLines     = None  # df with owners up to SYS1 or user ID
    
    accessKeywords = ['NONE','EXECUTE','READ','UPDATE','CONTROL','ALTER','-owner-']
    
    def accessAllows(level=None):
        ''' return list of access levels that allow the given access, e.g.
        RACF.accessAllows('UPDATE') returns [,'UPDATE','CONTROL','ALTER','-owner-']
        for use in pandas .query("ACCESS in @RACF.accessAllows('UPDATE')")
        '''
        return RACF.accessKeywords[RACF.accessKeywords.index(level):]

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
            status = "Limbo"     
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
            print(f'{datetime.now().strftime("%y-%m-%d %H:%M:%S")} - recordtype {r} -> {self.parsed(self._recordtype_info[r]["name"])} records parsed')
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

        # TODO: Reduce memory use, delete self._parsed after dataframes are made

        self.THREAD_COUNT -= 1
        if self.THREAD_COUNT == 0:
            self._state = self.STATE_READY         
            self._stoptime = datetime.now()
        return True

    def parsed(self, rname):
        """ how many records with this name (type) were parsed """
        rtype = RACF._recordname_type[rname]
        return self._records[rtype]['parsed'] if rtype in self._records else 0
        
    def correlate(self, thingswewant=_recordtype_info.keys()):
        """ construct tables that combine the raw dataframes for improved processing """
        
        # activate acl() method on our dataframes, so it get called with our instance's variables, the frame, and all optional parms
        # e.g. msys._datasetAccess.loc[['SYS1.**']].acl(permits=True, explode=False, resolve=False, admin=False, sort="user")
        pd.core.base.PandasObject.acl = lambda *x,**y: RACF.acl(self,*x,**y)
        pd.core.base.PandasObject.ACL = lambda *x,**y: RACF.acl(self,*x,**y)

        # generic and regex filter on the index levels of a frame
        pd.core.base.PandasObject.FILTER = RACF.gfilter
        pd.core.base.PandasObject.MATCH = RACF.rfilter
        pd.core.base.PandasObject.gfilter = RACF.gfilter
        pd.core.base.PandasObject.rfilter = RACF.rfilter


        # set consistent index columns for existing dfs: profile key, connect group+user, of profile class+key (for G.R.)
        for (rtype,rinfo) in RACF._recordtype_info.items():
            if rtype in thingswewant and rtype in self._records and self._records[rtype]['parsed']>0:
                if "index" in rinfo:
                    keys = rinfo["index"]
                    names = [keys[i].replace(rinfo["name"]+"_","_") for i in range(len(keys))]
                elif rtype[1]=="5":  # general resources
                    keys = [rinfo["name"]+"_CLASS_NAME",rinfo["name"]+"_NAME"]
                    names = ["_CLASS_NAME","_NAME"]
                else:
                    keys = rinfo["name"]+"_NAME"
                    names = "_NAME"
                getattr(self,rinfo['df']).set_index(keys,drop=False,inplace=True)
                getattr(self,rinfo['df']).rename_axis(names,inplace=True)  # prevent ambiguous index / column names 
        
        # copy group auth (USE,CREATE,CONNECT,JOIN) to complete the connectData list, using index alignment
        if self.parsed("GPMEM") == 0 or self.parsed("USCON") == 0:
            raise StoopidException("Need to parse GPMEM and USCON first...")
        else: 
            self.connectData["GPMEM_AUTH"]=self.connects["GPMEM_AUTH"]
        
        self._connectByUser = self._connectData.set_index("USCON_NAME",drop=False).rename_axis('NAME')
        self._connectByGroup = self._connectData.set_index("USCON_GRP_ID",drop=False).rename_axis('GRP_ID')
            
        # dicts containing lists of groups for printing group structure
        self._ownertree = self.ownertree()
        self._grouptree = self.grouptree()

        # self._grouptreeLines: frame of group + name of all superior groups until SYS1
        gtl = self._groups[['GPBD_NAME','GPBD_SUPGRP_ID']]
        gtlLen = 0
        while len(gtl)>gtlLen:
            nextup = gtl[gtlLen:]\
                     .query("GPBD_NAME!='SYS1' & GPBD_SUPGRP_ID!='SYS1'")\
                     .join(self._groups[['GPBD_SUPGRP_ID']],on='GPBD_SUPGRP_ID',lsuffix='_ME')\
                     .drop(['GPBD_SUPGRP_ID_ME'],axis=1,inplace=True)
            gtlLen = len(gtl)
            gtl=pd.concat([gtl,nextup],ignore_index=True,sort=False)
        self._grouptreeLines = gtl.rename(columns={'GPBD_NAME':'GROUP','GPBD_SUPGRP_ID':'PARENTS'})\
                                  .set_index("GROUP",drop=False)\
                                  .rename_axis('GROUP_NAME')
        
        # self._ownertreeLines: frame of group + name of all owners (group or user) until SYS1 or user ID found
        otl=self._groups[['GPBD_NAME','GPBD_SUPGRP_ID','GPBD_OWNER_ID']]
        otlLen = 0
        while len(otl)>otlLen:
            nextup = otl[otlLen:]\
                     .query("GPBD_SUPGRP_ID==GPBD_OWNER_ID & GPBD_SUPGRP_ID!='SYS1'")\
                     .join(self._groups[['GPBD_SUPGRP_ID','GPBD_OWNER_ID']],on='GPBD_SUPGRP_ID',lsuffix='_ME')\
                     .drop(['GPBD_SUPGRP_ID_ME','GPBD_OWNER_ID_ME'],axis=1)
            otlLen = len(otl)
            otl=pd.concat([otl,nextup],ignore_index=True,sort=False)
        self._ownertreeLines = otl.drop('GPBD_SUPGRP_ID',axis=1)\
                                  .rename(columns={'GPBD_NAME':'GROUP','GPBD_OWNER_ID':'OWNER_IDS'})\
                                  .set_index("GROUP",drop=False)\
                                  .rename_axis('GROUP_NAME')

        
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
                # TODO: ensure consistent data, delete old pickles that were not saved
                pass


    def generic2regex(selection, lenient='%&*'):
        ''' Change a RACF generic pattern into regex to match with text strings in pandas cells.  use lenient="" to match with dsnames/resources '''
        if selection in ('**',''):
            return '.*$'
        else:
            return selection.replace('*.**','`dot``ast`')\
                    .replace('.**','\`dot``dot``ast`')\
                    .replace('*','[\w@#$`lenient`]`ast`')\
                    .replace('%','[\w@#$]')\
                    .replace('.','\.')\
                    .replace('`dot`','.')\
                    .replace('`ast`','*')\
                    .replace('`lenient`',lenient)\
                    +'$'


    def giveMeProfiles(self, df, selection=None, option=None):
        ''' Search profiles using the index fields.  selection can be str or tuple.  Tuples check for group + user id in connects, or class + profile key in generals.
        option controls how selection is interpreted, and how data must be returned:
        None is for (expensive) backward compatibility, returns a df with 1 profile.
        LIST returns a series for 1 profile, much faster and easier to process.
        REGEX returns a df for profile matching selection, starting at beginning of profile name, (general) class, or class+profile, (connect) group, or group+user ID.
        GENERIC takes the generic pattern for the selection, turns it into regex, and returns a df.
        '''
        if not selection:
            raise StoopidException('profile criteria not specified...')
        if option in (None,'LIST','L'):  # return 1 profile
            # 1 string, several strings in a tuple, or a mix of strings and None, but the latter must be tested with get_level_values
            if type(selection)==str: pass
            elif type(selection)==tuple:
                selections = len(selection)
                strings = [type(selection[i])==str for i in range(selections)]
                if all(strings): pass
                else:
                    found = False
                    for i in range(selections):
                        if all(strings[0:i]) and not any(strings[i+1:]):
                            if i==0:
                                selection = selection[0]
                            else:    
                                selection = tuple(selection[j] for j in range(i+1))
                            found = True
                            break
                    if not found:
                        locs = True
                        for s in range(selections):
                            if selection[s] not in (None,'**'):
                                locs &= (df.index.get_level_values(s)==selection[s])
                        selection = locs
            else:
                raise StoopidException(f'specify patterns for profile, (group,userid) or (class,profile), not {selection}')
            if option == None:  # return DataFrame for 1 profile
                try:
                    return df.loc[[selection]]
                except KeyError:
                    return pd.DataFrame()
            elif option in ('LIST','L'):  # return Series for 1 profile
                try:
                    return df.loc[selection]
                except KeyError:
                    return []
        elif option in ('REGEX','R','GENERIC','GEN','G'):
            if type(selection)==str:
                return df.loc[df.index.get_level_values(0).str.match(selection if option in ('REGEX','R') else RACF.generic2regex(selection))]
            elif type(selection)==tuple:
                locs = True
                for s in range(len(selection)):
                    if selection[s] not in (None,'**'):
                        locs &= (df.index.get_level_values(s).str.match(selection[s] if option in ('REGEX','R') else RACF.generic2regex(selection[s])))
                return df.loc[locs]
            else:
                raise StoopidException(f'specify patterns for profile, (group,userid) or (class,profile), not {selection}')
        else:
            raise StoopidException(f'unexpected last parameter {option}')

    def gfilter(df, *selection):
        ''' Search profiles using GENERIC pattern on the index fields.  selection can be one or more values, corresponding to index levels of the df '''
        locs = True
        for s in range(len(selection)):
            if selection[s] not in (None,'**'):
                locs &= (df.index.get_level_values(s).str.match(RACF.generic2regex(selection[s])))
        return df.loc[locs]

    def rfilter(df, *selection):
        ''' Search profiles using refex on the index fields.  selection can be one or more values, corresponding to index levels of the df '''
        locs = True
        for s in range(len(selection)):
            if selection[s] not in (None,'**','.*'):
                locs &= (df.index.get_level_values(s).str.match(selection[s]))
        return df.loc[locs]




    @property
    def users(self):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        try:
            return self._users
        except:
            raise StoopidException('No USBD records parsed!')
    
    def user(self, userid=None, pattern=None):
        return self.giveMeProfiles(self._users, userid, pattern)

    def OLDuser(self, userid=None):
        if not userid:
            raise StoopidException('userid not specified...')
        try:
            return self._users.loc[[userid]]
        except:
            return []
        # return self._users.loc[self._users.USBD_NAME==userid]


    @property
    def connectData(self):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._connectData
        
    def connect(self, group=None, userid=None, pattern=None):
        return self.giveMeProfiles(self._connectData, (group,userid), pattern)


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
    
    def group(self, group=None, pattern=None):
        return self.giveMeProfiles(self._groups, group, pattern)

    def OLDgroup(self, group=None):
        if not group:
            raise StoopidException('group not specified...')
        try:
            return self._groups.loc[[group]]
        except:
            return []
        # return self._groups.loc[self._groups.GPBD_NAME==group]

    @property
    def groupsWithoutUsers(self):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._groups.loc[-self.groups.GPBD_NAME.isin(self._connectData.USCON_GRP_ID)]
    
    @property
    def groupConnect(self):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._groupConnect

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
    def installdata(self):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._userUSRDATA

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
    def datasets(self):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._datasets

    def dataset(self, profile=None, pattern=None):
        return self.giveMeProfiles(self._datasets, profile, pattern)

    @property
    def datasetConditionalAccess(self):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._datasetConditionalAccess

    def datasetConditionalPermit(self, profile=None, id=None, access=None, pattern=None):
        return self.giveMeProfiles(self._datasetConditionalAccess, (profile,id,access), pattern)

    @property
    def datasetAccess(self):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._datasetAccess

    def datasetPermit(self, profile=None, id=None, access=None, pattern=None):
        return self.giveMeProfiles(self._datasetAccess, (profile,id,access), pattern)

    @property
    def uacc_read_datasets(self):
        return self._datasets.loc[self._datasets.DSBD_UACC=="READ"]

    @property
    def generals(self, query=None):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._generals

    generics = property(deprecated(generals,"generics"))

    def general(self, resclass=None, profile=None, pattern=None):
        return self.giveMeProfiles(self._generals, (resclass,profile), pattern)

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
    
    def generalPermit(self, resclass=None, profile=None, id=None, access=None, pattern=None):
        return self.giveMeProfiles(self._generalAccess, (resclass,profile,id,access), pattern)
    
    
    @property
    def generalConditionalAccess(self):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._generalConditionalAccess

    genericConditionalAccess = property(deprecated(generalConditionalAccess,"genericConditionalAccess"))
    
    def generalConditionalPermit(self, resclass=None, profile=None, id=None, access=None, pattern=None):
        return self.giveMeProfiles(self._generalConditionalAccess, (resclass,profile,id,access), pattern)

    def rankedAccess(args):
        ''' translate access levels into integers, add 10 if permit is for the user ID. 
        could be used in .apply() but would be called for each row, so very very slow '''
        (userid,authid,access) = args
        accessNum = RACF.accessKeywords.index(access)
        return accessNum+10 if userid==authid else accessNum

    def acl(self, df, permits=True, explode=False, resolve=False, admin=False, access=None, allows=None, sort="profile"):
        ''' transform {dataset,general}[Conditional]Access table:
        permits=True: show normal ACL (with the groups identified in field USER_ID)
        explode=True: replace all groups with the users connected to the groups (in field USER_ID)
        resolve=True: show user specific permit, or the highest group permit for each user
        admin=True: add the users that have ability to change the groups on the ACL (in field ADMIN_ID)
            VIA identifies the group name, AUTHORITY the RACF privilege involved
        access=access level: show entries that are equal to the level specified, access='CONTROL'
        allows=access level: show entries that are higher or equal to the level specified, allows='UPDATE'
        sort=["user","access","id","admin","profile"] sort the resulting output
        '''
        tbName = df.columns[0].split('_')[0]
        tbEntity = tbName[0:2]
        if tbName in ["DSBD","DSACC","DSCACC"]:
            tbProfileKeys = ["NAME","VOL"]
        elif tbName in ["GRBD","GRACC","GRCACC"]:
            tbProfileKeys = ["CLASS_NAME","NAME"]
        else:
            raise StoopidException(f'Table {tbName} not supported for acl( ), except DSBD, DSACC, DSCACC, GRBD, GRACC or GRCACC.')

        if tbName in ["DSBD","GRBD"]:
            # profiles selected, add corresp. access + cond.access frames
            tbProfiles = df[[tbName+"_"+k for k in tbProfileKeys+["OWNER_ID","UACC"]]].copy()
            tbProfiles.columns = [tbProfiles.columns[i].replace(tbName+"_","") for i in range(len(tbProfiles.columns))]
            tbPermits = []
            for tb in [tbEntity+"ACC",tbEntity+"CACC"]:
                if self.parsed(tb)>0:
                    tbPermits.append(getattr(self,self._recordname_df[tb])\
                                     .merge(tbProfiles["UACC"], left_index=True, right_index=True))
                    tbPermits[-1].columns = [tbPermits[-1].columns[i].replace(tb+"_","") for i in range(len(tbPermits[-1].columns))]
            tbPermits = pd.concat(tbPermits,sort=False)\
                          .drop(["RECORD_TYPE","ACCESS_CNT","UACC"],axis=1)\
                          .fillna(' ') 
        elif tbName in ["DSACC","DSCACC","GRACC","GRCACC"]:
            # access frame selected, add profiles from frame tbEntity+BD
            tbPermits = df.copy()
            tbPermits.columns = [tbPermits.columns[i].replace(tbName+"_","") for i in range(len(tbPermits.columns))]
            tbPermits.drop(["RECORD_TYPE","ACCESS_CNT"],axis=1,inplace=True)
            tbProfiles = getattr(self,self._recordname_df[tbEntity+"BD"])\
                         .loc[tbPermits.droplevel([-2,-1]).index.drop_duplicates()].copy()
            tbProfiles.columns = [tbProfiles.columns[i].replace(tbEntity+"BD_","") for i in range(len(tbProfiles.columns))]
            tbProfiles = tbProfiles[tbProfileKeys+["OWNER_ID","UACC"]]
        else:
            raise StoopidException(f'Table {tbName} not supported for acl( ), except DSBD, DSACC, DSCACC, GRBD, GRACC or GRCACC.')
          
        # tbProfiles and tbPermits have column names without the tbName prefix
        
        returnFields = ["USER_ID","AUTH_ID","ACCESS"]
        if tbName in ["DSCACC","GRCACC"]:
            returnFields = returnFields+["CATYPE","CANAME","NET_ID","CACRITERIA"]

        sortBy = {"user":["USER_ID"]+tbProfileKeys, 
                  "access":["RANKED_ACCESS","USER_ID"],
                  "id":["AUTH_ID"]+tbProfileKeys, 
                  "admin":"ADMIN_ID", 
                  "profile":tbProfileKeys+["USER_ID"]}
        if sort not in sortBy:
            raise StoopidException(f'Sort value {sort} not supported for acl( ), use one of {",".join(sortBy.keys())}.')
        
        if explode or resolve:  # get user IDs connected to groups into field USER_ID
            acl = pd.merge(tbPermits, self._connectByGroup[["USCON_NAME"]], how="left", left_on="AUTH_ID", right_index=True)
            acl.insert(3,"USER_ID",acl["USCON_NAME"].where(acl["USCON_NAME"].notna(),acl["AUTH_ID"]))
        elif permits:  # just the userid+access from RACF, add USER_ID column for consistency
            acl = tbPermits
            acl.insert(3,"USER_ID",acl["AUTH_ID"].where(~ acl["AUTH_ID"].isin(self._groups.index.values),"-group-"))
        else:
            acl = pd.DataFrame(columns=tbProfileKeys+returnFields)
        if permits or explode or resolve:  # add -uacc- pseudo access
            uacc = tbProfiles.query("UACC!='NONE'").copy()
            if not uacc.empty:
                uacc["OWNER_ID"] = "-uacc-" # is renamed to AUTH_ID
                uacc["USER_ID"] = "-uacc-"
                uacc = uacc.rename({"OWNER_ID":"AUTH_ID","UACC":"ACCESS"},axis=1)
                acl = pd.concat([acl,uacc], ignore_index=True, sort=False).fillna(' ') # lose index b/c concat doesn't support us
            
        if resolve or sort=="access":
            # map access level to number, add 10 for user permits so they override group permits in sort_values( )
            acl["RANKED_ACCESS"] = acl["ACCESS"].map(RACF.accessKeywords.index)
            acl["RANKED_ACCESS"] = acl["RANKED_ACCESS"].where(acl["USER_ID"]!=acl["AUTH_ID"], acl["RANKED_ACCESS"]+10)
        if resolve:
            # keep highest value of RANKED_ACCESS, this is at least twice as fast as using .iloc[].idxmax() 
            condAcc = ["CATYPE","CANAME"] if "CATYPE" in acl.columns else []
            acl = acl.sort_values(tbProfileKeys+["USER_ID"]+condAcc+["RANKED_ACCESS"])\
                     .drop_duplicates(tbProfileKeys+["USER_ID"]+condAcc, keep='last')
        if sort=="access":
            acl.RANKED_ACCESS = 10 - (acl.RANKED_ACCESS % 10)  # highest access first
        
        if admin:
            # owner of the profile, or group special, or group authority
            # users who own the profiles
            profile_userowners = pd.merge(tbProfiles, self._users["USBD_NAME"],
                                          how="inner", left_on="OWNER_ID", right_index=True)\
                                   .rename({"OWNER_ID":"ADMIN_ID"},axis=1)\
                                   .drop(["USBD_NAME","UACC"],axis=1)
            profile_userowners["AUTHORITY"] = "OWNER"
            profile_userowners["VIA"] = "-profile-"
            profile_userowners["ACCESS"] = "-owner-"

            # groups that own the profiles
            profile_groupowner1 = pd.merge(tbProfiles, self._groups[["GPBD_NAME"]],
                                           how="inner", left_on="OWNER_ID", right_index=True)\
                                    .drop(["GPBD_NAME","UACC"],axis=1)
            profile_groupowner1["ACCESS"] = "-owner-"
            profile_groupowner2 = pd.merge(profile_groupowner1, self._ownertreeLines, how="inner", left_on="OWNER_ID", right_index=True)\
                                    .drop(["GROUP","OWNER_ID"],axis=1)
            # identify group special on owner group and on any owning group
            profile_groupowner1.rename({"OWNER_ID":"OWNER_IDS"},axis=1,inplace=True)
            # continue with group special processing to find admin users

            # who has administrative authority to modify groups from the ACL?
            admin_owners = pd.merge(tbPermits, self._groups[["GPBD_NAME","GPBD_OWNER_ID","GPBD_SUPGRP_ID"]],
                                    how="inner", left_on="AUTH_ID", right_index=True)
            admin_owners["USER_ID"] = "-group-"

            # users who own those groups
            admin_gowners = admin_owners.query("GPBD_OWNER_ID != GPBD_SUPGRP_ID")\
                                        .rename({"GPBD_NAME":"VIA","GPBD_OWNER_ID":"ADMIN_ID"},axis=1)\
                                        .drop(["GPBD_SUPGRP_ID"],axis=1)
            admin_gowners["AUTHORITY"] = "OWNER"
            
            # find all owner groups + groups up to SYS1 or user ID that breaks ownership
            admin_grpspec1 = admin_owners.query("GPBD_OWNER_ID == GPBD_SUPGRP_ID")\
                                         .drop(["GPBD_OWNER_ID","GPBD_SUPGRP_ID"],axis=1)
            admin_grpspec2 = pd.merge(admin_grpspec1, self._ownertreeLines, how="inner", left_on="AUTH_ID", right_index=True)\
                               .drop(["GPBD_NAME","GROUP"],axis=1)
            admin_grpspec1.rename({"GPBD_NAME":"OWNER_IDS"},axis=1,inplace=True)
            
            # identify group special on ACL group and on any owning group
            admin_grpspec = pd.merge(pd.concat([admin_grpspec1,admin_grpspec2,profile_groupowner1,profile_groupowner2], sort=False),\
                                     self._connectByGroup[["USCON_NAME","USCON_GRP_ID","USCON_GRP_SPECIAL"]]\
                                             .query('USCON_GRP_SPECIAL == "YES"'),
                                     how="inner", left_on="OWNER_IDS", right_index=True)\
                               .rename({"USCON_NAME":"ADMIN_ID","OWNER_IDS":"VIA"},axis=1)\
                               .drop(["USCON_GRP_ID","USCON_GRP_SPECIAL"],axis=1)
            admin_grpspec["AUTHORITY"] = "GRPSPECIAL"

            # CONNECT or JOIN authority on an ACL group
            admin_grpauth = pd.merge(tbPermits, self._connectByGroup[["USCON_NAME","USCON_GRP_ID","GPMEM_AUTH"]]
                                                 .query('GPMEM_AUTH==["CONNECT","JOIN"]'),
                                     how="inner", left_on="AUTH_ID", right_index=True)\
                              .rename({"USCON_NAME":"ADMIN_ID","USCON_GRP_ID":"VIA","GPMEM_AUTH":"AUTHORITY"},axis=1)
            admin_grpauth["USER_ID"] = "-group-"
            
            acl = pd.concat([acl,profile_userowners,admin_gowners,admin_grpspec,admin_grpauth],
                            ignore_index=True, sort=False).fillna(' ')
            returnFields += ["ADMIN_ID","AUTHORITY","VIA"]
            
        if access:
            acl = acl.loc[acl["ACCESS"].map(RACF.accessKeywords.index)==RACF.accessKeywords.index(access.upper())]
        if allows:
            acl = acl.loc[acl["ACCESS"].map(RACF.accessKeywords.index)>=RACF.accessKeywords.index(allows.upper())]
        return acl.sort_values(by=sortBy[sort])[tbProfileKeys+returnFields].reset_index(drop=True)

    
    def verify(self, rules=None, domains=None, module=".profileFieldRules"):
        ''' verify fields in profiles against the expected value, issues are returned in a df
        rules can be passed as a list of tuples, or dict via parameter, or as function result from external module.
        '''
        
        if not(rules and domains):
            ruleset = importlib.import_module(module, package="pyracf")
            ruleset = importlib.reload(ruleset)
            if not rules:
                rules = ruleset.rules(self)
            if not domains:
                domains = ruleset.domains(self,pd)  # needs pandas

        if type(rules)==str:
            rules= yaml.safe_load(rules)

        def listMe(item):
            ''' make list in parameters optional when there is only 1 item '''
            return item if type(item)==list else [item]
        
        brokenSum = pd.DataFrame(columns=['CLASS','PROFILE','FIELD_NAME','EXPECT','VALUE'])
        for (tbNames,*tbCriteria) in rules:
            for tbName in listMe(tbNames):
                dfName = RACF._recordname_df[tbName]
                if hasattr(self,dfName):
                    tbDF = getattr(self,dfName)
                    if tbDF.empty:
                      continue
                else:
                    continue
                tbEntity = tbName[0:2]
                tbClassName = {'DS':'dataset', 'GP':'group', 'GR':'general', 'US':'user'}[tbEntity]
                ixLevel = 1 if tbEntity=='GR' else 0  # GR has CLASS before NAME in the index

                for tbCrit in tbCriteria:
                    locs = True
                    matchPattern = None
                    if 'class' in tbCrit:
                        if tbEntity!='GR':
                            print('only for GR')
                        classPattern = ''
                        for cl in listMe(tbCrit['class']):
                            classPattern += RACF.generic2regex(cl) + "|"
                        locs &= tbDF.index.get_level_values(0).str.match(classPattern[:-1])
                    if '-class' in tbCrit:
                        if tbEntity=='GR':
                            classPattern = ''
                            for cl in listMe(tbCrit['-class']):
                                classPattern += RACF.generic2regex(cl) + "|"
                            locs &= ~ tbDF.index.get_level_values(0).str.match(classPattern[:-1])
                    if 'profile' in tbCrit:
                        locs &= tbDF.index.get_level_values(ixLevel).str.match(RACF.generic2regex(tbCrit['profile']))
                    if '-profile' in tbCrit:
                        locs &= ~ tbDF.index.get_level_values(ixLevel).str.match(RACF.generic2regex(tbCrit['-profile']))
                    if 'match' in tbCrit:
                        matchPattern = tbCrit['match'].replace('.','\.').replace('*','\*')\
                                                      .replace('(','(?P<').replace(')','>[^.]*)')
                        matched = tbDF[tbName+'_NAME'].str.extract(matchPattern)
                    for fldCrit in listMe(tbCrit['field']):
                        fldName = fldCrit['name'] if matchPattern else tbName+'_'+fldCrit['name']
                        fldExpect = fldCrit['expect'] if 'expect' in fldCrit else None
                        if matchPattern:
                            for fn in matched.columns:
                                if fn==fldName:
                                    if fldExpect:
                                        locs &= matched[fn].gt('') & - matched[fn].isin(domains[fldExpect])
                                    if 'or' in fldCrit:
                                        locs &= ~ matched[fn].isin(listMe(fldCrit['or']))
                        else:
                            if fldExpect:
                                locs &= tbDF[fldName].gt('') & - tbDF[fldName].isin(domains[fldExpect])
                            if 'or' in fldCrit:
                                locs &= ~ tbDF[fldName].isin(listMe(fldCrit['or']))
                        if any(locs):
                            broken = tbDF.loc[locs].copy()
                            broken['CLASS'] = broken[tbName+'_CLASS_NAME'] if tbEntity=='GR' else tbClassName
                            broken['PROFILE'] = broken[tbName+'_NAME']
                            broken['FIELD_NAME'] = fldName
                            broken['EXPECT'] = fldExpect
                            broken['VALUE'] = matched[fldName] if matchPattern else broken[fldName]
                            brokenSum = pd.concat([brokenSum,broken[brokenSum.columns]],
                                                   sort=False, ignore_index=True)
        return brokenSum        
    

    @property
    def neworphans(self):
        return self.verify(
            rules = [
                (['DSACC','DSCACC','GRACC','GRCACC'],
                 {'field': {'name':'AUTH_ID', 'expect':'ACLID'}})
            ]
        )


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

    def tree(self,linkup_field="GPBD_SUPGRP_ID"):
        # get all owners... (group or user) or all superior groups
        tree = {}
        where_is = {}
        higher_ups = self.groups.groupby(linkup_field)
        for higher_up in higher_ups.groups.keys():
            if higher_up not in tree:
                tree[higher_up] = []
                for group in higher_ups.get_group(higher_up)['GPBD_NAME'].values:
                    tree[higher_up].append(group)
                    where_is[group] = tree[higher_up]
        # initially, for an owner tree, anchor can be a user (like IBMUSER) or a group
        # now we gotta condense it, so only IBMUSER and other group owning users are at top level
        # for group tree, we should end up with SYS1, and a list of groups
        deletes = []
        for anchor in tree:
            if anchor in where_is:
                supgrpMembers = where_is[anchor]
                ix = supgrpMembers.index(anchor)
                supgrpMembers[ix] = {anchor: tree[anchor]}
                deletes.append(anchor)
        for anchor in deletes:
            tree.pop(anchor)
        return tree

    def ownertree(self):
        ''' 
        create dict with the user IDs that own groups as key, and a list of their owned groups as values.
        if a group in this list owns group, the list is replaced by a dict.
        '''
        return self._ownertree if self._ownertree else self.tree("GPBD_OWNER_ID")

    def grouptree(self):
        ''' 
        create dict starting with SYS1, and a list of groups owned by SYS1 as values.
        if a group in this list owns group, the list is replaced by a dict.
        because SYS1s superior group is blank/missing, we return the first group that is owned by "".
        '''
        return self._grouptree if self._grouptree else self.tree("GPBD_SUPGRP_ID")[""][0]

    def getdatasetrisk(self, profile=''):
        '''This will produce a dict as follows:
      
        '''
        try:
            if self.parsed("GPBD") == 0 or self.parsed("USCON") == 0 or self.parsed("USBD") == 0 or self.parsed("DSACC") == 0 or self.parsed("DSBD") == 0:
                raise StoopidException("Need to parse DSACC and DSBD first...")
        except:
            raise StoopidException("Need to parse DSACC, USCON, USBD, GPBD and DSBD first...")
        
        try:
            d = self.datasets.loc[[profile]]
        except KeyError:
            d = pd.DataFrame()
        if d.empty:
            raise StoopidException(f'Profile {profile} not found...')
        
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
                    if id in self.users.index:
                        accesslist[access].append(id)
                    else:
                        if id in self.groups.index:
                            g = self.connectData.loc[id][['USCON_NAME','USCON_GRP_SPECIAL']].values
                            for user,grp_special in g:
                                accesslist[access].append(user)
                                # But suppose this user is group_special here?
                                if grp_special=='YES':
                                    accessmanagers[access].append(user)
                            # And wait a minute... this groups owner, can also add people to the group?
                            [gowner,gsupgroup] = self.group(id)[['GPBD_OWNER_ID','GPBD_SUPGRP_ID']].values[0]
                            if gowner in self.users.index:
                                accessmanagers[access].append(gowner)
                            else:
                                # group special propages up
                                while gowner==gsupgroup:
                                    g = self.connectData.loc[gowner][['USCON_NAME','USCON_GRP_SPECIAL']].values
                                    for user,grp_special in g:
                                        if grp_special=='YES':
                                            accessmanagers[access].append(user)
                                    [gowner,gsupgroup] = self.group(gowner)[['GPBD_OWNER_ID','GPBD_SUPGRP_ID']].values[0]
                            # connect authority CONNECT/JOIN allows modification of member list
                            g = self.connects.loc[id][['GPMEM_MEMBER_ID','GPMEM_AUTH']].values
                            for user,grp_auth in g:
                                if grp_auth in ('CONNECT','JOIN'):
                                    accessmanagers[access].append(user)
                # clean up doubles...
                accesslist[access] = list(set(accesslist[access]))
                accessmanagers[access] = list(set(accessmanagers[access]))

        return {
            'owner': owner,
            'uacc': d['DSBD_UACC'].values[0],
            'accessmanagers': accessmanagers,
            'permits': accesslist
        }


class IRRDBU(RACF):
    pass

