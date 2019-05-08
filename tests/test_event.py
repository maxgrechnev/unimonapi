import pytest
from unimonapi import Event
from unimonapi import UnimonError

@pytest.fixture
def critical_event():
    return Event(Event.PROBLEM, True, Event.CRITICAL, 'host', 'text', 'id')

def test_event_init(critical_event):
    assert critical_event.type == Event.PROBLEM
    assert critical_event.detailed == True
    assert critical_event.severity == Event.CRITICAL
    assert critical_event.host == 'host'
    assert critical_event.text == 'text'
    assert critical_event.id == 'id'

def test_event_type_unsupported():
    with pytest.raises(UnimonError, match=r'Unsupported event type "unsupported"'):
        Event('unsupported', True, Event.CRITICAL, 'host', 'text', 'id')

def test_event_detailed_unsupported():
    with pytest.raises(UnimonError, match=r'Unsupported event detalization "unsupported"'):
        Event(Event.PROBLEM, 'unsupported', Event.CRITICAL, 'host', 'text', 'id')

def test_event_severity_unsupported():
    with pytest.raises(UnimonError, match=r'Unsupported event severity "unsupported"'):
        Event(Event.PROBLEM, True, 'unsupported', 'host', 'text', 'id')

def test_event_unicode(critical_event):
    event_unicode = unicode(critical_event)
    assert event_unicode == u'\u26d4 host: text'

def test_event_str(critical_event):
    event_unicode = str(critical_event)
    assert event_unicode == '\xe2\x9b\x94 host: text'
