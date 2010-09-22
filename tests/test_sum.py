from __future__ import with_statement
from hdf import Hdf5
from decimal import Decimal as d
from numpy import arange, array
from sum import Sum
import os

def pytest_funcarg__hdf_project(request):
    ''' Set up a project, create two datasets with alike dimensions (4x4
    (filled with the numbers from 0 to 4x4 = 15) and 1x1(filled with the number
    1))

    '''
    if os.path.exists('sum.hdf5'):
        os.remove('sum.hdf5')
    hdf = Hdf5('sum')
    two_d_name_1 = '2D_1'
    two_d_name_2 = '2D_2'

    # Create group 1
    name = hdf.add_sdcube(['x', 'y'], name=two_d_name_1)
    sdcube1 = hdf.get_sdcube(name)
    sdcube1.create_dataset({'x':[d('1'), d('2'), d('3'), d('4')],
            'y':[d('1'), d('2'), d('3'), d('4')]})
    sdcube1.create_dataset({'x':[d('10')], 'y':[d('10')]})
    sdcube1.set_data({'x':d('1'), 'y':d('1')}, arange(4*4).reshape((4,4)))
    sdcube1.set_data({'x':d('10'), 'y':d('10')}, array(1).reshape((1,1)))

    # Create group 2
    name = hdf.add_sdcube(['x', 'y'], name=two_d_name_2)
    sdcube2 = hdf.get_sdcube(name)
    sdcube2.create_dataset({'x':[d('1'), d('2'), d('3'), d('4')],
            'y':[d('1'), d('2'), d('3'), d('4')]})
    sdcube2.create_dataset({'x':[d('10')], 'y':[d('10')]})
    sdcube2.set_data({'x':d('1'), 'y':d('1')},
            arange(4*4).reshape((4,4)))
    sdcube2.set_data({'x':d('10'), 'y':d('10')},
            array(1).reshape((1,1)))
    return hdf

def test_two_cubes(hdf_project):
    my_sum = Sum('python.test.sum', [], ['2D_1', '2D_2'], ['sum'])
    hdf_project.add_function(my_sum)
    hdf_project.recompute()
    data = hdf_project.get_sdcube('sum').get_data()
    expected = [array([[0, 2, 4, 6], [8, 10, 12, 14],[16, 18, 20, 22], [24,
        26, 28, 30]]), array([[2]])]
    for array1, array2 in zip(data, expected):
        assert all((x == y) for x,y in zip(array1.flat, array2.flat))

def test_four_cubes(hdf_project):
    hdf = hdf_project
    two_d_name_3 = '2D_3'
    two_d_name_4 = '2D_4'

    # Create group 3
    name = hdf.add_sdcube(['x', 'y'], name=two_d_name_3)
    sdcube3 = hdf.get_sdcube(name)
    sdcube3.create_dataset({'x':[d('1'), d('2'), d('3'), d('4')], 'y':[d('1'),
        d('2'), d('3'), d('4')]})
    sdcube3.create_dataset({'x':[d('10')], 'y':[d('10')]})
    sdcube3.set_data({'x':d('1'), 'y':d('1')}, arange(4*4).reshape((4,4)))
    sdcube3.set_data({'x':d('10'), 'y':d('10')}, array(1).reshape((1,1)))

    # Create group 4
    name = hdf.add_sdcube(['x', 'y'], name=two_d_name_4)
    sdcube4 = hdf.get_sdcube(name)
    sdcube4.create_dataset({'x':[d('1'), d('2'), d('3'), d('4')],
            'y':[d('1'), d('2'), d('3'), d('4')]})
    sdcube4.create_dataset({'x':[d('10')], 'y':[d('10')]})
    sdcube4.set_data({'x':d('1'), 'y':d('1')}, arange(4*4).reshape((4,4)))
    sdcube4.set_data({'x':d('10'), 'y':d('10')}, array(1).reshape((1,1)))

    my_sum = Sum('python.test.sum', [], ['2D_1', '2D_2', '2D_3', '2D_4'],
            ['sum'])
    hdf.add_function(my_sum)
    hdf.recompute()
    data = hdf.get_sdcube('sum').get_data()
    expected = [array([[0, 4, 8, 12], [16, 20, 24, 28], [32, 36, 40, 44], [48,
        52, 56, 60]]), array([[4]])]
    for array1, array2 in zip(data, expected):
        assert all((x == y) for x,y in zip(array1.flat, array2.flat))

