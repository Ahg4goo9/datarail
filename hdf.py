#!/usr/bin/env python

''' This file contains some useful functions to manipulate hdf objects.
It also contains the classes Hdf5 and sdcube

'''

from __future__ import with_statement
import h5py
import cPickle as pickle
import os
import logging

def is_sequential(elements):
    ''' Return whether a list or a tuple is sequential

    '''
    for i, dim_index in enumerate(sorted(elements)):
        if i != dim_index:
            return False
    return True
    
def storeMapping(h5_elem, mapping):
    ''' Calls store_attribute to save a mapping as an attribute in the
    h5_element.
        
    '''
    store_attribute(h5_elem, 'mapping', mapping)

def store_attribute(h5_elem, attribute_name, attribute):
    ''' Stores an attribute in the h5 element.

    '''
    h5_elem.attrs[attribute_name] = pickle.dumps(attribute)

def load_mapping(h5_elem):
    ''' Calls load_attribute to load a mapping from the h5_element.
        
    '''
    return load_attribute(h5_elem, 'mapping')

def load_attribute(h5_elem, attribute_name):
    ''' Loads an attribute from the h5 element.

    '''
    return pickle.loads(str(h5_elem.attrs[attribute_name]))

class Hdf5:
    ''' Class for creating a hdf5 datacube with associated metadata.
    The metadata is referred to as mapping and is used to map the 
    data indices to the real indices in the hdf cube.

    '''
    def __init__(self, projectname):
        self.name = projectname
        self.filename = projectname + '.hdf5'
        logging.basicConfig( format='%(asctime)s %(levelname)s\
                %(message)s', level=logging.ERROR)
        logging.info('Try using an existing: %s' % self.filename)
        if not os.path.exists(self.filename):
            logging.info('Creating file: %s' % self.filename)
            with h5py.File(self.filename, 'w') as h5_file:
                # No functions yet
                h5_file.attrs['functions'] = pickle.dumps([])
                h5_file.attrs['sdcubes'] = pickle.dumps({})
                logging.info('Created file:' + self.filename)

    def get_sdcube(self, name):
        ''' Load the sdcube with the name name. 
        If filename is not given assume the sdcube is in the project file.

        '''
        with h5py.File(self.filename, 'r') as h5_file:
            sdcubes = load_attribute(h5_file, 'sdcubes')
        return SdCube.load(sdcubes[name], name)
    
    def add_sdcube(self, mapping, name=None):
        ''' Add an sd cube to the project. Return the created name and the
        filename.

        '''
        with h5py.File(self.filename, 'r') as h5_file:
            sdcubes = load_attribute(h5_file, 'sdcubes')
            if name in sdcubes:
                logging.error('A group with the name %s alread exists' % name)
                raise KeyError('A group with the name %s alread exists' % name)
            for key in sdcubes:
                if name.lower() == key:
                    raise Warning('%s looks like %s!' % (name, key))
        if not name:
            name = str(len(sdcubes)) #name will be a number
        
        filename = self.filename


        SdCube(name, filename, mapping)
        with h5py.File(self.filename, 'a') as h5_file:
            sdcubes = load_attribute(h5_file, 'sdcubes')
            sdcubes[name] = filename
            store_attribute(h5_file, 'sdcubes', sdcubes)
            store_attribute(h5_file[name], 'dirty', True)
        return name

    def delete_cube(self, group_name):
        ''' Delete a sdcube from the project

        '''
        logging.info('Try to delete: %s' % group_name)
        with h5py.File(self.filename, 'a') as h5_file:
            try:
                sdcubes = load_attribute(h5_file, 'sdcubes')
                del sdcubes[group_name]
                del h5_file[group_name]
                logging.info('Deleted: %s' % group_name)
            except KeyError: #change the error text and log
                logging.error('Unable to delete the group %s' % group_name)
                raise KeyError('Unable to delete the group %s' % group_name)
    def add_function(self, func):
        ''' Add a function to the project

        '''
        if func.name == "" or \
                not func.input_cube_names or \
                not func.output_cube_names:
            raise ValueError('name, input_dsets and output_dsets must not be'
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
            # can't test for object equality so iterate over all functions
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
        logging.info('Importing the function: %s' % func)
        with h5py.File(self.filename, 'a') as h5_file:
            input_cubes = []
            for input_cube_name in func.input_cube_names:
                input_cubes.append(h5_file[input_cube_name])
            logging.info('Executing the function: %s' % func)
            func.__call__(input_cubes, func.output_cube_names,
                    func.params)
            sdcubes = load_attribute(h5_file, 'sdcubes')
            for output_cube_name in func.output_cube_names:
                sdcubes[output_cube_name] = self.filename
                logging.info('Set the dirty status for the output datasets')
                h5_file[output_cube_name].attrs['dirty'] = True
            store_attribute(h5_file, 'sdcubes', sdcubes)

    def recompute(self):
        ''' Look for all functions with dirty(changed) datasets.
        Then execute those functions and remove the dirty state.

        '''
        dirty_funcs = []
        with h5py.File(self.filename, 'r') as hdf5_file:
            logging.info('Collecting all functions containing dirty datasets')
            for func in self.get_functions():
                for dset in func.input_cube_names:
                    if hdf5_file[dset].attrs['dirty']:
                        dirty_funcs.append(func)
        for func in set(dirty_funcs):
            logging.info('Execute all functions with dirty datasets')
            self.execute_function(func)
        with h5py.File(self.filename, 'a') as hdf5_file:
            logging.info('Remove the dirty state from alle datasets')
            for func in dirty_funcs:
                for dset in func.input_cube_names:
                    hdf5_file[dset].attrs['dirty'] = False
                for dset in func.output_cube_names:
                    hdf5_file[dset].attrs['dirty'] = False

class SdCube(object):
    ''' A SdCube is a h5py group with a mapping attached
    It has a list with the containing datasets and another list with the
    mapping for each containing dataset.

    '''

    def __init__(self, name, filename, dim_labels, units=[]):
        ''' Create a group with the name in an hdf5 file.
        If the group existed in the file before delete it.

        '''
        mapping = dict([dim, i] for i, dim in enumerate(dim_labels))
        if not is_sequential(mapping.values()):
            logging.error('Dimensions must be sequently.')
            raise ValueError('Dimensions must be sequently.')
        if units and not len(mapping) == len(units):
            logging.error('The number of units is not equal to the number of'
                    ' dimensions.')
            raise ValueError('The number of units is not equal to the number'
            ' of dimensions.')
        self.name = name
        self.filename = filename
        with h5py.File(self.filename, 'a') as h5_file:
            try:
                logging.info('Group created.')
                self.grp = h5_file.create_group(name)
                storeMapping(self.grp, mapping)
                store_attribute(self.grp, 'units', units)
            except ValueError:
                logging.info('Group already exists.')
    
    @classmethod
    def load(cls, filename, group_name, units=[]):
        ''' Load an existing SdCube from an hdf5 file.

        '''
        if not os.path.exists(filename):
            logging.error('The SdCube does not exist.')
            raise ValueError('The SdCube does not exist.')
        with h5py.File(filename, 'r') as h5_file:
            try:
                # The first key should the name of the group
                group = h5_file[group_name]
                mapping = load_mapping(group)
            except KeyError:
                logging.error('The file seems to be invalid.')
                raise KeyError('The file seems to be invalid.')
        return(cls(group_name, filename, mapping, units))

    @property
    def group(self):
        ''' Return the group.

        '''
        with h5py.File(self.filename, 'r') as h5_file:
            return h5_file[self.name]

    @property
    def unit_mapping(self):
        ''' Return the unit mapping for the group.

        '''
        with h5py.File(self.filename, 'r') as h5_file:
            return load_attribute(h5_file[self.name], 'units')

    @unit_mapping.setter
    def unit_mapping(self, value):
        ''' Set the unit_mapping to value if the length of value is equal to
        the number of dimensions of the group.

        '''
        if not len(value) == len(self.mapping):
            logging.error('The number of units must be equal to the number of'
            ' dimensions')
            raise ValueError('The number of units must be equal to the number'
            ' of dimensions')
        with h5py.File(self.filename, 'a') as h5_file:
            store_attribute(h5_file[self.name],'units',  value)
    
    @property
    def mapping(self):
        ''' Return the mapping for the group.
            
        '''
        with h5py.File(self.filename, 'r') as h5_file:
            return load_mapping(h5_file[self.name])

    @mapping.setter
    def mapping(self, value):
        ''' The the mapping of the group if the value is sequential and starts
        at the dimension index 0. E.g.
        {'x':0, 'y':1} would be valid, {'x':1, 'y':2} or {'x':0, 'y':2} are
        not.

        '''
        if not is_sequential(value.values()):
            logging.error('Dimensions must be sequently.')
            raise ValueError('Dimensions must be sequently.')
        with h5py.File(self.filename, 'a') as h5_file:
            storeMapping(h5_file[self.name], value)

    def create_dataset(self, dimensions):
        ''' Create a dataset within the SdCube

        '''
        if not dimensions:
            logging.error('Dimension must not be empty')
            raise ValueError('Dimension must not be empty')
        group_mapping = self.mapping
        if not dimensions.keys() == self.mapping.keys():
            logging.error('The dataset must have the same dimension labels as'
                    ' the old dataset.')
            raise ValueError('The dataset must have the same dimension labels'
                    ' as the old dataset.')
        dset_mapping = dict()
        dims = [[]] * len(group_mapping)
        for dim_label, dim_index in group_mapping.items():
            dset_mapping[dim_index] = dimensions[dim_label]
            dims[dim_index] = len(dimensions[dim_label])
        #for dim_label, index_labels in dimensions.items():
        #    dset_mapping[group_mapping[dim_label]] = index_labels
        #dset_mapping = dict([i, v] for i, (k, v) in enumerate(dimensions))
        #dims = [len(value) for value in dimensions.values()]

        with h5py.File(self.filename, 'a') as h5_file:
            grp = h5_file[self.name]
            # check if there already is a dataset and if the number 
            # of dimensions is equal to the new one '''
            if grp.keys():
                if not len(grp[grp.keys()[0]].shape) == len(dims):
                    logging.error('The new dataset has the wrong number of'
                            'dimensions: %s' % self.filename)
                    raise ValueError('The dataset has the wrong number of'
                    'dimensions')
                for key in grp.keys():
                    mapping = load_mapping(grp[key])
                    share_points = True
                    for key in mapping:
                        if not [x for x in mapping[key] if x in
                                dset_mapping[key]]:
                            share_points = False
                if share_points:
                    logging.error('The new dataset shares some datapoints '
                             ' with at least one existing dataset. Aborting'
                             ' insert.')
                    raise ValueError('The new dataset shares some datapoints'
                            ' with an existing dataset')
                    
            logging.info('Creating dataset: ' + self.name)
            # the dset name is just the next available number
            dset = grp.create_dataset(str(len(grp.keys())), dims)
            dset.attrs['mapping'] = pickle.dumps(dset_mapping)
            grp.attrs['dirty'] = True
            grp.attrs['mapping'] = pickle.dumps(group_mapping)
            logging.info('Dataset created.')

    def set_data(self, location, data):
        ''' Search for the right cube in the group and check if the
        data fits into the cube at the given location.
        Set the data for that given cube.

        '''
        logging.info('Setting data in: ' + self.name)

        with h5py.File(self.filename) as h5_file:
            grp = h5_file[self.name]
            group_mapping = self.mapping
            if not len(location) == len(group_mapping.keys()):
                logging.error('Please specify a single point')
                raise ValueError('Please specify a single point')

            if not len(location) == len(data.shape):
                logging.error('data should have as many dimensions as the '
                        'dataset')
                raise ValueError('data should have as many dimensions as the '
                        'dataset')
            for key in location.keys():
                if not key in group_mapping.keys():
                    logging.error('Index not in mapping.')
                    raise ValueError('Index not in mapping.')
            
            destination_dset, ind = self.__get_dataset_with_indices(grp,
                    location, data)
            if not destination_dset:
                logging.error('No valid dataset found.')
                raise ValueError('No valid dataset found.')

            for dim_index, dim_length in enumerate(data.shape):
                if dim_length > destination_dset.shape[dim_index]:
                    logging.error('The given data is too big for the '
                    'dataset.')
                    raise ValueError('The given data is too big.')
            destination_dset[tuple(ind)] = data
            grp.attrs['dirty'] = True
            logging.info('Data set.')

    def __get_dataset_with_indices(self, grp, indices, data):
        ''' Find the dataset within the group grp that contains the indices.
        '''

        group_mapping = pickle.loads(grp.attrs['mapping'])
        ind = [slice(0, dim_length, 1) for dim_length in data.shape]
        destination_dset = None
        for dset in grp.values():
            dataset_valid = True
            for key, value in indices.iteritems():
                index = self.index(group_mapping[key], value, dset)
                if index == -1:
                    dataset_valid = False
                    break 
                ind[group_mapping[key]] = slice(index, index +
                        data.shape[group_mapping[key]], 1)
            if not dataset_valid:
                continue 
            destination_dset = dset
            break #dataset found
        return destination_dset, ind

    def index(self, dimension_index, index_label, dset):
        ''' Returns the mapped index of the index_label within the hdf 
        data cube and the index of the value within that.
        
        '''
        mapping = pickle.loads(str(dset.attrs['mapping']))
        if index_label in mapping[dimension_index]:
            return mapping[dimension_index].index(index_label)
        return -1
        
    def get_data(self, items={}):
        ''' Get the data that matches the items.
        '''
        # Do not return the first indices
        return self.get_data_and_indices(items)[0]

    def first_index_labels(self, dset, items):
        ''' Get the 'first' point of a given dataset.
        Return them as a list compatible with create_dataset.

        '''
        first_index_labels = {}
        try:
            mapping = pickle.loads(str(dset.attrs['mapping']))
        except AttributeError:
            with h5py.File(self.filename,'r') as h5_file:
                mapping = pickle.loads(str(h5_file[dset].attrs['mapping']))
        group_mapping = self.mapping
        for dim_label, index_label in items.items():
            mapping[group_mapping[dim_label]] = [index_label]
        reverse_grp_map = dict((v, k) for k, v in group_mapping.iteritems())
        for index, value in mapping.items():
            first_index_labels[reverse_grp_map[index]] = value[0]
        return first_index_labels

    def get_data_and_indices(self, items={}):
        ''' Get all datasets.
        Exclude those that don't match items.
        Return the remaining datasets and their first indices.

        '''
        with h5py.File(self.filename,'r') as hdf5_file:
            data = []
            inds = []
            first_inds = []

            grp = hdf5_file[self.name]
            for dataset in grp.values():
                shape = dataset.shape
                data.append(dataset[...])
                inds.append([slice(None, None, None)] * len(shape))
                first_inds.append(self.first_index_labels(dataset, items))
                for dim_label, index_label in items.iteritems():
                    inds[-1][self.mapping[dim_label]] = \
                            self.index(self.mapping[dim_label], index_label,
                                    dataset)

            #prevent interation over datasets that do not match items
            data2 = list(data) 
            for i in xrange(len(data2) - 1, -1, -1):
                if -1 in inds[i]:
                    del data[i]
                    del inds[i]
                    del(first_inds[i])

            return_data = []
            for i, value in enumerate(data):
                shape = list(value.shape)
                for j, dim in enumerate(inds[i]):
                    if type(dim) == int:
                        shape[j] = 1
                return_data.append(value[tuple(inds[i])].reshape(shape))
            return return_data, first_inds
        
    """
    #TODO: make me work for sdcubes. It used to work within hdf
    def get_data_fill_with_nan(self, group_name, items):
        ''' Create one data_set out of the multiple data_sets get_data
        returns. Fill all gaps with NaNs.

        '''

        indices = self.get_all_possible_indices(group_name)
        for i, index in enumerate(indices):
            index_label = index[0]
            if index_label in items:
                indices[i] = [index_label, [items[index_label]]]
        start_point = dict(([k, v[0]]) for (k, v) in indices)
        shape = tuple(len(v) for (k, v) in indices)

        data, inds = self.get_data_and_indices(group_name, items)
        tmp_name = group_name + '.tmp'
        self.create_dataset(tmp_name, *indices)
        nan_array = empty(shape)
        nan_array[:] = nan
        self.set_dataset(tmp_name, start_point, nan_array)
        for i in xrange(len(inds)):
            self.set_dataset(tmp_name, inds[i], data[i])
        ret_data = self.get_data(tmp_name, items)
        self.delete_cube(tmp_name)
        return ret_data
    """

