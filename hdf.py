#!/usr/bin/env python

from __future__ import with_statement
import h5py
from numpy import random, ndarray
import cPickle as pickle
import os

class hdf5:
    """Class for creating a hdf5 datacube with associated metadata.
    The metadata is referred to as mapping and is used to map the 
    data indices to the real indices in the hdf cube.

    """
    def __init__(self, projectname):
        self.name = projectname
        self.filename = projectname + '.hdf5'

    def create(self, dset_name, *data):
        """ Creates the mapping, pickles it and then creates a hdf5 
        project. Remember to close the file after using.

        """
        mapping = dict((k , [i, v]) for i, (k, v) in enumerate(data))
        print mapping

        dims = []
        for k, v in data:
            dims.append(len(v))
        f = h5py.File(self.filename, 'w')
        self.dset = f.create_dataset(dset_name, dims)
        self.dset.attrs['mapping'] = pickle.dumps(mapping)
        return f, self.dset
       
    def index(self, key, value, mapping=None):
        """ Returns the mapped index of the key within the hdf data
        cube and the index of the value within that.
        
        """
        if not mapping:
            mapping = self.read_mapping()
        return mapping[key][0], mapping[key][1].index(value)

    def read_mapping(self, dset_name='Project Data', filename=None):
        """ Returns the mapping of the dimension from the given file 
        and datset

        """
        if not filename:
            filename = self.filename
        hdf5_file = h5py.File(filename,'r')
        return pickle.loads(str(hdf5_file[dset_name].attrs['mapping']))

    def visitAllObjects(self, group, path):
        """ Returns the file info for every dataset in the hdf5 file
        The file info consists of the shape (the dimensions) and the
        datatype (float[32,64],int32, string etc.)

        """
        info = {}

        for i in group.items():
            if isinstance(i[1],h5py.Group):
                visitAllObjects(i[1], os.path.join(path, i[0]))
            else:
                datasetName = os.path.join(path,i[0])
                info[datasetName] = (group[datasetName].shape,
                        group[datasetName].dtype) 

        return info 
    
    def get_data(self, items, dset_name='Project Data',
            filename=None):
        """ Gathers and return the data from every hdf File.
        The data is stored in a dict of numpy ndarrays

        """
        if not filename:
            filename = self.filename
        with h5py.File(filename,'r') as hdf5_file:
            file_info = self.visitAllObjects(hdf5_file, '')
            data = {}
            for dataset in file_info.keys():
                values = file_info[dataset][0]
                value_type = file_info[dataset][1]
                data[dataset] = ndarray(values, dtype=value_type)
                data[dataset] = hdf5_file[dataset].value
        
            indices = [slice(None, None, None)] * len(data[dset_name].shape)
            for k, v in items.iteritems():
                dim, index = self.index(k, v)
                indices[dim] = index
            
            hdf5_file.close()
            return data[dset_name][tuple(indices)]

if __name__ == "__main__":
    h = hdf5('project')
    f, dset = h.create('Project Data', ['first',[1, 2, 7.0]], ['second',['a', 'b', 'c']],
            ['test',[1.0, 2.0, 3.0]], ['another',[1, 2.0, '3', 4]])
    h.dset[...] = 2 + 2 * random.random(dset.shape)
    f.close()
    print h.get_data({'test':3.0, 'another':1, 'second':'c'})
