import function
import numpy
import logging
import pickle

def calc_data(dset, method, collapse_dim):
    if method == "average":
        logging.info('Calculation data using average')
        return numpy.average(dset[...], collapse_dim)
    elif method == "max":
        logging.info('Calculation data using max')
        return numpy.amax(dset[...], collapse_dim)
    if method == "min":
        logging.info('Calculation data using min')
        return numpy.amin(dset[...], collapse_dim)
    else:
        logging.error('Unknown method')
        raise ValueError('Unknown method')

class CollapseDimension(function.Function):
    '''

    '''
    def __call__(self, input_cubes, output_cube_names, params):
        ''' Collapse one dimension of the input cube with a method given by
        params. Store the output cube in the correct hdf project.

        '''
        if not len(params) == 2:
            logging.error('Please give a dimension to collapse and a method')
            raise ValueError('Please give a dimension to collapse and a method')
        if not len(input_cubes) == 1:
            logging.error('Please give exactly one cube!')
            raise ValueError('Please give exactly one cube!')

        collapse_dim, method = params
        cube = input_cubes[0]
        mapping = function.get_mapping(cube)
        if not collapse_dim in mapping.values():
            logging.error('The collapse dimension is not in the input cube')
            raise ValueError('The collapse dimension is not in the input cube')

        out_mapping = dict()
        for key, value in mapping.items():
            if value < collapse_dim:     
                out_mapping[key] = value
            elif value > collapse_dim:
                out_mapping[key] = value - 1 # no gaps please 


        logging.info('Creating new group: %s', output_cube_names[0])
        out_cube = cube.parent.create_group(output_cube_names[0])
        logging.debug('Copying attributes')
        for key in cube.attrs.keys():
            out_cube.attrs[key] = cube.attrs[key]

        out_cube.attrs['mapping'] = pickle.dumps(out_mapping)

        logging.debug('Create new datasets')
        for i in xrange(len(cube)):
            name = str(i)
            dset = cube[name]
            data = calc_data(dset, method, collapse_dim)
            ds = out_cube.create_dataset(name, shape=data.shape,
                    dtype=data.dtype)
            ds[...] = data
            ds_mapping = dict()
            for key, value in function.get_mapping(dset).items():
                if key < collapse_dim:     
                    ds_mapping[key] = value
                elif key > collapse_dim:     
                    ds_mapping[key-1] = value # no gaps please
            ds.attrs['mapping'] = pickle.dumps(ds_mapping)

