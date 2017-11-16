# -*- coding: utf-8 -*-
"""Module for dealing with multiple Livestatus instances at once."""

from pynag.Parsers import livestatus
from pynag.Parsers import errors


class MultiSite(livestatus.Livestatus):

    """ Wrapps around multiple Livesatus instances and aggregates the results
        of queries.

        Example:
            >>> m = MultiSite()
            >>> m.add_backend(path='/var/spool/nagios/livestatus.socket', name='local')
            >>> m.add_backend(path='127.0.0.1:5992', name='remote')

    """

    def __init__(self, *args, **kwargs):
        super(MultiSite, self).__init__(*args, **kwargs)
        self.backends = {}

    def add_backend(self, path, name):
        """ Add a new livestatus backend to this instance.

         Arguments:
            path (str):  Path to file socket or remote address
            name (str):  Friendly shortname for this backend
        """
        backend = livestatus.Livestatus(
            livestatus_socket_path=path,
            nagios_cfg_file=self.nagios_cfg_file,
            authuser=self.authuser
        )
        self.backends[name] = backend

    def get_backends(self):
        """ Returns a list of mk_livestatus instances

        Returns:
            list. List of mk_livestatus instances
        """
        return self.backends

    def get_backend(self, backend_name):
        """ Return one specific backend that has previously been added
        """
        if not backend_name:
            return list(self.backends.values())[0]
        try:
            return self.backends[backend_name]
        except KeyError:
            # TODO: Raise a more specific error.
            raise errors.ParserError("No backend found with name='%s'" % backend_name)

    def query(self, query, *args, **kwargs):
        """ Behaves like mk_livestatus.query() except results are aggregated from multiple backends

        Arguments:
            backend (str): If specified, fetch only data from this backend (see add_backend())
            *args:         Passed directly to mk_livestatus.query()
            **kwargs:      Passed directly to mk_livestatus.query()
        """
        result = []
        backend = kwargs.pop('backend', None)

        # Special hack, if 'Stats' argument was provided to livestatus
        # We have to maintain compatibility with old versions of livestatus
        # and return single list with all results instead of a list of dicts
        doing_stats = any([x.startswith('Stats:') for x in args + (query,)])

        # Iterate though all backends and run the query
        # TODO: Make this multithreaded
        for name, backend_instance in list(self.backends.items()):
            # Skip if a specific backend was requested and this is not it
            if backend and backend != name:
                continue

            query_result = backend_instance.query(query, *args, **kwargs)
            if doing_stats:
                result = self._merge_statistics(result, query_result)
            else:
                for row in query_result:
                    row['backend'] = name
                    result.append(row)

        return result

    def _merge_statistics(self, list1, list2):
        """ Merges multiple livestatus results into one result

        Arguments:
            list1 (list): List of integers
            list2 (list): List of integers

        Returns:
            list. Aggregated results of list1 + list2
        Example:
            >>> result1 = [1,1,1,1]
            >>> result2 = [2,2,2,2]
            >>> MultiSite()._merge_statistics(result1, result2)
            [3, 3, 3, 3]

        """
        if not list1:
            return list2
        if not list2:
            return list1

        number_of_columns = len(list1)
        result = [0] * number_of_columns
        for row in (list1, list2):
            for i, column in enumerate(row):
                result[i] += column
        return result

    def get_host(self, host_name, backend=None):
        """ Same as Livestatus.get_host() """
        backend = self.get_backend(backend)
        return backend.get_host(host_name)

    def get_service(self, host_name, service_description, backend=None):
        """ Same as Livestatus.get_service() """
        backend = self.get_backend(backend)
        return backend.get_service(host_name, service_description)

    def get_contact(self, contact_name, backend=None):
        """ Same as Livestatus.get_contact() """
        backend = self.get_backend(backend)
        return backend.get_contact(contact_name)

    def get_contactgroup(self, contactgroup_name, backend=None):
        """ Same as Livestatus.get_contact() """
        backend = self.get_backend(backend)
        return backend.get_contactgroup(contactgroup_name)

    def get_servicegroup(self, servicegroup_name, backend=None):
        """ Same as Livestatus.get_servicegroup() """
        backend = self.get_backend(backend)
        return backend.get_servicegroup(servicegroup_name)

    def get_hostgroup(self, hostgroup_name, backend=None):
        """ Same as Livestatus.get_hostgroup() """
        backend = self.get_backend(backend)
        return backend.get_hostgroup(hostgroup_name)


