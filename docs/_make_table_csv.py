import sys
import csv

from pyracf import RACF

r = RACF()

hardcoded_publisher = {
    'USINSTD':'userUSRDATA',
    'USDMAP':'userDistributedIdMapping',
    'GRBD':'generals',
    'GRACC':'generalAccess',    
    'GRCACC':'generalConditionalAccess',
    'GRMEM':'_generalMembers',
    'GRSIGN':'SSIGNON'
}
hardcoded_desc = {
    'GRST':'STARTED Class',
    'GRSV':'Systemview'
}

record_type_table = []
fields =  ['Type','Name','DataFrame','Description']
for type,item in r._recordtype_info.items():
    name = item['name']
    df = item['df']
    if 'publisher' in item:
        publisher = item['publisher']
        if publisher == '*':
            publisher = df[1:]
    elif name in hardcoded_publisher:
        df = hardcoded_publisher[name]
    else: publisher = ''
        
    if name in hardcoded_desc:
        desc = hardcoded_desc[name]
    else:
        desc = item['offsets'][0]['field-desc']
        desc = desc.replace('Record type of the','')
        desc = desc.replace('Record Type of the','')
        desc = desc.replace(' record','')
        desc = desc.replace(' Record','')
        desc = desc.split('(')[0].strip()
    record_type_table.append([type,name,publisher,desc])

filename = "record_type_table.csv"
with open(filename, 'w') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerows(record_type_table)

