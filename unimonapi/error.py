# -*- coding: utf-8 -*-

import traceback

class UnimonError(Exception):

    def __init__(self, message, derivative = False):
        self.message = message
        if derivative:
            self.message += '\n\t' + traceback.format_exc().replace('\n', '\n\t').strip()

    def __unicode__(self):
        return unicode(self.message)

    def __str__(self):
        return unicode(self.message).encode('utf-8')

class NotImplemented(UnimonError):
    pass

class WrongIpRange(UnimonError):
    pass

