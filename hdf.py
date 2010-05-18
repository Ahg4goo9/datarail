#!/usr/bin/env python

from __future__ import with_statement
import h5py
import cPickle as pickle
import os
from numpy import ndarray

class hdf5:
    '''Class for creating a hdf5 datacube with associated metadata.
    The metadata is referred to as mapping and is used to map the 
    data indices to the real indices in the hdf cube.

    '''
    def __init__(self, projectname):
        self.name = projectname
        self.filename = projectname + '.hdf5'
        with h5py.File(self.filename, 'w') as f:
            f.attrs['functions'] = pickle.dumps([]) # No functions yet

    def create_dataset(self, dset_name, *dimensions):
        ''' Creates the mapping, pickles it and then creates a hdf5 
        project. Remember to close the file after using.
        It returns the filehandler and the dataset.

        '''
        mapping = dict((k , [i, v]) for i, (k, v) in enumerate(dimensions))

        dims = []
        for k, v in dimensions:
            dims.append(len(v))
        with h5py.File(self.filename, 'a') as f:
            dset = f.create_dataset(dset_name, dims)
            dset.attrs['mapping'] = pickle.dumps(mapping)
            dset.attrs['dirty'] = True
    
    def set_dataset(self, dset_name, data):
        with h5py.File(self.filename) as f:
            f.get(dset_name)[...] = data
            f.get(dset_name).attrs['dirty'] = True
       
    def index(self, key, value, dset_name):
        ''' Returns the mapped index of the key within the hdf data
        cube and the index of the value within that.
        
        '''
        mapping = self.read_mapping(dset_name)
        return mapping[key][0], mapping[key][1].index(value)

    def read_mapping(self, dset_name):
        ''' Returns the mapping of the dimension from the given file 
        and datset

        '''
        with h5py.File(self.filename, 'r') as hdf5_file:
            return pickle.loads(str(hdf5_file[dset_name].attrs['mapping']))

    def visitAllObjects(self, group, path):
        ''' Returns the file info for every dataset in the hdf5 file
        The file info consists of the shape (the dimensions) and the
        datatype (float[32,64],int32, string etc.)

        '''
        info = {}

        for i in group.items():
            if isinstance(i[1],h5py.Group):
                visitAllObjects(i[1], os.path.join(path, i[0]))
            else:
                datasetName = os.path.join(path,i[0])
                info[datasetName] = (group[datasetName].shape,
                        group[datasetName].dtype) 

        return info 
    
    def get_data(self, items, dset_name):
        ''' Gathers and return the data of the dataset.
        The data is stored in a dict of numpy ndarrays

        '''
        with h5py.File(self.filename,'r') as hdf5_file:
            file_info = self.visitAllObjects(hdf5_file, '')
            data = {}
            for dataset in file_info.keys():
                values = file_info[dataset][0]
                value_type = file_info[dataset][1]
                data[dataset] = ndarray(values, dtype=value_type)
                data[dataset] = hdf5_file[dataset].value
        
            indices = [slice(None, None, None)] * len(data[dset_name].shape)
            for k, v in items.iteritems():
                dim, index = self.index(k, v, dset_name)
                indices[dim] = index
            
            hdf5_file.close()
            return data[dset_name][tuple(indices)]

    def add_function(self, function):
        ''' Add a function <-> cube mapping. 

        '''
        if function.name == "" or \
                not function.input_dsets or \
                not function.output_dsets:
            raise ValueError('name, input_dsets and output_dsets must not be\
                    empty')
        with h5py.File(self.filename,'a') as hdf5_file:
            functions = pickle.loads(str(hdf5_file.attrs['functions']))
            functions.append(function)
            hdf5_file.attrs['functions'] = pickle.dumps(functions)

    def del_function(self, function):
        ''' Remove a function <-> cube mapping from the project.

        '''
        with h5py.File(self.filename,'a') as hdf5_file:
            functions = pickle.loads(str(hdf5_file.attrs['functions']))
            # can't prove for object equality so iterate over all functions
            for func in functions:
                if str(func) == str(function):
                    functions.remove(func)
            hdf5_file.attrs['functions'] = pickle.dumps(functions)

    def get_functions(self):
        ''' Returns all function <-> cube mappings from the project

        '''
        with h5py.File(self.filename,'r') as hdf5_file:
            return pickle.loads(str(hdf5_file.attrs['functions']))

    def execute_function(self, function):
        ''' Executes a function and set the output dataset status to dirty.
        
        '''
        import os.path
        import os
        import sys
        path = os.path.join(os.getcwd(), *function.name.split('/')[:-1])
        sys.path.append(path)
        import_func = function.name.split('/')[-1].split('.')[0]
        func_class = __import__(import_func)
        with h5py.File(self.filename, 'a') as f:
            input_cubes = []
            for input_cube_name in function.input_dsets:
                input_cubes.append(f.get(input_cube_name))
            output_cubes = []
            func_class.function(input_cubes, function.output_dsets,
                    function.params)
            for output_cube_name in output_cubes:
                f.get(output_cube_name).attrs['dirty'] = True

    def recompute(self):
        ''' Look for all functions with dirty(changed) datasets.
        Then execute those functions and remove the dirty state.

        '''
        dirty_funcs = []
        with h5py.File(self.filename, 'r') as f:
            for func in self.get_functions():
                for dset in func.input_dsets:
                    if f.get(dset).attrs['dirty']:
                        dirty_funcs.append(func)
        for func in set(dirty_funcs):
            self.execute_function(func)
        with h5py.File(self.filename, 'a') as f:
            for func in dirty_funcs:
                for dset in func.input_dsets:
                    f.get(dset).attrs['dirty'] = False
                for dset in func.output_dsets:
                    f.get(dset).attrs['dirty'] = False


class function:
    def __init__(self, name, params, input_dsets, output_dsets):
        '''
        The name should be the relative path to hdf.py
        It also executes the function.

        '''
        self.name = name
        self.params = params
        self.input_dsets = input_dsets
        self.output_dsets = output_dsets

    def __str__(self):
        output = {self.name: [self.params, self.input_dsets,
            self.output_dsets]}
        return str(output)

