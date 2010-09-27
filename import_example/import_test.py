#!/usr/bin/env python

import xlrd
from hdf import Hdf5
from decimal import Decimal as d
from numpy import array
import os

 
def import_to_hdf(name):
    ''' This import is limited to a simplified version of the Janes et. al
    paper

    '''
    if os.path.exists('project.hdf5'):
        os.remove('project.hdf5')
    hdf = Hdf5('project')
    group_name = 'Project Data'
    nr_in_vars = 7
    book = xlrd.open_workbook(name, encoding_override='utf8')
    sheet = book.sheet_by_index(0)

    # get the dimension labels
    dimension_labels = list()
    row_content_1 = sheet.row_values(0) # Measurement method
    row_content_2 = sheet.row_values(1) # Protein
    for col_index, cell in enumerate(row_content_2):
        dimension_labels.append(cell)
        if not row_content_1[col_index] == '':
            dimension_labels[-1] += ' (' + row_content_1[col_index]+ ')'
    variables = dimension_labels[:nr_in_vars]
    variables.append('measurements')
    
    data = list()
    dep_data = list()
    holes = list()
    dependent_vars = list()

    # get the data and the holes (empty cells)
    for row_nr, row in enumerate(xrange(2, sheet.nrows)):
        data.append(list())
        dep_data.append(list())
        holes.append(list())
        dependent_vars.append(list())
        row_content = sheet.row_values(row)
        for col_index, cell in enumerate(row_content):
            if cell == "":
                holes[row_nr].append(col_index)
            else:
                data[row_nr].append(d(str(cell)))
                dependent_vars[row_nr].append(col_index)
                if (col_index >= nr_in_vars):
                    dep_data[row_nr].append(d(str(cell)))

    lastline = 0
    size = list()
    for index, hole_line in enumerate(holes[1:]):
        if hole_line == holes[index] and not index == len(holes) - 2:
            continue
    indices = dict()
    for var in variables[:-1]: 
        indices[var] = list()
    indices['measurements'] = list()
    location = dict()
    dims = list()
    name = hdf.add_sdcube(variables, name=group_name)
    for index, dependent_vars_line in enumerate(dependent_vars[1:]):
        if dependent_vars_line == dependent_vars[index] and not index ==\
                len(dependent_vars) - 1:
            for var in variables[:-1]: 
                indices[var].append(data[index][variables.index(var)])
            indices['measurements'] = dependent_vars_line[nr_in_vars:]
            continue
        for var in variables[:-1]: 
            indices[var].append(data[index][variables.index(var)])
        indices['measurements'] = dependent_vars[index][nr_in_vars:]

        # We only need the unique indices TODO is this correct?
        for var in variables[:-1]: 
            noDupes = []
            [noDupes.append(i) for i in indices[var] if not noDupes.count(i)] 
            indices[var] = noDupes
            location[var] = indices[var][0]
            dims.append(len(indices[var]))
        location['measurements'] = indices['measurements'][0]
        dims.append(len(indices['measurements']))

        size.append((nr_in_vars, index + 1 - lastline,
            len(dependent_vars[index])))
        sdcube = hdf.get_sdcube(name)

        sdcube.create_dataset(indices)
        sdcube.set_data(location, array(dep_data[lastline :index +
            1], dtype=float).reshape(dims))
        for var in variables[:-1]: 
            indices[var] = list()
        indices['measurements'] = list()
        dims = list()
        lastline = index + 1
   
if __name__ == '__main__':
    import_to_hdf('simple_example.xls')

