#import pickle
import logging
import function
import pickle
from numpy import concatenate
from itertools import combinations 

def join_cubes(out_cube, cubes):
    ''' Join the given cubes in the group
    
    '''
    while len(cubes) > 1:
        #common elements
        logging.info('Joining cubes: %s and %s' % (cubes[-1].name,
            cubes[-2].name))
        for i, (ds1, ds2) in enumerate(zip(cubes[-2].values(),
            cubes[-1].values())):
            logging.debug('Concatenating datasets: %s and %s' % (ds1.name,
                ds2.name))
            ds1_map = function.get_mapping(ds1)
            ds2_map = function.get_mapping(ds2)
            keys = function.compare(ds1_map, ds2_map)
            if not len(keys) == 1:
                logging.error('Only one dimension can be different. Different'
                        ' dimensions are %s' % keys)
                raise ValueError
            key = keys[0]
            outmap = ds1_map
            for value in ds2_map[key]:
                outmap[key].append(value)
            combined_data = concatenate((ds1[...], ds2[...]), key)
            try:
                del out_cube[str(i)]
            except KeyError:
                pass

            ds = out_cube.create_dataset(str(i), shape=combined_data.shape,
                    dtype=ds1.dtype)
            ds[...] = combined_data
            for key, value in ds1.attrs.items():
                ds.attrs[key] = value
            ds.attrs['mapping'] = pickle.dumps(outmap)

        #append non common elements
        (len_a, cube_a), (len_b, cube_b) = sorted((len(c), c) for c in
                cubes[-2:])
        for i in xrange(len_a, len_b):
            name = str(i)
            out_cube.copy(cube_b[name].name, name)

        cubes[-2] = out_cube
        cubes.pop()
    for combination in set(combinations(cubes[0].values(), 2)):
        cube1, cube2 = combination
        merge(cube1, cube2)

def merge(dataset1, dataset2):
    ''' Try to merge the given dataset into one

    '''
    ds1_map = function.get_mapping(dataset1)
    ds2_map = function.get_mapping(dataset2)
    keys = function.compare(ds1_map, ds2_map)
    if not len(keys) == 1:
        logging.warning('Only one dimension can be different. Did not merge')
        return
    logging.info('Merging datasets: %s and %s' % (dataset1.name,
        dataset2.name))
    key = keys[0]
    outmap = ds1_map
    for value in ds2_map[key]:
        outmap[key].append(value)
    combined_data = concatenate((dataset1[...], dataset2[...]), key)
    
    # copy doesn't work (because of changed shape)
    group = dataset1.parent
    name = dataset1.name
    dtype = dataset1.dtype
    attrs = dataset1.attrs.items()
    del group[dataset1.name]
    ds = group.create_dataset(name, shape=combined_data.shape,
            dtype=dtype)
    ds[...] = combined_data
    for key, value in attrs:
        ds.attrs[key] = value
    ds.attrs['mapping'] = pickle.dumps(outmap)
    del group[dataset2.name]

class JoinCubes(function.Function):
    ''' This function joins several cubes into one.
    It will try to merge the datasets if it is possible (only one 
    dimension has different index labels (and those labels must _not_
    overlap).

    '''
    def __call__(self, input_cubes, output_cubes, params):
        ''' 
            
        '''
        if not input_cubes or len(input_cubes) < 2:
            logging.error('input_cubes must be a list of at least two input'
                    ' cubes.')
            raise ValueError

        first_grp_mapping = function.get_mapping(input_cubes[0])
        for cube in input_cubes[1:]:
            if not first_grp_mapping == function.get_mapping(cube):
                logging.error('All cubes must have the same dimension_labels.')
                raise ValueError
       
        out_cube = input_cubes[0].parent.create_group(output_cubes[0])
        for key in input_cubes[0].attrs.keys():
            out_cube.attrs[key] = input_cubes[0].attrs[key]
        join_cubes(out_cube, input_cubes)

