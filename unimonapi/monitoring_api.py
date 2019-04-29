# -*- coding: utf-8 -*-

from error import NotImplemented

class MonitoringAPI:
    """ This class is an interface to be implemented by derived custom monitoring API class. """

    # Agent installation result codes
    [ UNKNOWN_ERROR, INSTALL_SUCCESS, WRONG_INPUT_NUMBER, CONNECT_FAIL, AUTH_FAIL,
        REPO_MISSING, NOT_STARTED, NOT_INSTALLED, ALREADY_INSTALLED, UNSUPPORTED_OS ] = range(-1, 9)

    def __init__(self, *args, **kwargs):
        """ Initialize Monitoring API instance. """
        pass

    def get_max_discovery_address_number(self):
        ''' Return maximum total number of discovered IP-addresses supported (zero means unlimited). '''
        raise NotImplemented('MonitoringAPI method "get_max_discovery_address_number" is not implemented')

    def get_discovery_ip_range(self):
        """ Return current network discovery IP range in the format of string: 192.168.1.33, 192.168.1-10.1-255, 192.168.4.0/24
        """
        raise NotImplemented('MonitoringAPI method "get_discovery_ip_range" is not implemented')

    def start_discovery(self, ip_range=None):
        """ Start network discovery and update an IP range if specified.
            Raise WrongIpRange if could not parse IP range.
            :param ip_range:            (string) IP range to use (support the formats: 192.168.1.33, 192.168.1-10.1-255, 192.168.4.0/24)
        """
        raise NotImplemented('MonitoringAPI method "start_discovery" is not implemented')

    def stop_discovery(self):
        """ Stop network discovery. """
        raise NotImplemented('MonitoringAPI method "stop_discovery" is not implemented')

    def get_problems(self, severities=None, groups=None):
        """ Return a list of actual problems (Event objects) with severity not lower than specified.
            :param severities:        (list of int) severity list of problems to be returned (possible values are Event.SEVERITY_ICONS.keys()), None means all possible
            :param groups:            (list of strings) host group ids of problems to be returned, None means all possible
        """
        raise NotImplemented('MonitoringAPI method "get_problems" is not implemented')

    def get_summary(self, severities):
        """ Return a list of HostGroup objects with at least one problem with severity not lower than specified.
            :param severities:        (list of int) severity list of groups to be returned (possible values are Event.SEVERITY_ICONS.keys())
        """
        raise NotImplemented('MonitoringAPI method "get_summary" is not implemented')

    def get_supported_agent_os(self):
        """ Return a list of supported operating system types to install monitoring agent by install_agent method. """
        raise NotImplemented('MonitoringAPI method "get_supported_agent_os" is not implemented')

    def install_agent(self, os_type, hostname, user, password):
        """ Install monitoring agent to the specified host and add it to the monitored host list. Return integer (one of installation result codes).
            :param os_type:            (int) operating system type of the specified host (possible values are get_supported_agent_os())
            :param hostname:        (string) hostname of the host to install agent to
            :param user:            (string) user name of the host to install agent to
            :param password:        (string) password of the specified user
        """
        raise NotImplemented('MonitoringAPI method "install_agent" is not implemented')

    def get_available_host_groups(self):
        """ Return a list of available host groups for assigning to a host. """
        raise NotImplemented('MonitoringAPI method "get_available_host_groups" is not implemented')

    def add_host(self, name, groups):
        """ Create a new host and add it to the specified groups. Return new host id (string).
            :param name:            (string) host name
            :param groups:            (list of strings) list of groups the host to be added to (possible values are get_available_host_groups())
        """
        raise NotImplemented('MonitoringAPI method "add_host" is not implemented')

    def get_host_name(self, id):
        """ Return a host name by id or None if not found.
            :param id:            (string) host id
        """
        raise NotImplemented('MonitoringAPI method "get_host_name" is not implemented')

    def get_host_id(self, name):
        """ Return a host id by name or None if not found.
            :param name:            (string) host name
        """
        raise NotImplemented('MonitoringAPI method "get_host_id" is not implemented')

    def delete_host(self, id):
        """ Delete a host by id.
            :param id:            (string) host id to be deleted
        """
        raise NotImplemented('MonitoringAPI method "delete_host" is not implemented')

    def export_config(self, auto_created=False):
        """ Return a dictionary with all configurations from monitoring system via API.
            :param auto_created:            (bool) export auto-created/discovered/temporary configurations
        """
        raise NotImplemented('MonitoringAPI method "export_config" is not implemented')

    def import_config(self, config, overwrite=True, delete=False):
        """ Import specified configurations to monitoring system via API
            :param config:        (dict) configurations to be imported
            :param overwrite:    (bool) overwrite existing configurations
            :param delete:        (bool) delete existing configurations that are not specified for importing
        """
        raise NotImplemented('MonitoringAPI method "import_config" is not implemented')
