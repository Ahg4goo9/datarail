import os
from decimal import Decimal as d
from numpy import arange
from hdf import SdCube

def pytest_funcarg__simple_sdcube(request):
    filename = 'myfile.hdf5'
    if os.path.exists(filename):
        os.remove(filename)
    return SdCube('myName', filename, ['x', 'y', 'z'])
    
def pytest_funcarg__filled_sdcube(request):
    filename = 'myfile.hdf5'
    if os.path.exists(filename):
        os.remove(filename)
    filled_sdcube = SdCube('filled', filename, ['x', 'y', 'z'])
    filled_sdcube.create_dataset(
        {'x':[d('1'), d('2'), d('7.0')],
        'y':['a', 'b', 'c'],
        'z':[d('1.0'), d('2.0'), d('3.0')]})
    return filled_sdcube

def pytest_funcarg__filled_complicated_sdcube(request):
    filename = 'myfile.hdf5'
    if os.path.exists(filename):
        os.remove(filename)
    filled_sdcube = SdCube('filled', filename, ['x', 'y'])
    filled_sdcube.create_dataset(
        {'x':[d('1'), d('2')],
        'y':['a', 'b', 'c']})
    filled_sdcube.set_data({'x':d('1'), 'y':'a'}, arange(2*3).reshape((2,3)))
    filled_sdcube.create_dataset(
        {'x':[d('3')],
        'y':['a', 'b', 'c']})
    filled_sdcube.set_data({'x':d('3'), 'y':'a',}, 7 +
            arange(1*3).reshape((1,3)))
    filled_sdcube.create_dataset(
        {'x':[d('3')],
        'y':['d', 'e', 'f']})
    filled_sdcube.set_data({'x':d('3'), 'y':'d'}, 11 +
            arange(1*3).reshape((1,3)))
    filled_sdcube.create_dataset(
        {'x':[d('1'), d('2'), d('5')],
        'y':['d', 'e']})
    filled_sdcube.set_data({'x':d('1'), 'y':'d'}, 15 +
            arange(3*2).reshape((3,2)))

    # And this is what it looks like
    #          y
    #     a  b  c  d  e  f #
    #----------------------#
    # |1| 0  1  2  15 16   #
    # |2| 3  4  5  17 18   #
    #x|3| 7  8  9  11 12 13#
    # |5|          19 20   #
    ########################

    return filled_sdcube

#def test_sdcube_creation(simple_sdcube):
#    if not simple_sdcube.mapping == {'x':0, 'y':1, 'z':2}:
#        assert False
#
#def test_mapping(simple_sdcube):
#    try:
#        simple_sdcube.mapping = {'x':1, 'y':2}
#        assert False
#    except ValueError:
#        assert True
#    simple_sdcube.mapping = {'EGF':0, 'h20':1}
#    
#    if not simple_sdcube.mapping == {'EGF':0, 'h20':1}:
#        assert False
#
#def test_units():
#    filename = 'myfile.hdf5'
#    if os.path.exists(filename):
#        os.remove(filename)
#    try:
#        SdCube('myName', filename, ['x', 'y', 'z'], ['ng', 'mg/l'])
#        assert False
#    except ValueError:
#        assert True
#    cube = SdCube('myName', filename, ['x', 'y', 'z'], ['ng', 'mg/l', 'm'])
#    if not cube.unit_mapping == ['ng', 'mg/l', 'm']:
#        assert False
#
#def test_create_dataset(simple_sdcube):
#    try:
#        simple_sdcube.create_dataset(
#            {'first':[d('1'), d('2'), d('7.0')],
#            'second':['a', 'b', 'c'],
#            'test':[d('1.0'), d('2.0'), d('3.0')]})
#        assert False
#    except ValueError:
#        assert True
#
#    simple_sdcube.create_dataset(
#            {'x':[d('1'), d('2'), d('7.0')],
#            'y':['a', 'b', 'c'],
#            'z':[d('1.0'), d('2.0'), d('3.0')]})
#
#def test_set_get_data(filled_sdcube):
#    data = arange(3*3*3).reshape((3,3,3))
#    filled_sdcube.set_data({'x':d('1'), 'y':'a', 'z':d('1.0')}, data)
#    stored_data = filled_sdcube.get_data()[0].flat
#    assert all(x == y for x, y in zip(data.flat, stored_data))
#
#def test_set_too_big_data(filled_sdcube):
#    data = arange(3*3*4).reshape((3,3,4))
#    try:
#        filled_sdcube.set_data({'x':d('1'), 'y':'a', 'z':d('1.0')}, data)
#        assert False
#    except ValueError:
#        assert True
#
#def test_set_data_to_nonexisting_dataset(simple_sdcube):
#    data = arange(3*3*3).reshape((3,3,3))
#    try:
#        simple_sdcube.set_data({'x':d('1'), 'y':'a', 'z':d('1.0')}, data)
#        assert False
#    except ValueError:
#        assert True
#
#def test_get_data_with_items(filled_sdcube):
#    data = arange(3*3*3).reshape((3,3,3))
#    filled_sdcube.set_data({'x':d('1'), 'y':'a', 'z':d('1.0')}, data)
#
#    stored_data = filled_sdcube.get_data(items={'x':d('1')})[0].flat
#    assert all(x == y for x, y in zip(data[0,:,:].flat, stored_data))
#
#    stored_data = filled_sdcube.get_data(items={'x':d('1'), 'y':'a'})[0].flat
#    assert all(x == y for x, y in zip(data[0,0,:].flat, stored_data))
#
#    stored_data = filled_sdcube.get_data(items={'x':d('1'), 'y':'a',
#    'z':d('3.0')})[0].flat
#    assert all(x == y for x, y in zip(data[0,0,2].flat, stored_data))

def test_get_data_complex(filled_complicated_sdcube):
    cube = filled_complicated_sdcube
    
    # And this is what it looks like
    #          y
    #     a  b  c  d  e  f #
    #----------------------#
    # |1| 0  1  2  15 16   #
    # |2| 3  4  5  17 18   #
    #x|3| 7  8  9  11 12 13#
    # |5|          19 20   #
    ########################

    for char in ['a', 'b', 'c', 'd', 'e', 'f']:
        print cube.get_data(items={'y':char})
        print 'x'*20
    for char in [1, 2, 3, 5]:
        print cube.get_data(items={'x':char})
        print 'x'*20

#def test_loading(simple_sdcube):
#    cube = SdCube.load(simple_sdcube.filename, simple_sdcube.name)
#    if not simple_sdcube.mapping == {'x':0, 'y':1, 'z':2}:
#        assert False

