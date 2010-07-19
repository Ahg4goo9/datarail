from hdf import Hdf5
from create_subcube import Create_subcube
from decimal import Decimal as d
from numpy import arange, array
import os
import os.path

def pytest_funcarg__hdf_project(request):
    ''' Set up a project, create two datasets with alike dimensions (4x4
    (filled with the numbers from 1 to 4x4 = 16) and 1x1(filled with the number
    1))

    '''
    if os.path.exists('subcube.hdf5'):
        os.remove('subcube.hdf5')
    hdf = Hdf5('subcube')
    two_d_name_1 = '2D_1'

    # Create dset 1
    hdf.create_dataset(two_d_name_1, ['x', [d('1'), d('2'), d('3'), d('4')]],
            ['y', ['a', 'b', 'c', 'd']])
    hdf.create_dataset(two_d_name_1, ['x', [d('10')]], ['y', ['e']])
    hdf.set_dataset(two_d_name_1, {'x':d('1'), 'y':'a'},
            arange(4*4).reshape((4, 4)))
    hdf.set_dataset(two_d_name_1, {'x':d('10'), 'y':'e'},
            array(1).reshape((1, 1)))

    # And this is what it looks like
    #          y
    #     a  b  c  d  e
    #--------------------
    # |1  0  1  2  3 
    # |2  4  5  6  7
    #x|3  8  9  10 11 
    # |4  12 13 14 15
    # |10             1
    return hdf

def test_create_subcube_range_and_non_range(hdf_project):
    hdf = hdf_project
    
    my_create_subcube1 = Create_subcube('Function 1',
            [{'x':[(d('1'), d('4'))], 'y':['a', 'e', 'd']}], ['2D_1'],
            ['subcube1'])
    hdf.add_function(my_create_subcube1)

    hdf.recompute()
    cubes = hdf_project.get_data('subcube1', items={})
    expected = [array([[0, 4, 8, 12]]), array([[3, 7, 11, 15]])]
    for array1, array2 in zip(cubes, expected):
        assert all((x == y) for x, y in zip(array1.flat, array2.flat))

def test_create_subcube_range_and_range(hdf_project):
    hdf = hdf_project
    my_create_subcube2 = Create_subcube('Function 2',
            [{'x':[(d('2'), d('4'))], 'y':[('a', 'c')]}], ['2D_1'],
            ['subcube2'])
    hdf.add_function(my_create_subcube2)

    hdf.recompute()
    cubes = hdf_project.get_data('subcube2', items={})
    expected = [array([[4, 5, 6], [8, 9, 10], [12, 13, 14]])]
    for array1, array2 in zip(cubes, expected):
        assert all((x == y) for x, y in zip(array1.flat, array2.flat))

def test_create_subecube_mixed_range_and_non_range(hdf_project):
    hdf = hdf_project

    my_create_subcube3 = Create_subcube('Function 3',
            [{'x':[(d('2'), d('4')), d('10')], 'y':[('a', 'c'), 'e']}],
            ['2D_1'], ['subcube3'])
    hdf.add_function(my_create_subcube3)

    hdf.recompute()
    cubes = hdf_project.get_data('subcube3', items={})
    expected = [array([[4, 5, 6], [8, 9, 10], [12, 13, 14]]), array([[1]])]
    for array1, array2 in zip(cubes, expected):
        assert all((x == y) for x, y in zip(array1.flat, array2.flat))
    #
    #my_create_subcube4 = Create_subcube('python.test.create_subcube',
    #    [{'x':[d('1')]}], ['3D_1'], ['subcube4'])
    #hdf.add_function(my_create_subcube4)



    #cubes = hdf_project.get_data('subcube3', items={})
    #expected = [array([[1]]), array([[0]]), array([[6]]), array([[8]]),
    #        array([[14]]), array([[24]]), array([[30]])] 
    #for array1, array2 in zip(cubes, expected):
    #    assert all((x == y) for x, y in zip(array1.flat, array2.flat))

