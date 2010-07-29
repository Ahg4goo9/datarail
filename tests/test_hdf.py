from __future__ import with_statement
from numpy import random, arange, array, NaN, isnan
import h5py
from hdf import Hdf5
from sum import Sum
from decimal import Decimal as d
import os
import os.path

def pytest_funcarg__hdf_project(request):
    ''' Set up a project, create two datasets with alike dimensions and
    fill both with the numbers (0, 1, 2,..., 3*3*3*4-1).

    '''
    if os.path.exists('project.hdf5'):
        os.remove('project.hdf5')
    hdf = Hdf5('project')
    group_name = 'Project Data'
    hdf.create_dataset(group_name, ['first',[d('1'), d('2'), d('7.0')]],
            ['second',['a', 'b', 'c']], ['test',[d('1.0'), d('2.0'), d('3.0')]],
            ['another',[d('1'), d('2.0'), '3', d('4')]])
    indices = {'first':d('1'), 'second':'a', 'test':d('1.0'), 'another':d('1')}
    with h5py.File(hdf.filename) as hdf5_file:
        group = hdf5_file[group_name]
        hdf.set_dataset(group_name, indices, 2 + 2 *
            random.random(hdf5_file[group_name]['0'].shape))
        length = 1
        for dim in group['0'].shape:
            length = length * dim
        hdf.set_dataset(group_name, indices,
            arange(length).reshape(group['0'].shape))
        hdf5_file.copy(group_name, 'ds')
        hdf.set_dataset('ds', indices, group['0'])
        hdf.set_dataset(group_name, {'first':d('2'), 'second':'b',
            'another':d('1'), 'test':d('1')}, 10*arange(2*1*2*4).reshape((2, 1,
                2, 4)))
    return hdf

def test_delete_non_existing_dataset(hdf_project):
    group_name = 'non existing'
    try:
        hdf_project.delete_cube(group_name)
        assert False
    except KeyError:
        assert True

def test_delete_dataset(hdf_project):
    group_name = 'Project Data'
    hdf_project.get_data(group_name, items={})
    hdf_project.delete_cube(group_name)
    try:
        hdf_project.get_data(group_name, items={})
        assert False
    except KeyError:
        assert True

def test_set_wrong_dimension_data(hdf_project):
    group_name = 'Project Data'
    indices = {'first':d('1'), 'second':'a', 'test':d('1.0'), 'another':d('1')}
    try:
        hdf_project.set_dataset(group_name, indices, arange(1))
        assert False
    except ValueError:
        assert True

def test_create_overlapping_datasets(hdf_project):
    try:
        group_name = 'Project Data'
        hdf_project.create_dataset(group_name, ['first',[d('1'), d('2'),
            d('7.0')]], ['second',['a', 'b', 'c']], ['test',[d('1.0'),
                d('2.0'), d('3.0')]], ['another',[d('1'), d('2.0'), '3',
                    d('4')]])
        assert False
    except ValueError:
        assert True

def test_create_non_overlapping_datasets(hdf_project):
    ''' This should prove that the integer and float index labels are
    different :-)

    '''
    group_name = 'Project Data'
    hdf_project.create_dataset(group_name, ['first',[d('1'), d('2'), d('7.0')]],
            ['second',['a', 'b', 'c']], ['test',[d('1.0'), d('2.0'), d('3.0')]],
            ['another',[d('1.1'), d('2.1'), d('3.1'), d('4.1')]])
    assert True
    
def test_create_dataset_lacking_dimension(hdf_project):
    try:
        group_name = 'Project Data'
        hdf_project.create_dataset(group_name, ['first',[d('1'), d('2'),
            d('7.0')]], ['second',['a', 'b', 'c']], ['test',[d('1.0'),
                d('2.0'), d('3.0')]])
        assert False
    except ValueError:
        assert True

def test_create_dataset_wrong_dimension(hdf_project):
    try:
        group_name = 'Project Data'
        hdf_project.create_dataset(group_name, ['first',[d('1'), d('2'),
            d('7.0')]], ['second',['a', 'b', 'c']], ['test',[d('1.0'),
                d('2.0'), d('3.0')]], ['wrong',[d('1.1'), d('2.1'), d('3.1'),
                    d('4.1')]])
        assert False
    except ValueError:
        assert True

def test_get_data(hdf_project):
    h = hdf_project
    group_name = 'Project Data'
    assert h.get_data(group_name, {'first':d('1'),'test':d('3.0'),
        'another':d('1'), 'second':'c'})[0] == 32

def test_get_data_fill_with_nan():
    if os.path.exists('project.hdf5'):
        os.remove('project.hdf5')
    hdf = Hdf5('project')
    two_d_name = '2d'
    hdf.create_dataset(two_d_name, ['x', [d('1'), d('2'), d('3'), d('4')]],
            ['y', [d('1'), d('2'), d('3'), d('4')]])
    hdf.create_dataset(two_d_name, ['x', [d('10')]], ['y', [d('10')]])
    hdf.set_dataset(two_d_name, {'x':d('1'), 'y':d('1')},
            5*arange(4*4).reshape((4,4)))
    data = hdf.get_data_fill_with_nan(two_d_name, items={})[0][...].flat
    expected = array([[0, 5, 10, 15, NaN], [20, 25, 30, 35, NaN], [40, 45, 50,
        55, NaN], [60, 65, 70, 75, NaN], [NaN, NaN, NaN, NaN, 0]]).flat

    #nan == nan is False
    assert all((x == y) or (isnan(x) and isnan(y)) for x,y in zip(data,
        expected))

def pytest_funcarg__function(request):
    my_sum = Sum('python.test.sum', [], ['Project Data', 'ds'], ['sum'])
    return my_sum

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
    hdf_project.execute_function(function)
    name = function.output_cube_names[0]
    data = hdf_project.get_data(name, items={})[0].flat
    expected = array([0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0,
        20.0, 22.0, 24.0, 26.0, 28.0, 30.0, 32.0, 34.0, 36.0, 38.0, 40.0, 42.0,
        44.0, 46.0, 48.0, 50.0, 52.0, 54.0, 56.0, 58.0, 60.0, 62.0, 64.0, 66.0,
        68.0, 70.0, 72.0, 74.0, 76.0, 78.0, 80.0, 82.0, 84.0, 86.0, 88.0, 90.0,
        92.0, 94.0, 48.0, 59.0, 70.0, 81.0, 92.0, 103.0, 114.0, 125.0, 112.0,
        114.0, 116.0, 118.0, 120.0, 122.0, 124.0, 126.0, 128.0, 130.0, 132.0,
        134.0, 136.0, 138.0, 140.0, 142.0, 144.0, 146.0, 148.0, 150.0, 152.0,
        154.0, 156.0, 158.0, 160.0, 162.0, 164.0, 166.0, 164.0, 175.0, 186.0,
        197.0, 208.0, 219.0, 230.0, 241.0, 184.0, 186.0, 188.0, 190.0, 192.0,
        194.0, 196.0, 198.0, 200.0, 202.0, 204.0, 206.0, 208.0, 210.0, 212.0,
        214.0]).flat
    assert all(x == y for x, y in zip(data, expected))

def test_recompute(hdf_project, function):
    h, mysum = hdf_project, function
    h.add_function(mysum)
    h.recompute()
    with h5py.File(h.filename, 'a') as f:
        assert f.get(mysum.output_cube_names[0]).attrs['dirty'] == False

def test_execute_fail_index_labels(hdf_project, function):
    h, my_sum = hdf_project, function
    h.create_dataset('fail', ['first_fail',[d('1'), d('2'), d('7.0')]],
            ['second',['a', 'b', 'c']], ['test',[d('1.0'), d('2.0'),
                d('3.0')]], ['another',[d('1'), d('2.0'), '3', d('4')]])
    my_sum.input_cube_names = [my_sum.input_cube_names[0], 'fail']
    h.add_function(my_sum)
    try:
        h.execute_function(my_sum)
        assert False
    except ValueError:
        assert True

