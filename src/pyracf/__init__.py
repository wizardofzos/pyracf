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

from .group_structure import GroupStructureTree
from .profile_frame import ProfileFrame
from .racf_functions import accessKeywords
from .utils import deprecated

class StoopidException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class RACF:
    
    # Our states
    STATE_BAD         = -1
    STATE_INIT        =  0
    STATE_PARSING     =  1
    STATE_READY       =  2
    STATE_CORRELATING =  3

    # keep track of names used for a record type, record type + name must match those in offsets.json
    # A dict with 'key' -> RecordType
    #                   'name' -> Internal name (and prefix for pickle-files, variables in the dfs (GPMEM_NAME etc... from offsets.json))
    #                   'df'   -> name of internal df
    #                   'index' -> index if different from <name>_NAME (and <name>_CLASS_NAME for GRxxx)
    #                   'publisher' -> adds property in class to get the df (default: no publisher)
    #                                *         -> same as df without the _
    #                                all but * -> this name as property
    _recordtype_info = {
    '0100': {'name':'GPBD', 'df':'_groups', 'publisher':'*'},
    '0101': {'name':'GPSGRP', 'df':'_subgroups', 'publisher':'*'},
    '0102': {'name':'GPMEM', 'df':'_connects', "index":["GPMEM_NAME","GPMEM_MEMBER_ID"], 'publisher':'*'},
    '0103': {'name':'GPINSTD', 'df':'_groupUSRDATA', 'publisher':'*'},
    '0110': {'name':'GPDFP', 'df':'_groupDFP', 'publisher':'*'},
    '0120': {'name':'GPOMVS', 'df':'_groupOMVS', 'publisher':'*'},
    '0130': {'name':'GPOVM', 'df':'_groupOVM'},
    '0141': {'name':'GPTME', 'df':'_groupTME', 'publisher':'*'},
    '0151': {'name':'GPCSD', 'df':'_groupCSDATA', 'publisher':'*'},
    '0200': {'name':'USBD', 'df':'_users', 'publisher':'*'},
    '0201': {'name':'USCAT', 'df':'_userCategories', 'publisher':'*'},
    '0202': {'name':'USCLA', 'df':'_userClasses', 'publisher':'*'},
    '0203': {'name':'USGCON', 'df':'_groupConnect', "index":["USGCON_GRP_ID","USGCON_NAME"], 'publisher':'*'},
    '0204': {'name':'USINSTD', 'df':'_userUSRDATA'},  # , 'publisher':'*'
    '0205': {'name':'USCON', 'df':'_connectData', "index":["USCON_GRP_ID","USCON_NAME"], 'publisher':'*'},
    '0206': {'name':'USRSF', 'df':'_userRRSFdata', 'publisher':'userRRSFDATA'},
    '0207': {'name':'USCERT', 'df':'_userCERTname', 'publisher':'*'},
    '0208': {'name':'USNMAP', 'df':'_userAssociationMapping', 'publisher':'*'},
    '0209': {'name':'USDMAP', 'df':'_userDistributedIdMapping'},  # , 'publisher':'*'
    '020A': {'name':'USMFA', 'df':'_userMFAfactor', 'publisher':'*'},
    '020B': {'name':'USMPOL', 'df':'_userMFApolicies', 'publisher':'*'},
    '0210': {'name':'USDFP', 'df':'_userDFP', 'publisher':'*'},
    '0220': {'name':'USTSO', 'df':'_userTSO', 'publisher':'*'},
    '0230': {'name':'USCICS', 'df':'_userCICS', 'publisher':'*'},
    '0231': {'name':'USCOPC', 'df':'_userCICSoperatorClasses', 'publisher':'*'},
    '0232': {'name':'USCRSL', 'df':'_userCICSrslKeys', 'publisher':'*'},
    '0233': {'name':'USCTSL', 'df':'_userCICStslKeys', 'publisher':'*'},
    '0240': {'name':'USLAN', 'df':'_userLANGUAGE', 'publisher':'*'},
    '0250': {'name':'USOPR', 'df':'_userOPERPARM', 'publisher':'*'},
    '0251': {'name':'USOPRP', 'df':'_userOPERPARMscope', 'publisher':'*'},
    '0260': {'name':'USWRK', 'df':'_userWORKATTR', 'publisher':'*'},
    '0270': {'name':'USOMVS', 'df':'_userOMVS', 'publisher':'*'},
    '0280': {'name':'USNETV', 'df':'_userNETVIEW', 'publisher':'*'},
    '0281': {'name':'USNOPC', 'df':'_userNETVIEWopclass', 'publisher':'*'},
    '0282': {'name':'USNDOM', 'df':'_userNETVIEWdomains', 'publisher':'*'},
    '0290': {'name':'USDCE', 'df':'_userDCE'},
    '02A0': {'name':'USOVM', 'df':'_userOVM'},
    '02B0': {'name':'USLNOT', 'df':'_userLNOTES'},
    '02C0': {'name':'USNDS', 'df':'_userNDS'},
    '02D0': {'name':'USKERB', 'df':'_userKERB'},
    '02E0': {'name':'USPROXY', 'df':'_userPROXY'},
    '02F0': {'name':'USEIM', 'df':'_userEIM'},
    '02G1': {'name':'USCSD', 'df':'_userCSDATA', 'publisher':'*'},
    '1210': {'name':'USMFAC', 'df':'_userMFAfactorTags', 'publisher':'*'},
    '0400': {'name':'DSBD', 'df':'_datasets', 'publisher':'*'},
    '0401': {'name':'DSCAT', 'df':'_datasetCategories', 'publisher':'*'},
    '0402': {'name':'DSCACC', 'df':'_datasetConditionalAccess', "index":["DSCACC_NAME","DSCACC_AUTH_ID","DSCACC_ACCESS"], 'publisher':'*'},
    '0403': {'name':'DSVOL', 'df':'_datasetVolumes'},
    '0404': {'name':'DSACC', 'df':'_datasetAccess', "index":["DSACC_NAME","DSACC_AUTH_ID","DSACC_ACCESS"], 'publisher':'*'},
    '0405': {'name':'DSINSTD', 'df':'_datasetUSRDATA', 'publisher':'*'},
    '0406': {'name':'DSMEM', 'df':'_datasetMember'},
    '0410': {'name':'DSDFP', 'df':'_datasetDFP', 'publisher':'*'},
    '0421': {'name':'DSTME', 'df':'_datasetTME', 'publisher':'*'},
    '0431': {'name':'DSCSD', 'df':'_datasetCSDATA', 'publisher':'*'},
    '0500': {'name':'GRBD', 'df':'_generals'},
    '0501': {'name':'GRTVOL', 'df':'_generalTAPEvolume', 'publisher':'*'},
    '0502': {'name':'GRCAT', 'df':'_generalCategories', 'publisher':'*'},
    '0503': {'name':'GRMEM', 'df':'_generalMembers'},
    '0504': {'name':'GRVOL', 'df':'_generalTAPEvolumes', 'publisher':'*'},
    '0505': {'name':'GRACC', 'df':'_generalAccess', "index":["GRACC_CLASS_NAME","GRACC_NAME","GRACC_AUTH_ID","GRACC_ACCESS"]},
    '0506': {'name':'GRINSTD', 'df':'_generalUSRDATA', 'publisher':'*'},
    '0507': {'name':'GRCACC', 'df':'_generalConditionalAccess', "index":["GRCACC_CLASS_NAME","GRCACC_NAME","GRCACC_AUTH_ID","GRCACC_ACCESS"]},
    '0508': {'name':'GRFLTR', 'df':'_generalDistributedIdFilter', 'publisher':'DistributedIdFilter'},
    '0509': {'name':'GRDMAP', 'df':'_generalDistributedIdMapping', 'publisher':'DistributedIdMapping'},
    '0510': {'name':'GRSES', 'df':'_generalSESSION', 'publisher':'SESSION'}, # APPCLU profiles
    '0511': {'name':'GRSESE', 'df':'_generalSESSIONentities', 'publisher':'SESSIONentities'},
    '0520': {'name':'GRDLF', 'df':'_generalDLFDATA', 'publisher':'DLFDATA'},
    '0521': {'name':'GRDLFJ', 'df':'_generalDLFDATAjobnames', 'publisher':'DLFDATAjobnames'},
    '0530': {'name':'GRSIGN', 'df':'_generalSSIGNON'}, # needs APPLDATA
    '0540': {'name':'GRST', 'df':'_generalSTDATA', 'publisher':'STDATA'},
    '0550': {'name':'GRSV', 'df':'_generalSVFMR', 'publisher':'SVFMR'}, # SYSMVIEW profiles
    '0560': {'name':'GRCERT', 'df':'_generalCERT', 'publisher':'CERT'},
    '1560': {'name':'CERTN', 'df':'_generalCERTname', 'publisher':'CERTname'},
    '0561': {'name':'CERTR', 'df':'_generalCERTreferences', 'publisher':'CERTreferences'},
    '0562': {'name':'KEYR', 'df':'_generalKEYRING', 'publisher':'KEYRING'},
    '0570': {'name':'GRTME', 'df':'_generalTME', 'publisher':'TME'},
    '0571': {'name':'GRTMEC', 'df':'_generalTMEchild', 'publisher':'TMEchild'},
    '0572': {'name':'GRTMER', 'df':'_generalTMEresource', 'publisher':'TMEresource'},
    '0573': {'name':'GRTMEG', 'df':'_generalTMEgroup', 'publisher':'TMEgroup'},
    '0574': {'name':'GRTMEE', 'df':'_generalTMErole', 'publisher':'TMErole'},
    '0580': {'name':'GRKERB', 'df':'_generalKERB', 'publisher':'KERB'},
    '0590': {'name':'GRPROXY', 'df':'_generalPROXY', 'publisher':'PROXY'},
    '05A0': {'name':'GREIM', 'df':'_generalEIM', 'publisher':'EIM'},
    '05B0': {'name':'GRALIAS', 'df':'_generalALIAS', 'publisher':'ALIAS'}, # IP lookup value in SERVAUTH class
    '05C0': {'name':'GRCDT', 'df':'_generalCDTINFO', 'publisher':'CDTINFO'},
    '05D0': {'name':'GRICTX', 'df':'_generalICTX', 'publisher':'ICTX'},
    '05E0': {'name':'GRCFDEF', 'df':'_generalCFDEF', "index":["GRCFDEF_CLASS","GRCFDEF_NAME"], 'publisher':'CFDEF'},
    '05F0': {'name':'GRSIG', 'df':'_generalSIGVER', 'publisher':'SIGVER'},
    '05G0': {'name':'GRCSF', 'df':'_generalICSF', 'publisher':'ICSF'},
    '05G1': {'name':'GRCSFK', 'df':'_generalICSFsymexportKeylabel', 'publisher':'ICSFsymexportKeylabel'},
    '05G2': {'name':'GRCSFC', 'df':'_generalICSFsymexportCertificateIdentifier', 'publisher':'ICSFsymexportCertificateIdentifier'},
    '05H0': {'name':'GRMFA', 'df':'_generalMFA', 'publisher':'MFA'},
    '05I0': {'name':'GRMFP', 'df':'_generalMFPOLICY', 'publisher':'MFPOLICY'},
    '05I1': {'name':'GRMPF', 'df':'_generalMFPOLICYfactors', 'publisher':'MFPOLICYfactors'},
    '05J1': {'name':'GRCSD', 'df':'_generalCSDATA', 'publisher':'*'},
    '05K0': {'name':'GRIDTP', 'df':'_generalIDTFPARMS', 'publisher':'IDTFPARMS'},
    '05L0': {'name':'GRJES', 'df':'_generalJES', 'publisher':'JES'}
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
    try:
        del file, rtype, rinfo, offset, _offsets  # don't need these as class attributes
    except NameError:
        pass

    _grouptree          = None  # dict with lists
    _ownertree          = None  # dict with lists
    _grouptreeLines     = None  # df with all supgroups up to SYS1
    _ownertreeLines     = None  # df with owners up to SYS1 or user ID
    

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
                    setattr(self, dfname, ProfileFrame.read_pickle(pickle))
                    recordsRetrieved = len(getattr(self, dfname))
                    self._records[recordtype] = {
                      "seen": recordsRetrieved,
                      "parsed": recordsRetrieved
                    }
                    self._unloadlines += recordsRetrieved

            # create remaining public DFs as empty
            for (rtype,rinfo) in RACF._recordtype_info.items():
                if not hasattr(self, rinfo['df']):
                    setattr(self, rinfo['df'], ProfileFrame())
                    self._records[rtype] = {
                      "seen": 0,
                      "parsed": 0
                    }

            self._state = self.STATE_CORRELATING
            self._correlate()
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
        elif self._state == self.STATE_CORRELATING:
            status = "Optimizing tables"
            start = self._starttime
            speed = math.floor(seen/((datetime.now() -self._starttime).total_seconds()))
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
        while self._state != self.STATE_CORRELATING:
            progress =  math.floor(((sum(r['seen'] for r in self._records.values() if r)) / self._unloadlines) * 63)
            pct = (progress/63) * 100 # not as strange as it seems:)
            done = progress * '▉'
            todo = (63-progress) * ' '
            print(f'{datetime.now().strftime("%y-%m-%d %H:%M:%S")} - progress: {done}{todo} ({pct:.2f}%)'.center(80), end="\r")
            time.sleep(0.5)
        print('')
        while self._state != self.STATE_READY:
             print(f'{datetime.now().strftime("%y-%m-%d %H:%M:%S")} - correlating data {40*" "}', end="\r")
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
                setattr(self, rinfo['df'], ProfileFrame.from_dict(self._parsed[rtype]))

        # TODO: Reduce memory use, delete self._parsed after dataframes are made

        # We need the correlate anyways all the times so let's run it
        self.THREAD_COUNT -= 1
        if self.THREAD_COUNT == 0:
            self._state = self.STATE_CORRELATING
            self._correlate()
            self._state = self.STATE_READY         
            self._stoptime = datetime.now()
        return True

    def parsed(self, rname):
        """ how many records with this name (type) were parsed """
        rtype = RACF._recordname_type[rname]
        return self._records[rtype]['parsed'] if rtype in self._records else 0
        
    def _correlate(self, thingswewant=_recordtype_info.keys()):
        """ construct tables that combine the raw dataframes for improved processing """
        
        # use the table definitions in _recordtype_info finalize the dfs:
        # set consistent index columns for existing dfs: profile key, connect group+user, of profile class+key (for G.R.)
        # define properties to access the dfs, in addition to the properties defined as functions below
        for (rtype,rinfo) in RACF._recordtype_info.items():
            fieldPrefix = rinfo["name"]+"_"
            getattr(self,rinfo['df'])._fieldPrefix = fieldPrefix
            if rtype in thingswewant and rtype in self._records and self._records[rtype]['parsed']>0:
                if "index" in rinfo:
                    keys = rinfo["index"]
                    names = [k.replace(fieldPrefix,"_") for k in keys]
                elif rtype[1]=="5":  # general resources
                    keys = [fieldPrefix+"CLASS_NAME",fieldPrefix+"NAME"]
                    names = ["_CLASS_NAME","_NAME"]
                else:
                    keys = fieldPrefix+"NAME"
                    names = "_NAME"
                if getattr(self,rinfo['df']).index.names!=names:  # reuse existing index for pickles
                    getattr(self,rinfo['df']).set_index(keys,drop=False,inplace=True)
                    getattr(self,rinfo['df']).rename_axis(names,inplace=True)  # prevent ambiguous index / column names 
            if 'publisher' in rinfo:
                publisher = rinfo['publisher'] if rinfo['publisher']!='*' else rinfo['df'].lstrip('_')
                if hasattr(self, rinfo['df']):
                    setattr(self, publisher, getattr(self, rinfo['df']))
                else:
                    setattr(self, publisher, lambda x: warnings.warn(f"{publisher} has not been collected."))
            getattr(self,rinfo['df'])._RACFobject = self  # access _groups and connectData from ProfileFrame methods

        # copy group auth (USE,CREATE,CONNECT,JOIN) to complete the connectData list, using index alignment
        if self.parsed("GPBD") > 0 and self.parsed("GPMEM") > 0 and self.parsed("USCON") > 0:
            self._connectData["GPMEM_AUTH"] = self._connects["GPMEM_AUTH"]

        # copy ID(*) access into resource frames, similar to UACC: IDSTAR_ACCESS and ALL_USER_ACCESS
        if self.parsed("DSBD") > 0 and self.parsed("DSACC") > 0 and 'IDSTAR_ACCESS' not in self._datasets.columns:
            uaccs = pd.DataFrame()
            uaccs["UACC_NUM"] = self._datasets["DSBD_UACC"].map(accessKeywords.index)
            uaccs["IDSTAR_ACCESS"] = self._datasetAccess.gfilter(None, '*').droplevel([1,2])['DSACC_ACCESS']
            uaccs["IDSTAR_ACCESS"] = uaccs["IDSTAR_ACCESS"].fillna(' ')
            uaccs["IDSTAR_NUM"] = uaccs["IDSTAR_ACCESS"].map(accessKeywords.index)
            uaccs["ALL_USER_NUM"] = uaccs[["IDSTAR_NUM","UACC_NUM"]].max(axis=1)
            uaccs["ALL_USER_ACCESS"] = uaccs['ALL_USER_NUM'].map(accessKeywords.__getitem__)
            column = self._datasets.columns.to_list().index('DSBD_UACC')
            self._datasets.insert(column+1,"IDSTAR_ACCESS",uaccs["IDSTAR_ACCESS"])
            self._datasets.insert(column+2,"ALL_USER_ACCESS",uaccs["ALL_USER_ACCESS"])
            del uaccs
        
        if self.parsed("GRBD") > 0 and self.parsed("GRACC") > 0 and 'IDSTAR_ACCESS' not in self._generals.columns:
            uaccs = pd.DataFrame()
            uaccs["UACC"] = self._generals["GRBD_UACC"]
            uaccs["UACC"] = uaccs["UACC"].where(uaccs["UACC"].isin(accessKeywords),other=' ')  # DIGTCERT fields may be distorted
            uaccs["UACC_NUM"] = uaccs["UACC"].map(accessKeywords.index)
            uaccs["IDSTAR_ACCESS"] = self._generalAccess.gfilter(None, '*').droplevel([1,2])['GRACC_ACCESS']
            uaccs["IDSTAR_ACCESS"] = uaccs["IDSTAR_ACCESS"].fillna(' ')
            uaccs["IDSTAR_NUM"] = uaccs["IDSTAR_ACCESS"].map(accessKeywords.index)
            uaccs["ALL_USER_NUM"] = uaccs[["IDSTAR_NUM","UACC_NUM"]].max(axis=1)
            uaccs["ALL_USER_ACCESS"] = uaccs['ALL_USER_NUM'].map(accessKeywords.__getitem__)
            column = self._generals.columns.to_list().index('GRBD_UACC')
            self._generals.insert(column+1,"IDSTAR_ACCESS",uaccs["IDSTAR_ACCESS"])
            self._generals.insert(column+2,"ALL_USER_ACCESS",uaccs["ALL_USER_ACCESS"])
            del uaccs
        
        # dicts containing lists of groups for printing group structure
        self._ownertree = self.ownertree
        self._grouptree = self.grouptree

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


    # user frames

    def user(self, userid=None, pattern=None):
        return self._users.giveMeProfiles(userid, pattern)

    def connect(self, group=None, userid=None, pattern=None):
        ''' connect('SYS1') returns 1 index level with user IDs, connect(None,'IBMUSER') returns 1 index level with group names '''
        if pattern=='L' or pattern=='LIST':
            return self._connectData.giveMeProfiles((group,userid), pattern)
        else:
            if group and (not userid or userid=='**'):
                # with group given, return connected user IDs via index (.loc['group'] strips level(0))
                selection = group
            elif userid and (not group or group=='**'):
                # with user ID given, return connected groups via index (only level(0))
                return self._connectData.loc[(slice(None),userid),].droplevel(1)
            else:
                # with group + user ID given, return 1 entry with all index levels (because only the data columns will be of interest)
                selection = [(group,userid)]
            try:
                return self._connectData.loc[selection]
            except KeyError:
                return ProfileFrame()


    @property
    def userUSRDATA(self):
        # retained here due to deprecated property definition
        return self._userUSRDATA

    installdata = property(deprecated(userUSRDATA,"installdata"))

    @property
    def userDistributedIdMapping(self):
        # retained here due to deprecated property definition
        return self._userDistributedIdMapping

    userDistributedMapping = property(deprecated(userDistributedIdMapping,"userDistributedMapping"))


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


    # group frames

    def group(self, group=None, pattern=None):
        return self._groups.giveMeProfiles(group, pattern)

    @property
    def groupsWithoutUsers(self):
        return self._groups.loc[~self.groups.GPBD_NAME.isin(self._connectData.USCON_GRP_ID)]
    

    # dataset frames
        
    def dataset(self, profile=None, pattern=None):
        return self._datasets.giveMeProfiles(profile, pattern)

    def datasetConditionalPermit(self, profile=None, id=None, access=None, pattern=None):
        return self._datasetConditionalAccess.giveMeProfiles((profile,id,access), pattern)

    def datasetPermit(self, profile=None, id=None, access=None, pattern=None):
        return self._datasetAccess.giveMeProfiles((profile,id,access), pattern)

    @property
    def uacc_read_datasets(self):
        return self._datasets.loc[self._datasets.DSBD_UACC=="READ"]
    @property
    def uacc_update_datasets(self):
        return self._datasets.loc[self._datasets.DSBD_UACC=="UPDATE"]
    @property
    def uacc_control_datasets(self):
        return self._datasets.loc[self._datasets.DSBD_UACC=="CONTROL"]
    @property
    def uacc_alter_datasets(self):
        return self._datasets.loc[self._datasets.DSBD_UACC=="ALTER"]


    # general resource frames

    @property
    def generals(self, query=None):
        # retained here due to deprecated property definition
        return self._generals

    generics = property(deprecated(generals,"generics"))

    def general(self, resclass=None, profile=None, pattern=None):
        return self._generals.giveMeProfiles((resclass,profile), pattern)

    @property
    def generalMembers(self, query=None):
        # retained here due to deprecated property definition
        return self._generalMembers    

    genericMembers = property(deprecated(generalMembers,"genericMembers"))

    @property
    def generalAccess(self, query=None):
        # retained here due to deprecated property definition
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._generalAccess

    genericAccess = property(deprecated(generalAccess,"genericAccess"))
    
    def generalPermit(self, resclass=None, profile=None, id=None, access=None, pattern=None):
        return self._generalAccess.giveMeProfiles((resclass,profile,id,access), pattern)
    
    
    @property
    def generalConditionalAccess(self):
        # retained here due to deprecated property definition
        return self._generalConditionalAccess

    genericConditionalAccess = property(deprecated(generalConditionalAccess,"genericConditionalAccess"))
    
    def generalConditionalPermit(self, resclass=None, profile=None, id=None, access=None, pattern=None):
        return self._generalConditionalAccess.giveMeProfiles((resclass,profile,id,access), pattern)

    @property
    def SSIGNON(self): # GRSIGN
        return self._generalSSIGNON.join(self._generals['GRBD_APPL_DATA'])


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


    @property
    def ownertree(self):
        ''' 
        create dict with the user IDs that own groups as key, and a list of their owned groups as values.
        if a group in this list owns group, the list is replaced by a dict.
        '''
        return self._ownertree if self._ownertree else GroupStructureTree(self._groups,"GPBD_OWNER_ID")

    @property
    def grouptree(self):
        ''' 
        create dict starting with SYS1, and a list of groups owned by SYS1 as values.
        if a group in this list owns group, the list is replaced by a dict.
        because SYS1s superior group is blank/missing, we return the first group that is owned by "".
        '''
        return self._grouptree if self._grouptree else GroupStructureTree(self._groups,"GPBD_SUPGRP_ID")


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
            d = ProfileFrame()
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
                            g = self.connect(id)[['USCON_NAME','USCON_GRP_SPECIAL']].values
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
                                    g = self.connect(gowner)[['USCON_NAME','USCON_GRP_SPECIAL']].values
                                    for user,grp_special in g:
                                        if grp_special=='YES':
                                            accessmanagers[access].append(user)
                                    [gowner,gsupgroup] = self.group(gowner)[['GPBD_OWNER_ID','GPBD_SUPGRP_ID']].values[0]
                            # connect authority CONNECT/JOIN allows modification of member list
                            g = self.connect(id)[['USCON_NAME','GPMEM_AUTH']].values
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

