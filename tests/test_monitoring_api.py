import pytest
from inspect import getargspec
from unimonapi import MonitoringAPI
from unimonapi import NotImplemented

@pytest.fixture
def monitoring_api():
    return MonitoringAPI()

@pytest.fixture(params=[
    method for method in dir(MonitoringAPI)
    if callable(getattr(MonitoringAPI, method)) and not method.startswith('_')
])
def monitoring_api_method(request):
    '''Get all public methods' names of the MonitoringAPI class'''
    return request.param

def test_monitoring_api(monitoring_api, monitoring_api_method):
    '''Invoke every method with dummy arguments and assert that NotImplemented is raised'''
    method = getattr(monitoring_api, monitoring_api_method)
    dummy_arguments = getargspec(method).args[1:] # Skip 'self' argument
    with pytest.raises(NotImplemented, match='MonitoringAPI method "{}" is not implemented'.format(monitoring_api_method)):
        method(*dummy_arguments)
