import pytest
from unimonapi import UnimonError

def test_error_init():
    error = UnimonError('message')
    assert error.message == 'message'
    assert unicode(error) == u'message'
    assert str(error) == 'message'

def test_error_derivative():
    try:
        raise Exception('original')
    except Exception:
        error = UnimonError('derivative', derivative=True)

    assert error.message[:10] == 'derivative'
    assert error.message[-19:] == 'Exception: original'
