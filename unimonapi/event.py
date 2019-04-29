# -*- coding: utf-8 -*-

from error import UnimonError
import emoji

class Event:
    ''' Universal monitoring event '''

    RESOLUTION, PROBLEM = range(2)
    NO_SEVERITY, INFO, WARNING, CRITICAL = range(-1, 3)
    SEVERITY_ICONS = {
        INFO:       emoji.emojize(':information_source:', use_aliases = True),
        WARNING:    emoji.emojize(':warning:', use_aliases = True),
        CRITICAL:   emoji.emojize(':no_entry:', use_aliases = True),
    }
    RESOLUTION_ICON = emoji.emojize(':white_check_mark:', use_aliases = True)

    def __init__(self, event_type, event_detailed, event_severity, event_host, event_text, event_id):
        """ Initialize event object.
            :param event_type:          (int) event type (RESOLUTION or PROBLEM)
            :param event_detailed:      (bool) whether event is detailed
            :param event_severity:      (int) event severity (one of defined in this class)
            :param event_host:          (string) host related to the event
            :param event_text:          (string) text description of the event
            :param event_id:            (string) unique identifier of the event
        """

        if event_severity not in self.SEVERITY_ICONS:
            raise UnimonError('Unsupported event severity "{}"'.format(str(event_severity)))
        if event_type not in [self.PROBLEM, self.RESOLUTION]:
            raise UnimonError('Unsupported event type "{}"'.format(str(event_type)))
        if type(event_detailed) != bool:
            raise UnimonError('Unsupported event detalization "{}"'.format(str(event_detailed)))

        self.type = event_type
        self.detailed = event_detailed
        self.severity = event_severity
        self.host = event_host
        self.text = event_text
        self.id = event_id

    def __unicode__(self):
        return u'{} {}: {}'.format(self.SEVERITY_ICONS[ self.severity ], self.host, self.text)

    def __str__(self):
        return unicode(self).encode('utf-8')