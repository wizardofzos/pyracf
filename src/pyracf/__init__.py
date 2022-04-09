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

#TODO : @property breaks the goddamn query== tools :(

class StoopidException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class RACF:
    # Our states
    STATE_BAD     = -1
    STATE_INIT    =  0
    STATE_PARSING =  1
    STATE_READY   =  2

    # Running threads
    THREAD_COUNT = 0

    # list of parsed record-types
    _records = {}

    # Better be prepared for all of em :)
    GPBD  = []            
    GPSGRP = []
    GPMEM  = []
    GPDFP  = []
    GPOMVS  = []
    GPOVM  = []
    GPTME  = []
    GPCSD  = []
    USBD  = []
    USCAT  = []
    USCLA  = []
    USINSTD  = []
    USCERT  = []
    USNMAP  = []
    USDMAP  = []
    USDFP  = []
    USTSO  = []
    USCICS  = []
    USCOPC  = []
    USCRSL  = []
    USCTSL  = []
    USLAN  = []
    USOPR  = []
    USOPRP  = []
    USWRK  = []
    USOMVS  = []
    USNOPC  = []
    USNDOM  = []
    USDCE  = []
    USOVM  = []
    USLNOT  = []
    USDNS  = []
    USKERB  = []
    USPROXY  = []
    USEIM  = []
    USCSD  = []
    DSBD  = []
    DSACC  = []
    DSDFP  = []
    GRBD  = []
    GRTVOL  = []
    GRACC  = []
    CERTN  = []

    def __init__(self, irrdbu00=None):

        self._state = self.STATE_INIT

        with importlib.resources.open_text("pyracf", "offsets.json") as file:
            self._offsets = json.load(file)      

        if not irrdbu00:
            self._state = self.STATE_BAD
        else:
            self._irrdbu00 = irrdbu00
            self._state    = self.STATE_INIT

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
            speed  = seen/((datetime.now() -self._starttime).total_seconds())

        elif self._state == self.STATE_READY:
            status = "Ready"
            start  = self._starttime
            stop   = self._stopttime
            speed  = seen/((self._stopttime - self._starttime).total_seconds())
            parsetime = (self._stopttime - self._starttime).total_seconds()
     


        return {'status': status, 'lines-read': seen, 'lines-parsed': parsed, 'lines-per-second': math.floor(speed), 'parse-time': parsetime}

    def findOffsets(self, recordType):
        for offset in self._offsets:
            if self._offsets[offset]['record-type'] == recordType:
                return json.loads(json.dumps(self._offsets[offset]))
        return False

    def parse(self, thread_count=1):
        self._starttime = datetime.now()
        if thread_count == 1:
            pt3 = threading.Thread(target=self.parse_t,args=(['0100', '0102', '0200','0400', '0404', '0500', '0505'],))
            pt3.start()
        elif thread_count == 2:
            pt1 = threading.Thread(target=self.parse_t,args=(['0100', '0102', '0200'],))
            pt2 = threading.Thread(target=self.parse_t,args=(['0400', '0404', '0500', '0505'],))
            pt1.start()
            pt2.start()
        else:
            raise StoopidException('Thread count can only be 1 or 2.')
        
        return True

    def parse_t(self, thingswewant=['0100', '0102', '0200', '0400', '0404', '0500', '0505']):
        # TODO: make this multiple threads (per record-type?)
        self._state = self.STATE_PARSING
        self.THREAD_COUNT += 1
        # TODO: Complete all record-types. Fix offsets.json !
        with open(self._irrdbu00, 'r', encoding="utf-8", errors="replace") as infile:
            for line in infile:
                r = line[:4]
                if r in self._records:
                    self._records[r]['seen'] += 1
                else:
                    self._records[r] = {}
                    self._records[r]['seen'] = 1
                    self._records[r]['parsed'] = 0
                if r in thingswewant:
                    model = self.findOffsets(r)
                    if model:
                        irrmodel = {}
                        for model in model['offsets']:
                            start = int(model['start'])
                            end   = int(model['end'])
                            name  = model['field-name']
                            value = line[start-1:end].strip()
                            irrmodel[name] = str(value) 
                            
                        if r == '0100':
                            self.GPBD.append(irrmodel)
                        if r == '0102':
                            self.GPMEM.append(irrmodel)
                        if r == '0200':
                            self.USBD.append(irrmodel)   
                        if r == '0400':
                            self.DSBD.append(irrmodel)
                        if r == '0404':
                            self.DSACC.append(irrmodel)  
                        if r == '0500': 
                            self.GRBD.append(irrmodel)
                        if r == '0505':
                            self.GRACC.append(irrmodel)       
                    self._records[r]['parsed'] += 1
        # all models parsed :)
        if "0200" in thingswewant:
            self._users = pd.DataFrame.from_dict(self.USBD)     
        if "0100" in thingswewant:
            self._groups = pd.DataFrame.from_dict(self.GPBD)
        if "0102" in thingswewant:
            self._connects = pd.DataFrame.from_dict(self.GPMEM)
        if "0400" in thingswewant:
            self._datasets = pd.DataFrame.from_dict(self.DSBD)
        if "0500" in thingswewant:
            self._generics = pd.DataFrame.from_dict(self.GRBD)
        if "0404" in thingswewant:
            self._datasetAccess = pd.DataFrame.from_dict(self.DSACC)
        if "0505" in thingswewant:
            self._genericAccess = pd.DataFrame.from_dict(self.GRACC)
        
        self.THREAD_COUNT -= 1
        if self.THREAD_COUNT == 0:
            self._state = self.STATE_READY         
            self._stopttime = datetime.now()
        return True


    @property
    def users(self):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._users
    
    def user(self, userid=None):
        if not userid:
            raise StoopidException('userid not specified...')
        return self._users.loc[self._users.USBD_NAME==userid]

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
    def datasets(self):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._datasets

    @property
    def connects(self):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._connects

    @property
    def datasetAccess(self):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._datasetAccess

    @property
    def uacc_read_datasets(self):
        return self._datasets.loc[self._datasets.DSBD_UACC=="READ"]

    @property
    def generics(self, query=None):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._generics

    @property
    def genericAccess(self, query=None):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')
        return self._genericAccess
    
    @property
    def orphans(self):
        self._datasetAccess = self._datasetAccess.assign(inGroups=self._datasetAccess.DSACC_AUTH_ID.isin(self._groups.GPBD_NAME))
        self._datasetAccess = self._datasetAccess.assign(inUsers=self._datasetAccess.DSACC_AUTH_ID.isin(self._users.USBD_NAME))
        datasetOrphans = self._datasetAccess.loc[(self._datasetAccess['inGroups'] == False) & (self._datasetAccess['inUsers'] == False) & (self._datasetAccess['DSACC_AUTH_ID'] != "*") & (self._datasetAccess['DSACC_AUTH_ID'] != "&RACUID")]
        
        self._genericAccess = self._genericAccess.assign(inGroups=self._genericAccess.GRACC_AUTH_ID.isin(self._groups.GPBD_NAME))
        self._genericAccess = self._genericAccess.assign(inUsers=self._genericAccess.GRACC_AUTH_ID.isin(self._users.USBD_NAME))
        genericOrphans =  self._genericAccess.loc[(self._genericAccess['inGroups'] == False) & (self._genericAccess['inUsers'] == False) & (self._genericAccess['GRACC_AUTH_ID'] != "*") & (self._genericAccess['GRACC_AUTH_ID'] != "&RACUID")]

        return datasetOrphans, genericOrphans
