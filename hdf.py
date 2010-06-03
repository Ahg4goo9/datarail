#!/usr/bin/env python

''' This file contains the classes Hdf5 and function

'''

from __future__ import with_statement
import h5py
import cPickle as pickle
import os
import os.path
import logging
from numpy import array, nan, empty

class Hdf5:
    ''' Class for creating a hdf5 datacube with associated metadata.
    The metadata is referred to as mapping and is used to map the 
    data indices to the real indices in the hdf cube.

    '''
    def __init__(self, projectname):
        self.name = projectname
        self.filename = projectname + '.hdf5'
        logging.basicConfig( format='%(asctime)s %(levelname)s\
                %(message)s', level=logging.DEBUG)
        logging.info('Try using an existing: %s' % self.filename)
        if not os.path.exists(self.filename):
            logging.info('Creating file: %s' % self.filename)
            with h5py.File(self.filename, 'w') as hdf5_file:
                # No functions yet
                hdf5_file.attrs['functions'] = pickle.dumps([])
                logging.info('Created file:' + self.filename)

    def create_dataset(self, dset_name, *dimensions):
        ''' Create the mapping and pickle it. 
        Load the group named like the dataset or create it if it is not
        present.

        '''

        group_mapping = dict((k, i) for i, (k, v) in enumerate(dimensions))
        dset_mapping = dict(([i, v]) for i, (k, v) in enumerate(dimensions))
        
        dims = []
        for key, value in dimensions:
            dims.append(len(value))

        with h5py.File(self.filename, 'a') as h5_file:
            logging.info('Load group: %s' % dset_name)
            try:
                group = h5_file[dset_name]
                if not group_mapping == self.read_mapping(group):
                    logging.error('The dimensions of the new and the old'\
                            'dataset must be the same')
                    raise ValueError('The dimensions of the new and the old'\
                            'dataset must be the same')
            except KeyError:
                logging.info('Failed to load group: %s' % dset_name)
                logging.info('Creating group: %s' % dset_name)
                group = h5_file.create_group(dset_name)

            # check if there already is a dataset and if the number 
            # of dimensions is equal to the new one '''
            if group.keys():
                if not len(group[group.keys()[0]].shape) == len(dims):
                    logging.error('The new dataset has the wrong number of'\
                            'dimensions: %s' % self.filename)
                    raise ValueError('The dataset has the wrong number of'\
                    'dimensions')
                for key in group.keys():
                    mapping = pickle.loads(group[key].attrs['mapping'])
                    
                    share_points = True
                    for key in mapping:
                        if not [x for x in mapping[key] if x in
                                dset_mapping[key]]:
                            share_points = False
                if share_points:
                    logging.error('The new dataset shares some datapoints '\
                             'with at least one existing dataset. Aborting'\
                             'insert.')
                    raise ValueError('The new dataset shares some datapoints'\
                            'with an existing dataset')
                    
            logging.info('Creating dataset: ' + dset_name)
            dset = group.create_dataset(str(len(group.keys())), dims)
            dset.attrs['mapping'] = pickle.dumps(dset_mapping)
            group.attrs['dirty'] = True
            group.attrs['mapping'] = pickle.dumps(group_mapping)
            logging.info('Dataset created.')
    
    def set_dataset(self, group_name, indices, data):
        ''' Search for the right cube in the group and check if the
        data fits into the cube at the given coordinates.
        Set the data for that given cube.

        '''
        logging.info('Setting data in: ' + group_name)

        with h5py.File(self.filename) as h5_file:
            group = h5_file[group_name]
            if not len(indices) == len(data.shape):
                logging.error('Please specify a single point')
                raise ValueError('Please specify a single point')

            group_mapping = pickle.loads(group.attrs['mapping'])
            for key in indices.keys():
                if not key in group_mapping.keys():
                    logging.error('Index not in mapping.')
                    raise ValueError('Index not in mapping.')

            ind = [slice(None, None, None)]*len(data.shape)
            for dimindex, dim_length in enumerate(data.shape):
                ind[dimindex] = slice(0, dim_length, 1)
            
            for dset in group.values():
                dataset_valid = True
                for key, value in indices.iteritems():
                    index = self.index(group_mapping[key], value, dset)
                    if index == -1:
                        dataset_valid = False
                        break 
                    ind[group_mapping[key]] = slice(index, index +
                            data.shape[group_mapping[key]], None)
                if not dataset_valid:
                    continue 
                destination_dset = dset
                break #dataset found
            if not dataset_valid:
                logging.error('No valid dataset found.')
                raise ValueError('No valid dataset found.')

            for dim_index, dim_length in enumerate(data.shape):
                if dim_length > destination_dset.shape[dim_index]:
                    logging.error('The given data is too big for the'\
                    'dataset.')
                    raise ValueError('The given data is too big.')
            ind = tuple(ind)
            destination_dset[ind] = data
            group.attrs['dirty'] = True
            logging.info('Data set.')
       
    def index(self, key, value, dset):
        ''' Returns the mapped index of the key within the hdf data
        cube and the index of the value within that.
        
        '''
        mapping = self.read_mapping(dset)
        if value in mapping[key]:
            return mapping[key].index(value)
        return -1

    def read_mapping(self, h5_element):
        ''' Returns the mapping of the element

        '''
        return pickle.loads(str(h5_element.attrs['mapping']))

    def visit_all_objects(self, group, path):
        ''' Returns the file info for every dataset in the group.
        The file info consists of the shape (the dimensions) and the
        datatype (float[32,64],int32, string etc.)

        '''
        info = {}
        for i in group.items():
            if isinstance(i[1], h5py.Group):
                self.visit_all_objects(i[1], os.path.join(path, i[0]))
            else:
                dataset_name = os.path.join(path, i[0])
                #dataset_name = i[0] 
                info[dataset_name] = (group.file[dataset_name].shape,
                        group.file[dataset_name].dtype) 
        return info 
    
    def get_possible_indices(self, group_name):
        '''Get all indices from all different datasets within the group.
        Return them as a list compatible with create_dataset.

        '''
        with h5py.File(self.filename,'r') as hdf5_file:
            group = hdf5_file[group_name]
            group_mapping = self.read_mapping(group)
            indices = dict.fromkeys(group_mapping.values())
            for dset in group.values():
                mapping = self.read_mapping(dset)
                for index, values in mapping.items():
                    for value in values:
                        try:
                            indices[index].index(value)
                        except ValueError:
                            indices[index].append(value)
                        except AttributeError:
                            indices[index] = [value]

        reverse_grp_map = dict((v,k) for k,v in group_mapping.iteritems())
        indices_list = []
        for i in xrange(len(indices.keys())):
            indices_list.append([reverse_grp_map[i], indices[i]])
        return indices_list 
   
    def get_data_fill_with_nan(self, group_name, items):
        ''' Create one data_set out of the multiple data_sets get_data
        returns. Fill all gaps with NaNs.

        '''

        indices = self.get_possible_indices(group_name)
        start_point = dict(([k, v[0]]) for (k, v) in indices)
        shape = tuple(len(v) for (k, v) in indices)
        dsets, inds = self.get_data(group_name, items)
        for dset in dsets:
            print '-' *50
            print dset
            print '-' *50
        print inds
        tmp_name = group_name + '.tmp'
        self.create_dataset(tmp_name, *indices)
        nan_array = empty(shape)
        nan_array[:] = nan
        hdf.set_dataset(tmp_name, start_point, nan_array)
        return dsets

    def get_data(self, group_name, items):
        ''' Gathers and return the data of the group.
        The data is stored in a dict of numpy ndarrays.

        '''
        with h5py.File(self.filename,'r') as hdf5_file:
            #file_info = self.visit_all_objects(hdf5_file, '')
            data = {}
            indices = {}

            group = hdf5_file[group_name]
            for dataset in group.values():
                shape = dataset.shape
                data[dataset.name] = dataset[...]
                group_mapping = self.read_mapping(group)
                indices[dataset.name] = [slice(None, None, None)] * len(shape)
                for key, value in items.iteritems():
                    index = self.index(group_mapping[key], value, dataset)
                    indices[dataset.name][group_mapping[key]] = index
                #if not -1 in indices:
                    #break
                if -1 in indices:
                    del data[dataset.name]
                    del indices[dataset.name]
            return_data = []
            for key, value in data.items():
                return_data.append(array(value[tuple(indices[key])]))

            return return_data, indices
            #return value[tuple(indices[key])]
            #return data[dataset.name][tuple(indices[dataset.name])]

    def add_function(self, func):
        ''' Add a function <-> cube mapping. 

        '''
        if func.name == "" or \
                not func.input_cubes or \
                not func.output_cubes:
            raise ValueError('name, input_dsets and output_dsets must not be'\
                    'empty')
        with h5py.File(self.filename,'a') as hdf5_file:
            functions = pickle.loads(str(hdf5_file.attrs['functions']))
            functions.append(func)
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
        with h5py.File(self.filename, 'r') as hdf5_file:
            return pickle.loads(str(hdf5_file.attrs['functions']))

    def execute_function(self, func):
        ''' Executes a function and set the output dataset status to dirty.

        '''
#TODO make me work for non python functions
        import sys
        logging.info('Importing the function: %s' % func)
        __import__(func.name)
        func_class = sys.modules[func.name]
        with h5py.File(self.filename, 'a') as h5_file:
            input_cubes = []
            for input_cube_name in func.input_cubes:
                input_cubes.append(h5_file[input_cube_name])
            output_cubes = []
            logging.info('Executing the function: %s' % func)
            func_class.function(input_cubes, func.output_cubes,
                    func.params)
            for output_cube_name in output_cubes:
                logging.info('Set the dirty status for the output datasets')
                h5_file[output_cube_name].attrs['dirty'] = True

    def recompute(self):
        ''' Look for all functions with dirty(changed) datasets.
        Then execute those functions and remove the dirty state.

        '''
        dirty_funcs = []
        with h5py.File(self.filename, 'r') as hdf5_file:
            logging.info('Collecting all functions containing dirty datasets')
            for func in self.get_functions():
                for dset in func.input_dsets:
                    if hdf5_file[dset].attrs['dirty']:
                        dirty_funcs.append(func)
        for func in set(dirty_funcs):
            logging.info('Execute all functions with dirty datasets')
            self.execute_function(func)
        with h5py.File(self.filename, 'a') as hdf5_file:
            logging.info('Remove the dirty state from alle datasets')
            for func in dirty_funcs:
                for dset in func.input_dsets:
                    hdf5_file[dset].attrs['dirty'] = False
                for dset in func.output_dsets:
                    hdf5_file[dset].attrs['dirty'] = False

if __name__ == '__main__':
    from numpy import random, arange
    from decimal import Decimal as d
    os.remove('project.hdf5')
    hdf = Hdf5('project')
    group_name = 'Project Data'
    hdf.create_dataset(group_name, ['first',[d('1'), d('2'), d('7.0')]],
            ['second',['a', 'b', 'c']], ['test',[d('1.0'), d('2.0'), d('3.0')]],
            ['another',[d('1'), d('2.0'), '3', d('4')]])
    hdf.create_dataset(group_name, ['first',[d('10'), d('20'), d('70.0')]],
            ['second',['a', 'b', 'c']], ['test',[d('1.0'), d('2.0'), d('3.0')]],
            ['another',[d('1'), d('2.0'), '3', d('4')]])
    hdf.create_dataset(group_name, ['first',[d('80')]], ['second',['a', 'b',
        'c']], ['test',[d('1.0')]], ['another',[d('1'), d('2.0'), '3', d('4')]])
    with h5py.File(hdf.filename) as hdf5_file:
        group = hdf5_file[group_name]
        hdf.set_dataset(group_name, {'first':d('1'), 'second':'a',
            'test':d('1.0'), 'another':1}, 2 + 2 *
            random.random(hdf5_file[group_name]['0'].shape))
        length = 1
        for dim in group['0'].shape:
            length = length * dim
        hdf.set_dataset(group_name, {'first':d('1'), 'second':'a',
            'test':d('1.0'), 'another':1},
            arange(length).reshape(group['0'].shape))
        hdf5_file.copy(group_name, 'ds')
    hdf.set_dataset('ds', {'first':d('1'), 'second':'a', 'test':d('1.0'),
        'another':1}, arange(length).reshape((d('3'),d('3'),d('3'),4)))
    hdf.set_dataset(group_name, {'first':d('1'), 'second':'a', 'test':d('1.0'),
        'another':1}, arange(length).reshape((d('3'),d('3'),d('3'),4)))
    hdf.set_dataset(group_name, {'first':d('1'), 'second':'b', 'test':d('1.0'),
        'another':1}, 10*arange(2*1*2*4).reshape((d('2'), d('1'), d('2'), 4)))
    hdf.set_dataset(group_name, {'first':d('10'), 'second':'b',
        'test':d('1.0'),'another':1},
        10*arange(2*1*2*4).reshape((d('2'), d('1'), d('2'), 4)))
    #print hdf.get_data(group_name, {'test':d('2.0'), 'another':1})
    #print hdf.get_data(group_name, {'first':d('10')})
    for data_set in hdf.get_data_fill_with_nan(group_name, {}):
        pass
        #print data_set
        #print data_set.shape


class Function:
    def __init__(self, name, params, input_cubes, output_cubes):
        '''
        The name should be the relative path to hdf.py
        It also executes the function.

        '''
        self.name = name
        self.params = params
        self.input_cubes = input_cubes
        self.output_cubes = output_cubes

    def __str__(self):
        output = {self.name: [self.params, self.input_cubes,
            self.output_cubes]}
        return str(output)

