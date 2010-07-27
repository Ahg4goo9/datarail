from hdf import Hdf5
from join_cubes import JoinCubes
from decimal import Decimal as d
from numpy import arange, array
import os
import os.path

def pytest_funcarg__hdf_project(request):
    ''' Set up a project, create two datasets with alike dimensions (4x4
    (filled with the numbers from 1 to 4x4 = 16) and 1x1(filled with the number
    1))

    '''
    if os.path.exists('join.hdf5'):
        os.remove('join.hdf5')
    hdf = Hdf5('join')

    # Create dset 1
    two_d_name_1 = '2D_1'
    hdf.create_dataset(two_d_name_1, ['x', [d('1'), d('2'), d('3'), d('4')]],
            ['y', ['a', 'b', 'c', 'd']])
    hdf.create_dataset(two_d_name_1, ['x', [d('10')]], ['y', ['e']])
    hdf.set_dataset(two_d_name_1, {'x':d('1'), 'y':'a'},
            arange(4*4).reshape((4, 4)))
    hdf.set_dataset(two_d_name_1, {'x':d('10'), 'y':'e'},
            array(1).reshape((1, 1)))

    # And this is what it looks like
    #          y
    #     a  b  c  d  e  #
    #--------------------#
    # |1  0  1  2  3     #
    # |2  4  5  6  7     #
    #x|3  8  9  10 11    #
    # |4  12 13 14 15    #
    # |10             1  #
    ######################

    # Create dset 2
    two_d_name_2 = '2D_2'
    hdf.create_dataset(two_d_name_2, ['x', [d('10')]], ['y', ['a', 'b', 'c',
        'd']])
    hdf.create_dataset(two_d_name_2, ['x', [d('1'), d('2'), d('3'), d('4')]],
            ['y', ['e']])
    hdf.set_dataset(two_d_name_2, {'x':d('10'), 'y':'a'},
            arange(4).reshape((1, 4)))
    hdf.set_dataset(two_d_name_2, {'x':d('1'), 'y':'e'},
            arange(4).reshape((4, 1)))

    # And this is what it looks like
    #          y
    #     a  b  c  d  e  #
    #--------------------#
    # |1              0  #
    # |2              1  #
    #x|3              2  #
    # |4              3  #
    # |10 0  1  2  3     #
    ######################

    return hdf

def test_one_cube_fail(hdf_project):
    ''' Try to join one cube. This is expected to fail.

    '''
    my_join_functions = JoinCubes('Join', [], ['2D_1'], ['joined_cube'])
    hdf_project.add_function(my_join_functions)
    try:
        hdf_project.recompute()
        assert False
    except ValueError:
        assert True

def test_different_dim_labels(hdf_project):
    ''' Create a dataset with a different dimension label. It should 
    fail because of that.

    '''
    # Create dset 3
    two_d_name_3 = '2D_3'
    hdf_project.create_dataset(two_d_name_3, ['x', [d('10')]], ['z', ['a', 'b',
        'c', 'd']])
    my_join_functions = JoinCubes('Join', [], ['2D_1', '2D_2', '2D_3'],
            ['joined_cube'])
    hdf_project.add_function(my_join_functions)
    try:
        hdf_project.recompute()
        assert False
    except ValueError:
        assert True

def test_two_2D_cubes(hdf_project):
    ''' Join the two existing cubes

    '''
    my_join_functions = JoinCubes('Join', [], ['2D_1', '2D_2'], ['joined_cube'])
    hdf_project.add_function(my_join_functions)
    hdf_project.recompute()
    data = hdf_project.get_data('joined_cube')
    expected = [array([
        [ 0,  1,  2,  3],
        [ 4,  5,  6,  7],
        [ 8,  9, 10, 11],
        [12, 13, 14, 15],
        [ 0,  1,  2,  3]]),
        array([
            [1],
            [0],
            [1],
            [2],
            [3]])]
    for array1, array2 in zip(data, expected):
        assert all((x == y) for x, y in zip(array1.flat, array2.flat))


def test_five_2D_cubes(hdf_project):
    ''' Create three additional cubes and try to join them and the two
    existing ones

    '''
    hdf = hdf_project
    # Create dset 3 additional cubes
    for i in xrange(3, 6):
        cube_name = ''.join(('2D_', str(i)))
        hdf.create_dataset(cube_name, ['x', [d(str(i*4))]], ['y', ['a', 'b',
            'c', 'd']])
        hdf.set_dataset(cube_name, {'x':d(str(i*4)), 'y':'a'},
                3 * i * arange(4).reshape((1, 4)))

    cube_names = [''.join(('2D_', str(i))) for i in xrange(1, 6)]
    my_join_functions = JoinCubes('Join', [], cube_names, ['joined_cube'])
    hdf_project.add_function(my_join_functions)
    hdf_project.recompute()

    data = hdf_project.get_data('joined_cube')
    expected = [array([
        [ 0,  1,  2,  3],
        [ 4,  5,  6,  7],
        [ 8,  9, 10, 11],
        [12, 13, 14, 15],
        [ 0,  1,  2,  3],
        [ 0,  9, 18, 27],
        [ 0, 12, 24, 36],
        [ 0, 15, 30, 45]]),
        array([
            [1],
            [0],
            [1],
            [2],
            [3]])]
    for array1, array2 in zip(data, expected):
        assert all((x == y) for x, y in zip(array1.flat, array2.flat))

def test_merge(hdf_project):
    hdf = hdf_project
    # Create dset 4
    two_d_name_3 = '2D_3'
    hdf.create_dataset(two_d_name_3, ['x', [d('1'), d('2'), d('3'), d('4')]],
            ['y', ['a', 'b', 'c', 'd']])
    hdf.create_dataset(two_d_name_3, ['x', [d('1')]], ['y', ['e']])
    hdf.set_dataset(two_d_name_3, {'x':d('1'), 'y':'a'},
            arange(4*4).reshape((4, 4)))
    hdf.set_dataset(two_d_name_3, {'x':d('1'), 'y':'e'},
            array(1).reshape((1, 1)))

    # And this is what it looks like
    #          y
    #     a  b  c  d  e  #
    #--------------------#
    # |1  0  1  2  3  1  #
    # |2  4  5  6  7     #
    #x|3  8  9  10 11    #
    # |4  12 13 14 15    #
    # |10                #
    ######################

    # Create dset 4
    two_d_name_4 = '2D_4'
    hdf.create_dataset(two_d_name_4, ['x', [d('10')]], ['y', ['a', 'b', 'c',
        'd']])
    hdf.create_dataset(two_d_name_4, ['x', [d('2'), d('3'), d('4'), d('10')]],
            ['y', ['e']])
    hdf.set_dataset(two_d_name_4, {'x':d('10'), 'y':'a'},
            arange(4).reshape((1, 4)))
    hdf.set_dataset(two_d_name_4, {'x':d('2'), 'y':'e'},
            arange(4).reshape((4, 1)))

    # And this is what it looks like
    #          y
    #     a  b  c  d  e  #
    #--------------------#
    # |1                 #
    # |2              0  #
    #x|3              1  #
    # |4              2  #
    # |10 0  1  2  3  3  #
    ######################

    my_join_functions = JoinCubes('Join', [], ['2D_3', '2D_4'], ['joined_cube'])
    hdf.add_function(my_join_functions)
    hdf.recompute()
    data = hdf.get_data('joined_cube')
    expected = [array([
        [0 ,  1,  2,  3, 1],
        [4 ,  5,  6,  7, 0],
        [8 ,  9, 10, 11, 1],
        [12, 13, 14, 15, 2],
        [0 ,  1,  2,  3, 3]])]
    for array1, array2 in zip(data, expected):
        assert all((x == y) for x, y in zip(array1.flat, array2.flat))

