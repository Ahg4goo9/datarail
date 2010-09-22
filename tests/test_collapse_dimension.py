from hdf import Hdf5
from decimal import Decimal as d
from numpy import arange, array
import os
from collapse_dimension import CollapseDimension

def pytest_funcarg__simple_hdf_project(request):
    ''' Set up a project, create one dataset with two dimensions (4x4
    (filled with the numbers from 0 to 4x4 = 15))

    '''
    if os.path.exists('collapse.hdf5'):
        os.remove('collapse.hdf5')
    hdf = Hdf5('collapse')

    # Create dset 1
    two_d_name_1 = '2D_1'
    name = hdf.add_sdcube(['x', 'y'], name=two_d_name_1)
    sdcube1 = hdf.get_sdcube(name)
    sdcube1.create_dataset({'x':[d('1'), d('2'), d('3'), d('4')], 'y':['a',
        'b', 'c', 'd']})
    sdcube1.set_data({'x':d('1'), 'y':'a'}, arange(4*4).reshape((4, 4)))

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

def pytest_funcarg__hdf_project(request):
    ''' Set up a project, create one datasets with two dimensions (4x4
    (filled with the numbers from 0 to 4x4 = 15) and 1x1 (filled with the number
    0))

    '''
    if os.path.exists('collapse.hdf5'):
        os.remove('collapse.hdf5')
    hdf = Hdf5('collapse')

    # Create dset 1
    two_d_name_1 = '2D_1'
    name = hdf.add_sdcube(['x', 'y'], name=two_d_name_1)
    sdcube1 = hdf.get_sdcube(name)
    sdcube1.create_dataset({'x':[d('1'), d('2'), d('3'), d('4')], 'y':['a',
        'b', 'c', 'd']})
    sdcube1.create_dataset({'x':[d('10')], 'y':['e']})
    sdcube1.set_data({'x':d('1'), 'y':'a'}, arange(4*4).reshape((4, 4)))
    sdcube1.set_data({'x':d('10'), 'y':'e'}, arange(1*1).reshape((1, 1)))

    # And this is what it looks like
    #          y
    #     a  b  c  d  e #
    #-------------------#
    # |1  0  1  2  3    #
    # |2  4  5  6  7    #
    #x|3  8  9  10 11   #
    # |4  12 13 14 15   #
    # |               0 #  
    #####################

    return hdf

def test_average(simple_hdf_project):
    collapse_dim = 0
    output_cube_names = ['collapsed_cube']
    my_collapse_functions = CollapseDimension('Collapse', [collapse_dim,
        'average'], ['2D_1'], output_cube_names)
    simple_hdf_project.add_function(my_collapse_functions)
    simple_hdf_project.recompute()
    outcube = simple_hdf_project.get_sdcube(output_cube_names[0])
    data = outcube.get_data()
    
    #test the data
    expected = [array([[6, 7, 8, 9]])]
    for array1, array2 in zip(data, expected):
        assert all((x == y) for x, y in zip(array1.flat, array2.flat))

    #test the attributes
    cube_mapping = outcube.mapping
    if not cube_mapping == {'y':0}:
        assert False

    
def test_max(simple_hdf_project):
    collapse_dim = 0
    output_cube_names = ['collapsed_cube']
    my_collapse_functions = CollapseDimension('Collapse', [collapse_dim,
        'max'], ['2D_1'], output_cube_names)
    simple_hdf_project.add_function(my_collapse_functions)
    simple_hdf_project.recompute()
    outcube = simple_hdf_project.get_sdcube(output_cube_names[0])
    data = outcube.get_data()
    
    #test the data
    expected = [array([[12, 13, 14, 15]])]
    for array1, array2 in zip(data, expected):
        assert all((x == y) for x, y in zip(array1.flat, array2.flat))

    #test the attributes
    cube_mapping = outcube.mapping
    if not cube_mapping == {'y':0}:
        assert False

    
def test_min(simple_hdf_project):
    collapse_dim = 1
    output_cube_names = ['collapsed_cube']
    my_collapse_functions = CollapseDimension('Collapse', [collapse_dim,
        'min'], ['2D_1'], output_cube_names)
    simple_hdf_project.add_function(my_collapse_functions)
    simple_hdf_project.recompute()
    outcube = simple_hdf_project.get_sdcube(output_cube_names[0])
    data = outcube.get_data()
    
    #test the data
    expected = [array([[0, 4, 8, 12]])]
    for array1, array2 in zip(data, expected):
        assert all((x == y) for x, y in zip(array1.flat, array2.flat))

    #test the attributes
    cube_mapping = outcube.mapping
    if not cube_mapping == {'x':0}:
        assert False

def test_test(hdf_project):
    input_cube_names = ['2D_1']
    output_cube_names = ['collapsed_cube']
    collapse_dim = 1
    my_collapse_functions = CollapseDimension('Collapse', [collapse_dim,
        'min'], input_cube_names, output_cube_names)
    hdf_project.add_function(my_collapse_functions)
    hdf_project.recompute()
    outcube = hdf_project.get_sdcube(output_cube_names[0])
    data = outcube.get_data()
    
    #test the data
    expected = [array([[0, 4, 8, 12]]), array([[0]])]
    for array1, array2 in zip(data, expected):
        assert all((x == y) for x, y in zip(array1.flat, array2.flat))

    #test the attributes
    cube_mapping = outcube.mapping
    if not cube_mapping == {'x':0}:
        assert False

