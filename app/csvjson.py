import xlrd
from collections import OrderedDict
import simplejson as json
import pprint

def convert_csv(filepath):
    wb = xlrd.open_workbook(filepath)
    sh = wb.sheet_by_index(0) 
    # List to hold dictionaries
    samples_list = []
    header_values = []
    # Iterate through each row in worksheet and fetch values into dict
    for rownum in range(0, sh.nrows):
        
        if rownum == 0:
            header_values = sh.row_values(rownum)
            
        else:
            sample = OrderedDict()
            row_values = sh.row_values(rownum)
            
            for i in range (len(header_values)):
                sample[header_values[i]] = row_values[i]
            samples_list.append(sample)
    # Serialize the list of dicts to JSON
    j = json.dumps(samples_list)

    return j




