# -*- coding: utf-8 -*-

from event import Event
from error import UnimonError

class HostGroup:

    def __init__(self, group_name, group_id):
        self.name = group_name
        self.id = group_id
        self.severity = Event.NO_SEVERITY
        self.problems = 0
        self.problems_by_severity = {}

        for severity in Event.SEVERITY_ICONS:
            self.problems_by_severity[severity] = 0

    def __unicode__(self):
        if self.severity in Event.SEVERITY_ICONS:
            group_str = Event.SEVERITY_ICONS[self.severity] + self.name
        else:
            group_str = self.name

        return group_str

    def __str__(self):
        return unicode(self).encode('utf-8')

    def count_problem(self, severity):
        if severity not in Event.SEVERITY_ICONS:
            raise UnimonError('Unsupported problem severity "{}"'.format(str(severity)))
        elif severity > self.severity:
            self.severity = severity

        self.problems += 1
        self.problems_by_severity[severity] += 1