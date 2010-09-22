'''Some useful functions for modifying or accessing cubes.


'''
import pickle

def get_first_index_labels(dset, items):
    ''' Get the 'first' index_labels of a given dataset (index 0 for every
    dimension)
    Return them as a list compatible with create_dataset.

    '''
    index_labels = {}
    mapping = get_mapping(dset)
    group_mapping = get_mapping(dset.parent)
    for key, value in items.items():
        mapping[group_mapping[key]] = [value]
    reverse_grp_map = dict((v, k) for k, v in group_mapping.iteritems())
    for key, value in mapping.items():
        index_labels[reverse_grp_map[key]] = value[0]
    return index_labels

def get_index(dimension_index, index_label, dset):
    ''' Returns the mapped index of the index_label within the hdf 
    data cube and the index of the value within that.
    
    '''
    mapping = get_mapping(dset)
    if index_label in mapping[dimension_index]:
        return mapping[dimension_index].index(index_label)
    return -1

def get_index_label(dimension_index, index, dset):
    ''' Load the mapping for the dataset and return the index_label
    of the dataset mapping.
    
    '''
    return get_mapping(dset)[dimension_index][index]

def get_combinations(to_be_combined):
    '''Returns all possible combinations of the elments in the 
    dictionary to_be_combined.

    '''
    combinations = [[]]
    for key in to_be_combined:
        combinations = [i + [{key: y}] for y in to_be_combined[key] for i in
                combinations]
    return combinations

def get_mapping(h5_elem):
    '''Get and return the mapping of the h5 element

    '''
    return pickle.loads(str(h5_elem.attrs['mapping']))

def compare(dict1, dict2):
    ''' Compare two dictionaries and return the keys where the values are not
    equal.

    '''
    return [k for k in dict1 if dict1[k] != dict2[k]]

def get_indices_and_labels(grp_map, dataset, items):
    ''' Get all indices and labels
    '''
    inds = list()
    dim_labels = list()
    for combination in get_combinations(items):
        #TODO Check for multiple used indices (how are we treating those?)
        inds.append(list())
        dim_labels.append(dict())
        comb = dict([(x.keys()[0], x.items()[0][1]) for x in
            combination])
        inds[-1].append([slice(None, None, None)] * len(dataset.shape))
        for key, value in comb.items():
            dim_index = grp_map[key]
            dim_labels[-1][dim_index] = list()
            if type(value) == tuple and len(value) == 2: # range of index_labels
                start = get_index(dim_index, value[0], dataset)
                end = get_index(dim_index, value[1], dataset)
                if start != -1 and end != -1:
                    inds[-1][-1][dim_index] = slice(start, end +
                            1, None)
                    for index in xrange(start, end + 1):
                        dim_labels[-1][dim_index].append(
                                get_index_label(dim_index, index, dataset))
                else:
                    inds.pop()
                    dim_labels.pop()
                    break
            else:
                ind = get_index(dim_index, value, dataset)
                if ind != -1:
                    inds[-1][-1][dim_index] = ind
                    dim_labels[-1][dim_index].append(
                            get_index_label(dim_index, ind, dataset))
                else:
                    inds.pop()
                    dim_labels.pop()
                    break
    return inds, dim_labels

def get_data_and_indices(group, items):
    ''' Gathers and return the data of the group.
    The data is stored in a list of numpy ndarrays.

    '''
    data = list()
    inds = list()
    dim_labels = list()
    grp_map = get_mapping(group)
    for dataset in group.values():
        data.append(dataset[...])
        one, two = get_indices_and_labels(grp_map, dataset, items)
        inds.append(one)
        dim_labels.append(two)

    ret_data = list()
    ret_labels = list()

    for i, indices in enumerate(inds):
        for indices2 in indices:
            for index in indices2:
                ret_data.append(data[i][index])
        for dim_label in dim_labels[i]:
            ret_labels.append(dim_label)

    return ret_data, ret_labels


class Function:
    ''' Class that holds all necessary parametes for a function

    '''
    def __init__(self, name, params, input_cube_names, output_cube_names):
        '''
        The name should be the relative path to hdf.py
        It also executes the function.

        '''
        self.name = name
        self.params = params
        self.input_cube_names = input_cube_names
        self.output_cube_names = output_cube_names

    def __str__(self):
        output = {self.name: [self.params, self.input_cube_names,
            self.output_cube_names]}
        return str(output)
    
    def __call__(self, input_cubes, output_cube_names, params):
        raise NotImplementedError

