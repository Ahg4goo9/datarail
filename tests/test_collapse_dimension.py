from hdf import Hdf5
from decimal import Decimal as d
from numpy import arange, array
import os
import os.path
from collapse_dimension import CollapseDimension

def pytest_funcarg__hdf_project(request):
    ''' Set up a project, create two datasets with alike dimensions (4x4
    (filled with the numbers from 1 to 4x4 = 16) and 1x1(filled with the number
    1))

    '''
    if os.path.exists('collapse.hdf5'):
        os.remove('collapse.hdf5')
    hdf = Hdf5('collapse')

    # Create dset 1
    two_d_name_1 = '2D_1'
    hdf.create_dataset(two_d_name_1, ['x', [d('1'), d('2'), d('3'), d('4')]],
            ['y', ['a', 'b', 'c', 'd']])
    hdf.set_dataset(two_d_name_1, {'x':d('1'), 'y':'a'},
            arange(4*4).reshape((4, 4)))

    # And this is what it looks like
    #          y
    #     a  b  c  d  #
    #-----------------#
    # |1  0  1  2  3  #
    # |2  4  5  6  7  #
    #x|3  8  9  10 11 #
    # |4  12 13 14 15 #
    ###################

    return hdf

def test_average(hdf_project):
    collapse_dim = 0
    my_collapse_functions = CollapseDimension('Collapse', [collapse_dim,
        'average'], ['2D_1'], ['collapsed_cube'])
    hdf_project.add_function(my_collapse_functions)
    hdf_project.recompute()
    data = hdf_project.get_data('collapsed_cube')
    
    #test the data
    expected = [array([[6, 7, 8, 9]])]
    for array1, array2 in zip(data, expected):
        assert all((x == y) for x, y in zip(array1.flat, array2.flat))

    #test the attributes
    cube_mapping = hdf_project.get_mapping('collapsed_cube')
    if not cube_mapping == {'y':0}:
        assert False

    
def test_max(hdf_project):
    collapse_dim = 0
    my_collapse_functions = CollapseDimension('Collapse', [collapse_dim,
        'max'], ['2D_1'], ['collapsed_cube'])
    hdf_project.add_function(my_collapse_functions)
    hdf_project.recompute()
    data = hdf_project.get_data('collapsed_cube')
    
    #test the data
    expected = [array([[12, 13, 14, 15]])]
    for array1, array2 in zip(data, expected):
        assert all((x == y) for x, y in zip(array1.flat, array2.flat))

    #test the attributes
    cube_mapping = hdf_project.get_mapping('collapsed_cube')
    if not cube_mapping == {'y':0}:
        assert False

    
def test_min(hdf_project):
    collapse_dim = 1
    my_collapse_functions = CollapseDimension('Collapse', [collapse_dim,
        'min'], ['2D_1'], ['collapsed_cube'])
    hdf_project.add_function(my_collapse_functions)
    hdf_project.recompute()
    data = hdf_project.get_data('collapsed_cube')
    
    #test the data
    expected = [array([[0, 4, 8, 12]])]
    for array1, array2 in zip(data, expected):
        assert all((x == y) for x, y in zip(array1.flat, array2.flat))

    #test the attributes
    cube_mapping = hdf_project.get_mapping('collapsed_cube')
    if not cube_mapping == {'x':0}:
        assert False

    
