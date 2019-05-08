import pytest
from inspect import getargspec
from unimonapi import MonitoringAPI
from unimonapi import NotImplemented

@pytest.fixture
def monitoring_api():
    return MonitoringAPI()

@pytest.fixture(params=dir(MonitoringAPI))
def monitoring_api_attr(request):
    return request.param

def test_monitoring_api(monitoring_api, monitoring_api_attr):
    method = getattr(monitoring_api, monitoring_api_attr)
    if not callable(method):
        pytest.skip('Attribute "{}" is not a method'.format(monitoring_api_attr))
    if monitoring_api_attr.startswith('_'):
        pytest.skip('Method "{}" is private'.format(monitoring_api_attr))
    argument_number = len(getargspec(method).args) - 1  # Skip 'self' argument
    arguments = range(argument_number)
    with pytest.raises(NotImplemented, match='MonitoringAPI method "{}" is not implemented'.format(monitoring_api_attr)):
        method(*arguments)
