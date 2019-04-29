import pytest
from unimonapi import Event

@pytest.fixture
def event():
    return Event(Event.PROBLEM, True, Event.CRITICAL, 'host', 'text', 'id')

def test_event_type(event):
    assert event.type == Event.PROBLEM

def test_event_detailed(event):
    assert event.detailed == True

def test_event_severity(event):
    assert event.severity == Event.CRITICAL

def test_event_host(event):
    assert event.host == 'host'

def test_event_text(event):
    assert event.text == 'text'

def test_event_id(event):
    assert event.id == 'id'
