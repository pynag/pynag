from pynag.Parsers import retention_dat
from pynag.Parsers import main


class StatusDat(retention_dat.RetentionDat):

    """ Easy way to parse status.dat file from nagios

    After calling parse() contents of status.dat are kept in status.data
    Example usage::

        >>> s = StatusDat()
        >>> s.parse()
        >>> keys = s.data.keys()
        >>> 'info' in keys
        True
        >>> 'programstatus' in keys
        True
        >>> for service in s.data.get('servicestatus',[]):
        ...     host_name=service.get('host_name', None)
        ...     description=service.get('service_description',None)

    """

    def __init__(self, filename=None, cfg_file=None):
        """ Initilize a new instance of status

        Args (you only need to provide one of these):

            filename: path to your status.dat file

            cfg_file: path to your nagios.cfg file, path to status.dat will be
            looked up in this file

        """
        # If filename is not provided, lets try to discover it from
        # nagios.cfg
        if filename is None:
            main_config = pynag.Parsers.main.MainConfig(cfg_file)
            filename = main_config.get("status_file")

        self.filename = filename
        self.data = None

    def get_contactstatus(self, contact_name):
        """ Returns a dictionary derived from status.dat for one particular contact

        Args:

            contact_name: `contact_name` field of the contact's status.dat data
            to parse and return as a dict.

        Returns:

            dict derived from status.dat for the contact.

        Raises:

            ValueError if object is not found

        Example:

            >>> s = StatusDat()
            >>> s.get_contactstatus(contact_name='invalid_contact')
            ValueError('invalid_contact',)
            >>> first_contact = s.data['contactstatus'][0]['contact_name']
            >>> s.get_contactstatus(first_contact)['contact_name'] == first_contact
            True

        """
        if self.data is None:
            self.parse()
        for i in self.data['contactstatus']:
            if i.get('contact_name') == contact_name:
                return i
        return ValueError(contact_name)

    def get_hoststatus(self, host_name):
        """ Returns a dictionary derived from status.dat for one particular contact

        Args:

            host_name: `host_name` field of the host's status.dat data
            to parse and return as a dict.

        Returns:

            dict derived from status.dat for the host.

        Raises:

            ValueError if object is not found
        """
        if self.data is None:
            self.parse()
        for i in self.data['hoststatus']:
            if i.get('host_name') == host_name:
                return i
        raise ValueError(host_name)

    def get_servicestatus(self, host_name, service_description):
        """ Returns a dictionary derived from status.dat for one particular service

        Args:

            service_name: `service_name` field of the host's status.dat data
            to parse and return as a dict.

        Returns:

            dict derived from status.dat for the service.

        Raises:

            ValueError if object is not found
        """
        if self.data is None:
            self.parse()
        for i in self.data['servicestatus']:
            if i.get('host_name') == host_name:
                if i.get('service_description') == service_description:
                    return i
        raise ValueError(host_name, service_description)
