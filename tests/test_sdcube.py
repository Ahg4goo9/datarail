import os
from decimal import Decimal as d
from hdf import SdCube

def pytest_funcarg__simple_sdcube(request):
    filename = 'myfile.hdf5'
    if os.path.exists(filename):
        os.remove(filename)
    return SdCube('myName', filename, ['x', 'y', 'z'])
    

def test_sdcube_creation(simple_sdcube):
    if not simple_sdcube.mapping == {'x':0, 'y':1, 'z':2}:
        assert False

def test_mapping(simple_sdcube):
    try:
        simple_sdcube.mapping = {'x':1, 'y':2}
        assert False
    except ValueError:
        assert True
    simple_sdcube.mapping = {'EGF':0, 'h20':1}
    
    if not simple_sdcube.mapping == {'EGF':0, 'h20':1}:
        assert False

def test_units():
    filename = 'myfile.hdf5'
    if os.path.exists(filename):
        os.remove(filename)
    try:
        SdCube('myName', filename, ['x', 'y', 'z'], ['ng', 'mg/l'])
        assert False
    except ValueError:
        assert True
    cube = SdCube('myName', filename, ['x', 'y', 'z'], ['ng', 'mg/l', 'm'])
    if not cube.unit_mapping == ['ng', 'mg/l', 'm']:
        assert False

def test_create_dataset(simple_sdcube):
    try:
        simple_sdcube.create_dataset(
            {'first':[d('1'), d('2'), d('7.0')],
            'second':['a', 'b', 'c'],
            'test':[d('1.0'), d('2.0'), d('3.0')]})
        assert False
    except ValueError:
        assert True

    simple_sdcube.create_dataset(
            {'x':[d('1'), d('2'), d('7.0')],
            'y':['a', 'b', 'c'],
            'z':[d('1.0'), d('2.0'), d('3.0')]})

def test_loading(simple_sdcube):
    cube = SdCube.load(simple_sdcube.filename, simple_sdcube.name)
    if not simple_sdcube.mapping == {'x':0, 'y':1, 'z':2}:
        assert False

