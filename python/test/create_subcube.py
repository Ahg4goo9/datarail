import pickle
import logging
import function

class Create_subcube(function.Function):
    def __call__(self, input_cubes, output_cubes, params):
        ''' Create a subcube of an existing cubes.
        The params are should be a list of one dictionary.
        The dictionary keys should match valid indexlabels.
        The dictionary values should be a tuple of two values if you
        want to have a range or a list of any number of values.
            
        '''
        if not input_cubes or len(input_cubes) != 1:
            logging.error('input_cubes must be a list of one input cube.')
            raise ValueError
        if not output_cubes or len(output_cubes) != 1:
            logging.error('output_cubes must be a list of one output cube name.')
            raise ValueError
        items = {}
        if len(params) > 0:
            items = params[0]
        in_group = input_cubes[0]
        in_group_mapping = pickle.loads(str(in_group.attrs['mapping'])) 
        logging.info('Get splitted data')
        data, indices = function.get_data_and_indices(in_group, items)

        logging.info('Create new group')
        group = in_group.parent.create_group(output_cubes[0])
        group.attrs['mapping'] = pickle.dumps(in_group_mapping)
        logging.debug('Create new datasets')
        for i in xrange(len(data)):
            if data[i] == []:
                continue
            name = str(i)
            ds = group.create_dataset(name, shape=data[i].shape,
                    dtype=data[i].dtype)
            ds[...] = data[i][...]
            dset_mapping = indices[i]
            ds.attrs['mapping'] = pickle.dumps(dset_mapping)

        logging.debug('Subcubes created.')

