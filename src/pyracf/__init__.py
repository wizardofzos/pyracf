import importlib.resources
import json
import pandas as pd 

# No mess with my header lines
import pandas.io.formats.excel
pandas.io.formats.excel.ExcelFormatter.header_style = None

import threading
import time
from datetime import datetime


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

    def status(self):
        seen = 0
        parsed = 0
        for r in self._records:
            seen += self._records[r]['seen']
            parsed += self._records[r]['parsed']

        return {'status': self._state, 'in-lines': seen, 'parsed-lines': parsed}

    def findOffsets(self, recordType):
        for offset in self._offsets:
            if self._offsets[offset]['record-type'] == recordType:
                return json.loads(json.dumps(self._offsets[offset]))
        return False

    def parse(self):
        # TODO: make this multiple threads (per record-type?)
        self._state = self.STATE_PARSING
        # TODO: Complete all record-types. Fix offsets.json !
        thingswewant = ['0200']    
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
                            
                        if r == '0200':
                            self.USBD.append(irrmodel)     
                    self._records[r]['parsed'] += 1
        # all models parsed :)
        if '0200' in thingswewant:
            self._users = pd.DataFrame.from_dict(self.USBD)  
        
        self._state = self.STATE_READY         
        return True


    def users(self, query=None):
        if self._state != self.STATE_READY:
            raise StoopidException('Not done parsing yet! (PEBKAM/ID-10T error)')

        if query == 'special':
            return self._users.loc[self._users['USBD_SPECIAL'] == 'YES']
        if query == 'operations':
            return self._users.loc[self._users['USBD_OPER'] == 'YES']
        # TODO: Need more coolness here :)

        return self._users
