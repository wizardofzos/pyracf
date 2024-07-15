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

import os
import glob

import warnings

from .exceptions import PyRacfException
from .profile_frame import ProfileFrame
from .profile_publishers import ProfilePublisher
from .rule_verify import RuleVerifier
from .racf_functions import accessKeywords
from .utils import deprecated, readableList
from .xls_writers import XlsWriter


class RACF(ProfilePublisher,XlsWriter):

    # Our states
    STATE_BAD         = -1
    STATE_INIT        =  0
    STATE_PARSING     =  1
    STATE_CORRELATING =  2
    STATE_CORRELATED  =  3
    STATE_READY       =  4

    # keep track of names used for a record type, record type + name must match those in offsets.json
    # A dict with 'key' -> RecordType
    #                   'name' -> Internal name (and prefix for pickle-files, variables in the dfs (GPMEM_NAME etc... from offsets.json))
    #                   'df'   -> name of internal df
    #                   'index' -> index if different from <name>_NAME (and <name>_CLASS_NAME for GRxxx)
    #                   'publisher' -> adds property in class to get the df
    #                                missing   -> same as df without the _
    #                                str       -> define this name as property, unless there is a method in ProfilePublisher with this name

    _recordtype_info = {
    '0100': {'name':'GPBD', 'df':'_groups'},
    '0101': {'name':'GPSGRP', 'df':'_subgroups'},
    '0102': {'name':'GPMEM', 'df':'_connects', "index":["GPMEM_NAME","GPMEM_MEMBER_ID"]},
    '0103': {'name':'GPINSTD', 'df':'_groupUSRDATA'},
    '0110': {'name':'GPDFP', 'df':'_groupDFP'},
    '0120': {'name':'GPOMVS', 'df':'_groupOMVS'}, # add GPOMVS_GID_
    '0130': {'name':'GPOVM', 'df':'_groupOVM'},
    '0141': {'name':'GPTME', 'df':'_groupTME'},
    '0151': {'name':'GPCSD', 'df':'_groupCSDATA'},
    '0200': {'name':'USBD', 'df':'_users'},
    '0201': {'name':'USCAT', 'df':'_userCategories'},
    '0202': {'name':'USCLA', 'df':'_userClasses'},
    '0203': {'name':'USGCON', 'df':'_groupConnect', "index":["USGCON_GRP_ID","USGCON_NAME"]},
    '0204': {'name':'USINSTD', 'df':'_userUSRDATA'},
    '0205': {'name':'USCON', 'df':'_connectData', "index":["USCON_GRP_ID","USCON_NAME"]},
    '0206': {'name':'USRSF', 'df':'_userRRSFdata', 'publisher':'userRRSFDATA'},
    '0207': {'name':'USCERT', 'df':'_userCERTname'},
    '0208': {'name':'USNMAP', 'df':'_userAssociationMapping'},
    '0209': {'name':'USDMAP', 'df':'_userDistributedIdMapping'},
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
    '0270': {'name':'USOMVS', 'df':'_userOMVS'}, # add USOMVS_UID_
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
    '1210': {'name':'USMFAC', 'df':'_userMFAfactorTags'},
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
    '0504': {'name':'GRVOL', 'df':'_generalTAPEvolumes'},
    '0505': {'name':'GRACC', 'df':'_generalAccess', "index":["GRACC_CLASS_NAME","GRACC_NAME","GRACC_AUTH_ID","GRACC_ACCESS"]},
    '0506': {'name':'GRINSTD', 'df':'_generalUSRDATA'},
    '0507': {'name':'GRCACC', 'df':'_generalConditionalAccess', "index":["GRCACC_CLASS_NAME","GRCACC_NAME","GRCACC_AUTH_ID","GRCACC_ACCESS"]},
    '0508': {'name':'GRFLTR', 'df':'_generalDistributedIdFilter', 'publisher':'DistributedIdFilter'},
    '0509': {'name':'GRDMAP', 'df':'_generalDistributedIdMapping', 'publisher':'DistributedIdMapping'},
    '0510': {'name':'GRSES', 'df':'_generalSESSION', 'publisher':'SESSION'}, # APPCLU profiles
    '0511': {'name':'GRSESE', 'df':'_generalSESSIONentities', 'publisher':'SESSIONentities'},
    '0520': {'name':'GRDLF', 'df':'_generalDLFDATA', 'publisher':'DLFDATA'},
    '0521': {'name':'GRDLFJ', 'df':'_generalDLFDATAjobnames', 'publisher':'DLFDATAjobnames'},
    '0530': {'name':'GRSIGN', 'df':'_generalSSIGNON', 'publisher':'SSIGNON'}, # add APPLDATA
    '0540': {'name':'GRST', 'df':'_generalSTDATA', 'publisher':'STDATA'},
    '0550': {'name':'GRSV', 'df':'_generalSVFMR', 'publisher':'SVFMR'}, # SYSMVIEW profiles
    '0560': {'name':'GRCERT', 'df':'_generalCERT', 'publisher':'CERT'}, # add UACC and APPLDATA
    '1560': {'name':'CERTN', 'df':'_generalCERTname', 'publisher':'CERTname'},
    '0561': {'name':'CERTR', 'df':'_generalCERTreferences', 'publisher':'CERTreferences'},
    '0562': {'name':'KEYR', 'df':'_generalKEYRING', 'publisher':'KEYRING'}, # add APPLDATA
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
    '05J1': {'name':'GRCSD', 'df':'_generalCSDATA'},
    '05K0': {'name':'GRIDTP', 'df':'_generalIDTFPARMS', 'publisher':'IDTFPARMS'},
    '05L0': {'name':'GRJES', 'df':'_generalJES', 'publisher':'JES'}
    }

    _recordname_type = {}    # {'GPBD': '0100', ....}
    _recordname_df = {}      # {'GPBD': '_groups', ....}
    _recordname_publisher = {}      # {'GPBD': 'groups', ....}
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

    # define publishers as class properties so they turn up in sphinx-autodoc
    for (rtype,rinfo) in _recordtype_info.items():
        publisher = rinfo['publisher'] if 'publisher' in rinfo else rinfo['df'].lstrip('_')
        if publisher:
            _recordname_publisher.update({rinfo['name']: publisher}) # add publisher name to map for use in r.table()

            if not hasattr(ProfilePublisher,publisher) or publisher in getattr(ProfilePublisher,'_doc_stubs'):
                # publisher is not a method in ProfilePublisher, so add property and for docs add purpose too
                purpose = rinfo['offsets'][0]['field-desc']\
                          .replace('Record type of the','')\
                          .replace('Record Type of the','')\
                          .replace(' record','')\
                          .replace(' Record','')

                def _publish(self,frame=rinfo['df']) -> ProfileFrame:
                    return getattr(self,frame)

                vars()[publisher] = property(_publish,doc=purpose)

    _grouptreeLines     = None  # df with all supgroups up to SYS1
    _ownertreeLines     = None  # df with owners up to SYS1 or user ID

    try:
        del file, rtype, rinfo, offset, _offsets, publisher, purpose  # don't need these as class attributes
    except NameError:
        pass

    def __init__(self, irrdbu00=None, pickles=None, auto_pickles=False, prefix=''):

        self._state = self.STATE_INIT

        if not irrdbu00 and not pickles and not auto_pickles:
            self._state = self.STATE_BAD
        elif pickles and not auto_pickles:
            # Read from pickles dir
            self.load_pickles(path=pickles, prefix=prefix)
            irrbdu00 = None  # don't read another database
        elif pickles and auto_pickles:
            # Read from pickles dir unless irrdbu00 is more recent
            picklefiles = glob.glob(f'{pickles}/{prefix}*.pickle')
            last_update = 0
            for pickle in picklefiles:
                fname = os.path.basename(pickle)
                recordname = fname.replace(prefix,'').split('.')[0]
                if recordname in RACF._recordname_type:
                    last_update = max(last_update,os.path.getmtime(pickle))
            if last_update==0:
                print(f'no matching pickles found {pickles}/{prefix}*.pickle')
            if irrdbu00 is None or os.path.getmtime(irrdbu00)<last_update: # unload is older than pickles, so use pickles
                self.load_pickles(path=pickles, prefix=prefix)
                irrdbu00 = None  # don't read unload
            else: # newer unload, pickles must be refreshed
                if irrdbu00 is None:
                    raise ValueError('autopickle has to process an irrdbu00 input file, but no file specified')
                self._auto_pickles = True
                self._pickles = pickles
                self._pickles_prefix = prefix
        self._irrdbu00 = irrdbu00

        if irrdbu00:
            # prepare for user's choice to do parse() or fancycli()
            self._unloadlines = sum(1 for _ in open(self._irrdbu00, errors="ignore"))

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
        elif self._state == self.STATE_CORRELATED:
            status = "Saving tables to pickles"
            start = self._starttime
            speed = math.floor(seen/((datetime.now() -self._starttime).total_seconds()))
        elif self._state == self.STATE_READY:
            status = "Ready"
            speed  = math.floor(seen/((self._stoptime - self._starttime).total_seconds()))
            parsetime = (self._stoptime - self._starttime).total_seconds()
        else:
            status = "Limbo"
        return {'status': status, 'input-lines': self._unloadlines, 'lines-read': seen, 'lines-parsed': parsed, 'lines-per-second': speed, 'parse-time': parsetime}

    def parse_fancycli(self, recordtypes=None, save_pickles=False, prefix=''):
        if self._irrdbu00 is None:
            print('No parse needed, pickles were loaded')
            return
        print(f'{datetime.now().strftime("%y-%m-%d %H:%M:%S")} - parsing {self._irrdbu00}')
        self.parse(recordtypes=recordtypes)
        print(f'{datetime.now().strftime("%y-%m-%d %H:%M:%S")} - selected recordtypes: {",".join(recordtypes) if recordtypes else "all"}')
        while self._state < self.STATE_CORRELATING:
            progress =  math.floor(((sum(r['seen'] for r in self._records.values() if r)) / self._unloadlines) * 63)
            pct = (progress/63) * 100 # not as strange as it seems:)
            done = progress * '▉'
            todo = (63-progress) * ' '
            print(f'{datetime.now().strftime("%y-%m-%d %H:%M:%S")} - progress: {done}{todo} ({pct:.2f}%)'.center(80), end="\r")
            time.sleep(0.5)
        print('')
        while self._state < self.STATE_CORRELATED:
             print(f'{datetime.now().strftime("%y-%m-%d %H:%M:%S")} - correlating data {40*" "}', end="\r")
             time.sleep(0.5)
        print('')
        # make completed line always show 100% :)
        print(f'{datetime.now().strftime("%y-%m-%d %H:%M:%S")} - progress: {63*"▉"} ({100:.2f}%)'.center(80))
        for r in (recordtypes if recordtypes else self._recordtype_info.keys()):
            print(f'{datetime.now().strftime("%y-%m-%d %H:%M:%S")} - recordtype {r} -> {self.parsed(self._recordtype_info[r]["name"])} records parsed')
        print(f'{datetime.now().strftime("%y-%m-%d %H:%M:%S")} - total parse time: {(self._stoptime - self._starttime).total_seconds()} seconds')
        if save_pickles or hasattr(self,'_auto_pickles'):
            if hasattr(self,'_auto_pickles'):
                save_pickles = self._pickles # save to auto-manage directory
            self.save_pickles(path=save_pickles,prefix=prefix)
            print(f'{datetime.now().strftime("%y-%m-%d %H:%M:%S")} - Pickle files saved to {save_pickles}')
        self._state = self.STATE_READY

    def parse(self, recordtypes=None):
        if self._irrdbu00 is None:
            print('No parse needed')
            return
        pt = threading.Thread(target=self.parse_t,args=(recordtypes,))
        pt.start()
        return True

    def parse_t(self, thingswewant=None):
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
                if r in RACF._recordtype_info and (not thingswewant or r in thingswewant):
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
            if not thingswewant or rtype in thingswewant:
                setattr(self, rinfo['df'], ProfileFrame.from_dict(self._parsed[rtype]))

        # Reduce memory use, delete self._parsed after dataframes are made
        del self._parsed

        # We need the correlate anyways all the times so let's run it
        self.THREAD_COUNT -= 1
        if self.THREAD_COUNT == 0:
            self._state = self.STATE_CORRELATING
            self._correlate()
            self._state = self.STATE_CORRELATED
            self._stoptime = datetime.now()
            if hasattr(self,'_auto_pickles'):
                self.save_pickles(path=self._pickles,prefix=self._pickles_prefix)
            self._state = self.STATE_READY
            self._stoptime = datetime.now()
        return True

    def parsed(self, rname):
        """ how many records with this name (type) were parsed """
        rtype = RACF._recordname_type[rname]
        return self._records[rtype]['parsed'] if rtype in self._records else 0

    def table(self, rname=None) -> ProfileFrame:
        """ return table with this name (type) """
        if rname:
            try:
                return getattr(self, RACF._recordname_publisher[rname])
            except KeyError:
                warnings.warn(f'RACF object does not have a table {rname}')
        else:
            raise TypeError(f"table name missing, try {readableList(sorted(RACF._recordname_publisher.keys()))}")

    def _correlate(self, thingswewant=_recordtype_info.keys()):
        """ construct tables that combine the raw dataframes for improved processing """

        # use the table definitions in _recordtype_info finalize the dfs:
        # set consistent index columns for existing dfs: profile key, connect group+user, of profile class+key (for G.R.)

        for (rtype,rinfo) in RACF._recordtype_info.items():
            if rtype in thingswewant and rtype in self._records and self._records[rtype]['parsed']>0:
                df = getattr(self,rinfo['df'])  # dataframe with these records
                df._RACFobject = self  # used to access _groups and _connectData from ProfileFrame methods
                fieldPrefix = rinfo["name"]+"_"
                df._fieldPrefix = fieldPrefix
                if "index" in rinfo:
                    keys = rinfo["index"]
                    names = [k.replace(fieldPrefix,"_") for k in keys]
                elif rtype[1]=="5":  # general resources
                    keys = [fieldPrefix+"CLASS_NAME",fieldPrefix+"NAME"]
                    names = ["_CLASS_NAME","_NAME"]
                else:
                    keys = fieldPrefix+"NAME"
                    names = "_NAME"
                if df.index.names!=names:  # reuse existing index for pickles
                    df.set_index(keys,drop=False,inplace=True)
                    df.rename_axis(names,inplace=True)  # prevent ambiguous index / column names

        # copy group auth (USE,CREATE,CONNECT,JOIN) to complete the connectData list, using index alignment
        if self.parsed("GPBD") > 0 and self.parsed("GPMEM") > 0 and self.parsed("USCON") > 0:
            self._connectData["GPMEM_AUTH"] = self._connects["GPMEM_AUTH"]

        # copy ID(*) access into resource frames, similar to UACC: IDSTAR_ACCESS and ALL_USER_ACCESS
        if self.parsed("DSBD") > 0 and self.parsed("DSACC") > 0 and 'IDSTAR_ACCESS' not in self._datasets.columns:
            uaccs = pd.DataFrame()
            uaccs["UACC_NUM"] = self._datasets["DSBD_UACC"].map(accessKeywords.index)
            uaccs["IDSTAR_ACCESS"] = self._datasetAccess.reindex(['*'],level=1,axis=0).droplevel([1,2])['DSACC_ACCESS']
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
            uaccs["IDSTAR_ACCESS"] = self._generalAccess.reindex(['*'],level=2,axis=0).droplevel([2,3]).drop_duplicates(['GRACC_CLASS_NAME','GRACC_NAME','GRACC_ACCESS'])['GRACC_ACCESS']
            uaccs["IDSTAR_ACCESS"] = uaccs["IDSTAR_ACCESS"].fillna(' ')
            uaccs["IDSTAR_NUM"] = uaccs["IDSTAR_ACCESS"].map(accessKeywords.index)
            uaccs["ALL_USER_NUM"] = uaccs[["IDSTAR_NUM","UACC_NUM"]].max(axis=1)
            uaccs["ALL_USER_ACCESS"] = uaccs['ALL_USER_NUM'].map(accessKeywords.__getitem__)
            column = self._generals.columns.to_list().index('GRBD_UACC')
            self._generals.insert(column+1,"IDSTAR_ACCESS",uaccs["IDSTAR_ACCESS"])
            self._generals.insert(column+2,"ALL_USER_ACCESS",uaccs["ALL_USER_ACCESS"])
            del uaccs

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
        if self._state not in [self.STATE_CORRELATED, self.STATE_READY]:
            raise PyRacfException('Not done parsing yet!')

        df.to_pickle(f'{path}/{prefix}{dfname}.pickle')


    def save_pickles(self, path='/tmp', prefix=''):
        # Sanity check
        if self._state not in [self.STATE_CORRELATED, self.STATE_READY]:
            raise PyRacfException('Not done parsing yet!')
        # Is Path there ?
        if not os.path.exists(path):
            madedir = os.system(f'mkdir -p {path}')
            if madedir != 0:
                raise PyRacfException(f'{path} does not exist, and cannot create')
        # Let's save the pickles
        for (rtype,rinfo) in RACF._recordtype_info.items():
            if rtype in self._records and self._records[rtype]['parsed']>0:
                self.save_pickle(df=getattr(self, rinfo['df']), dfname=rinfo['name'], path=path, prefix=prefix)
            else:
                # TODO: ensure consistent data, delete old pickles that were not saved
                pass


    def load_pickles(self, path='/tmp', prefix=''):
        # Read from pickles dir
        picklefiles = glob.glob(f'{path}/{prefix}*.pickle')
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
        emptyFrame = ProfileFrame()
        for (rtype,rinfo) in RACF._recordtype_info.items():
            if not hasattr(self, rinfo['df']):
                setattr(self, rinfo['df'], emptyFrame)
                self._records[rtype] = {
                  "seen": 0,
                  "parsed": 0
                }

        self._state = self.STATE_CORRELATING
        self._correlate()
        self._state = self.STATE_READY
        self._stoptime = datetime.now()


    @property
    def rules(self) -> RuleVerifier:
        ''' create a RuleVerifier instance '''
        return RuleVerifier(self)


    def getdatasetrisk(self, profile=''):
        '''This will produce a dict as follows:

        '''
        try:
            if self.parsed("GPBD") == 0 or self.parsed("USCON") == 0 or self.parsed("USBD") == 0 or self.parsed("DSACC") == 0 or self.parsed("DSBD") == 0:
                raise PyRacfException("Need to parse DSACC and DSBD first...")
        except:
            raise PyRacfException("Need to parse DSACC, USCON, USBD, GPBD and DSBD first...")

        try:
            d = self.datasets.loc[[profile]]
        except KeyError:
            d = self.datasets.head(0)
        if d.empty:
            raise PyRacfException(f'Profile {profile} not found...')

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

