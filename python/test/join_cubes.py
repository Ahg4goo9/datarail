import pickle
import logging
import tools

def function(input_cubes, output_cubes, params):
    ''' Create a subcube of an existing cubes.
        
    '''
    if not input_cubes or len(input_cubes) < 2:
        logging.error('input_cubes must be a list of at least two input cube.')
        raise ValueError

    items = {}
    if len(params) > 0:
        items = params[0]
    in_group = input_cubes[0]
    in_group_mapping = pickle.loads(str(in_group.attrs['mapping'])) 
    data, indices = tools.get_data_and_indices2(in_group, items)

    group = in_group.parent.create_group(output_cubes[0])
    group.attrs['mapping'] = pickle.dumps(in_group_mapping)
    for i in xrange(len(data)):
        for j in xrange(len(data[i])):
            if data[i][j] == []:
                continue
            name = str(i)
            ds = group.create_dataset(name, shape=data[i][j].shape,
                    dtype=data[i][j].dtype)
            ds[...] = data[i][j][...]
            dset_mapping = dict([in_group_mapping[k], [v]] for (k, v) in
                    indices[i][0].items())
            ds.attrs['mapping'] = pickle.dumps(dset_mapping)

    
