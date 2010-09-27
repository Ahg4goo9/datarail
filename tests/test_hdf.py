from __future__ import with_statement
from numpy import arange
import h5py
from hdf import Hdf5
from sum import Sum
from decimal import Decimal as d
import os

def pytest_funcarg__hdf_project(request):
    ''' Set up a project, create two datasets with alike dimensions and
    fill both with the numbers (0, 1, 2,..., 3*3*3*4-1).

    '''
    if os.path.exists('project.hdf5'):
        os.remove('project.hdf5')
    hdf = Hdf5('project')
    group_name = 'Project Data'
    indices = {'first':d('1'), 'second':'a', 'test':d('1.0'), 'another':d('1')}
    name = hdf.add_sdcube(['first', 'second', 'test', 'another'],
            name=group_name)
    sdcube1 = hdf.get_sdcube(name)
    sdcube1.create_dataset({'first':[d('1'), d('2'), d('7.0')],
            'second':['a', 'b', 'c'], 'test':[d('1.0'), d('2.0'), d('3.0')],
            'another':[d('1'), d('2.0'), '3', d('4')]})
    sdcube1.set_data(indices, arange(3*3*3*4).reshape((3, 3, 3, 4)))

    name = hdf.add_sdcube(['first', 'second', 'test', 'another'],
            name='ds')
    sdcube2 = hdf.get_sdcube(name)
    sdcube2.create_dataset({'first':[d('1'), d('2'), d('7.0')],
            'second':['a', 'b', 'c'], 'test':[d('1.0'), d('2.0'), d('3.0')],
            'another':[d('1'), d('2.0'), '3', d('4')]})
    sdcube2.set_data(indices, sdcube1.get_data()[0])
    return hdf

def pytest_funcarg__function(request):
    my_sum = Sum('python.test.sum', [], ['Project Data', 'ds'], ['sum'])
    return my_sum

def test_delete_non_existing_dataset(hdf_project):
    group_name = 'non existing'
    try:
        hdf_project.delete_cube(group_name)
        assert False
    except KeyError:
        assert True

def test_delete_dataset(hdf_project):
    group_name = 'Project Data'
    hdf_project.get_sdcube(group_name).get_data()
    hdf_project.delete_cube(group_name)
    try:
        hdf_project.get_sdcube(group_name).get_data()
        assert False
    except KeyError:
        assert True

def test_set_wrong_dimension_data(hdf_project):
    group_name = 'Project Data'
    indices = {'first':d('1'), 'second':'a', 'test':d('1.0'), 'another':d('1')}
    try:
        hdf_project.get_sdcube(group_name).set_data(indices, arange(1))
        assert False
    except ValueError:
        assert True

def test_create_overlapping_datasets(hdf_project):
    try:
        group_name = 'Project Data'
        sdcube = hdf_project.get_sdcube(group_name)
        sdcube.create_dataset({'first':[d('1'), d('2'), d('7.0')],
            'second':['a', 'b', 'c'], 'test':[d('1.0'), d('2.0'), d('3.0')],
            'another':[d('1'), d('2.0'), '3', d('4')]})
        assert False
    except ValueError:
        assert True

def test_create_non_overlapping_datasets(hdf_project):
    ''' This should prove that the integer and float index labels are
    different :-)

    '''
    group_name = 'Project Data'
    sdcube = hdf_project.get_sdcube(group_name)
    sdcube.create_dataset({'first':[d('1'), d('2'), d('7.0')], 'second':['a',
        'b', 'c'], 'test':[d('1.0'), d('2.0'), d('3.0')], 'another':[d('1.1'),
            d('2.1'), d('3.1'), d('4.1')]})
    assert True
    
def test_create_dataset_lacking_dimension(hdf_project):
    try:
        group_name = 'Project Data'
        sdcube = hdf_project.get_sdcube(group_name)
        sdcube.create_dataset({'first':[d('1'), d('2'), d('7.0')],
            'second':['a', 'b', 'c'], 'test':[d('1.0'), d('2.0'), d('3.0')]})
        assert False
    except ValueError:
        assert True

def test_create_dataset_wrong_dimension(hdf_project):
    try:
        group_name = 'Project Data'
        sdcube = hdf_project.get_sdcube(group_name)
        sdcube.create_dataset({'first':[d('1'), d('2'), d('7.0')],
            'second':['a', 'b', 'c'], 'test':[d('1.0'), d('2.0'), d('3.0')],
            'wrong':[d('1.1'), d('2.1'), d('3.1'), d('4.1')]})
        assert False
    except ValueError:
        assert True

def test_get_data(hdf_project):
    h = hdf_project
    group_name = 'Project Data'
    assert h.get_sdcube(group_name).get_data({'first':d('1'),'test':d('3.0'),
        'another':d('1'), 'second':'c'})[0] == 32

#def test_get_data_fill_with_nan():
#    if os.path.exists('project.hdf5'):
#        os.remove('project.hdf5')
#    hdf = Hdf5('project')
#    two_d_name = '2d'
#    name = hdf.add_sdcube(['x', 'y',], name=two_d_name)
#    sdcube1 = hdf.get_sdcube(name)
#    sdcube1.create_dataset({'x':[d('1'), d('2'), d('3'), d('4')],
#            'y':[d('1'), d('2'), d('3'), d('4')]})
#    sdcube1.create_dataset({'x':[d('10')], 'y':[d('10')]})
#    sdcube1.set_data({'x':d('1'), 'y':d('1')}, 5*arange(4*4).reshape((4,4)))
#    data = hdf.get_data_fill_with_nan(two_d_name, items={})[0][...].flat
#    expected = array([[0, 5, 10, 15, NaN], [20, 25, 30, 35, NaN], [40, 45, 50,
#        55, NaN], [60, 65, 70, 75, NaN], [NaN, NaN, NaN, NaN, 0]]).flat
#
#    #nan == nan is False
#    assert all((x == y) or (isnan(x) and isnan(y)) for x,y in zip(data,
#        expected))

def test_add(hdf_project, function):
    h, my_sum = hdf_project, function
    h.add_function(my_sum)
    group_name = 'Project Data'
    func = h.get_functions()[0]
    assert func.name == 'python.test.sum'
    assert func.params ==[]
    assert func.input_cube_names == [group_name, 'ds']
    assert func.output_cube_names == ['sum']

def test_execute_fail_length(hdf_project, function):
    h, my_sum = hdf_project, function
    my_sum.input_cube_names = ['ds']
    h.add_function(my_sum)
    try:
        h.execute_function(my_sum)
        assert False
    except ValueError:
        assert True

def test_del(hdf_project, function):
    h, my_sum = hdf_project, function
    h.del_function(my_sum)
    assert len(h.get_functions()) == 0

def test_execute_function(hdf_project, function):
    hdf_project.add_function(function)
    hdf_project.execute_function(function)
    name = function.output_cube_names[0]
    data = hdf_project.get_sdcube(name).get_data()[0].flat
    expected = 2 * arange(3*3*3*4) #the sum should be double the amount
    assert all(x == y for x, y in zip(data, expected))

def test_recompute(hdf_project, function):
    h, mysum = hdf_project, function
    h.add_function(mysum)
    h.recompute()
    with h5py.File(h.filename, 'a') as f:
        assert f.get(mysum.output_cube_names[0]).attrs['dirty'] == False

def test_execute_fail_index_labels(hdf_project, function):
    h, my_sum = hdf_project, function
    name = h.add_sdcube(['first_fail', 'second', 'test', 'another'],
            name='fail')
    sdcube = h.get_sdcube(name)
    sdcube.create_dataset({'first_fail':[d('1'), d('2'), d('7.0')],
            'second':['a', 'b', 'c'], 'test':[d('1.0'), d('2.0'), d('3.0')],
            'another':[d('1'), d('2.0'), '3', d('4')]})
    my_sum.input_cube_names = [my_sum.input_cube_names[0], 'fail']
    h.add_function(my_sum)
    try:
        h.execute_function(my_sum)
        assert False
    except ValueError:
        assert True

