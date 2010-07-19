import pickle
import logging
from function import Function

class Sum(Function):
    def __call__(self, input_cubes, output_cubes, params):
        '''Sum up input cubes that have identical indices.

        '''
        if not input_cubes or len(input_cubes) < 2:
            logging.error('input_cubes must be a list of at least two'
                    ' input_cubes.')
            raise ValueError
        for i in xrange(len(input_cubes[0])):
            for cube in input_cubes[1:]:
                if not input_cubes[0][str(i)].shape == cube[str(i)].shape:
                    logging.error('input_cubes must have the same dimensions')
                    raise ValueError
        for cube in input_cubes[1:]:
            if not pickle.loads(str(input_cubes[0].attrs['mapping'])) ==\
                    pickle.loads( str(cube.attrs['mapping'])):
                logging.error('The input_cubes must have the same indices and'
                            ' dimension identifiers')
                raise ValueError
        if not len(output_cubes) == 1:
            logging.error('There must be one name in list output_cubes')
            raise ValueError


        in_one = input_cubes[0]
        logging.info('Creating cube: %s' % output_cubes[0])
        group = in_one.parent.create_group(output_cubes[0])
        for i in xrange(len(in_one)):
            name = str(i)
            logging.debug('Creating ds: %s' % name)
            ds = group.create_dataset(name, shape=in_one[name].shape,
                    dtype=in_one[name].dtype)
            for key, value in in_one[name].attrs.items():
                ds.attrs[key] = value

            # set the data
            ds[...] = in_one[name][...]
            logging.debug('Setting data in ds: %s' % name)
            logging.debug('data: %s' % ds[...])
            for cube in input_cubes[1:]:
                ds[...] = ds[...] + cube[name][...]
        logging.debug('Setting attributes for group')
        for key in in_one.attrs.keys():
            group.attrs[key] = in_one.attrs[key]

