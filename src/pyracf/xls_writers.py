import pandas as pd
import xlsxwriter

from .utils import deprecated

class XlsWriter():

    def accessMatrix2xls(self,fileName='irrdbu00.xlsx'):
        ''' create excel file with sheets for each class, lines for each profile and columns for each ID in the access control list.
        runs as method on the RACF object, table('DSACC') or table('GRACC') '''

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

        # ss = datetime.now()

        accessTable = False
        if hasattr(self,'parse'):  # RACF object, show dataset + general resources
            accessTable1 = self.table('DSACC').stripPrefix()[['NAME','AUTH_ID','ACCESS']]
            accessTable1['CLASS_NAME'] = 'dataset'
            accessTable2 = self.table('GRACC').stripPrefix()[['CLASS_NAME','NAME','AUTH_ID','ACCESS']]
            accessTable = pd.concat([accessTable1,accessTable2], sort=False)\
                            .set_index("CLASS_NAME",drop=False)
        elif hasattr(self,'_fieldPrefix'):  # ProfileFrame
            if self._fieldPrefix=='DSACC_':
                accessTable = self.stripPrefix()[['NAME','AUTH_ID','ACCESS']]
                accessTable['CLASS_NAME'] = 'dataset'
                accessTable = accessTable.set_index('CLASS_NAME', drop=False)
            elif self._fieldPrefix=='GRACC_':
                accessTable = self.stripPrefix()[['CLASS_NAME','NAME','AUTH_ID','ACCESS']].droplevel([1,2,3])
        if isinstance(accessTable,pd.DataFrame):
            accessTable.ACCESS = accessTable.ACCESS.apply(accessLevels.get)  # reduce access levels to 1 character
        else:
            raise TypeError('accessMatrix2xls runs off the RACF object, datasetAccess or generalAccess')

        for resClass in accessTable.index.unique():
            if not resClass or resClass == 'DIGTCERT': continue  # contains buggy records
            accesssForClass = accessTable.loc[[resClass]]
            authIDsInClass = accesssForClass.AUTH_ID.nunique()
            profilesInClass = accesssForClass.shape[0]
            longestProfile = max(accesssForClass.NAME.str.len())
            pivotTab = accesssForClass.pivot(index='NAME',columns='AUTH_ID',values='ACCESS')
            pivotTab.to_excel(writer, sheet_name=resClass)
            worksheet = writer.sheets[resClass]
            worksheet.set_row(0, 64, format_br)
            worksheet.set_column(1, authIDsInClass+1, 2, format_center)
            worksheet.set_column(0, 0, longestProfile + 2)
            worksheet.write(0, 0, f'{resClass}\n\n\nProfile', format_nr)
            for level,fmt in accessLevelFormats.items():
                worksheet.conditional_format(1,1,profilesInClass,authIDsInClass,
                    {
                        "type": "cell",
                        "criteria": "==",
                        "value": f'"{level}"',
                        "format": fmt
                     }
                )

        writer.close()

    xls = deprecated(accessMatrix2xls,"xls")
