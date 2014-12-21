import socket
import sys
import time

import pynag.Parsers.errors
import pynag.Parsers.main
import pynag.Utils.paths

# TODO remove this and raise proper exceptions
from pynag.Parsers.errors import ParserError


class Error(ParserError):
    """Base class for errors in this module."""


class LivestatusNotConfiguredException(Error):
    """ This exception is raised if we tried to autodiscover path to livestatus and failed """


class LivestatusError(Error):
    """ Used when we get errors from Livestatus """


class InvalidResponseFromLivestatus(Error):
    """Used when an unparsable response comes out of livestatus"""
    def __init__(self, query, response, *args, **kwargs):
        self.query = query
        self.response = response
        super(InvalidResponseFromLivestatus, self).__init__(*args, **kwargs)

    def __str__(self):
        message = 'Could not parse response from livestatus.\nQuery:{query}\nResponse: {response}'
        return message.format(query=self.query, response=self.response)




class LivestatusQuery(object):
    """Convenience class to help construct a livestatus query.

    When talking to Livestatus we use the LQL - the Livestatus Query Language.

    Each query contains:
        * A Command in the form of 'GET <table>' (e.g. 'GET services')
        * Arbritary number of 'Header Lines' in the form of 'Header: Argument'
        * An Empty line, i.e. \n

    Example Livestatus Queries:
        'GET contacts\n'
        'GET contacts\nColumns: name alias\n'

    Examples on using this class:
        >>> query = LivestatusQuery('GET contacts')
        >>> query.get_query()
        'GET contacts\\n\\n'
        >>> query.set_outputformat('python')
        >>> query.get_query()
        'GET contacts\\nOutputFormat: python\\n\\n'

    For more information on Livestatus see:
        https://mathias-kettner.de/checkmk_livestatus.html
    """

    # The following constants describe names of specific
    # Livestatus headers:
    _RESPONSE_HEADER = 'ResponseHeader'
    _OUTPUT_FORMAT = 'OutputFormat'
    _COLUMNS = 'Columns'
    _COLUMN_HEADERS = 'ColumnHeaders'
    _LIMIT = 'Limit'
    _AUTH_USER = 'AuthUser'
    _STATS = 'Stats'
    _FILTER = 'Filter'
    _OR = 'Or'

    # How a header line is formatted in a query
    _FORMAT_OF_HEADER_LINE = '{keyword}: {arguments}'

    # How a typical filter statement looks like:
    __FILTER_STATEMENT = 'Filter: {attribute} = {value}'

    # This is a mapping from 'pynag style' attribute suffixes into appropriate
    # livestatus filter statement.
    __FILTER_TRANSMUTATION_SUFFIX = {
        '__contains': 'Filter: {attribute} ~~ {value}',
        '__has_field': 'Filter: {attribute} >= {value}',
        '__isnot': 'Filter: {attribute} != {value}',
        '__startswith': 'Filter: {attribute} ~ ^{value}',
        '__endswith': 'Filter: {attribute} ~ {value}$',
        '__regex': 'Filter: {attribute} ~ {value}',
        '__gt': 'Filter: {attribute} > {value}',
        '__lt': 'Filter: {attribute} < {value}',
    }

    def __init__(self, query, *args, **kwargs):
        """Create a new LivestatusQuery.

        Args:
            query: String. Initial query (like GET hosts).
                Technically any object (not only str) having a `splitlines`
                method (accepting no arguments) and returning an iterable will be handled as well.
            *args: String. Any args will appended to the query as additional headers.
            **kwargs: String. Any kwargs will be treated like additional filter to our query.

        Examples:
            >>> query = LivestatusQuery('GET services')
            >>> query.get_query()
            'GET services\\n\\n'

            >>> query = LivestatusQuery('GET services', 'OutputFormat: json')
            >>> query.get_query()
            'GET services\\nOutputFormat: json\\n\\n'

            >>> query = LivestatusQuery('GET services', 'Columns: service_description', host_name='localhost')
            >>> query.get_query()
            'GET services\\nColumns: service_description\\nFilter: host_name = localhost\\n\\n'
        """
        self._query = []

        # We purposefully strip white space, extra line breaks will
        # be added to the query string when get_query() is called.
        for header_line in query.strip().splitlines():
            self.add_header_line(header_line)

        for header_line in args:
            self.add_header_line(header_line)
        self.add_filters(**kwargs)

    def __eq__(self, other):
        return self._query == other._query

    def _join_arguments_with_or(self, *args):
        """join multiple Livestatus Filter statements with a logical OR.

        Args:
            *args: List of strings like: ['Filter: state = 0', 'Filter: state = 1']

        Returns:
            List of strings. Same as args except 'Or: %s' % len(args) is added to the list.

        Examples:
            >>> query = LivestatusQuery('')
            >>> query._join_arguments_with_or('', '', '')
            ['', '', '', 'Or: 3']
            >>> query._join_arguments_with_or('')
            ['']

        """
        args = list(args)
        length_of_arguments = len(args)
        if length_of_arguments > 1:
            or_statement = 'Or: %s' % len(args)
            args.append(or_statement)
        return args

    def get_query(self):
        """Get a string representation of our query

        Example:
            >>> query = LivestatusQuery('GET services')
            >>> query.get_query()
            'GET services\\n\\n'
            >>> query.add_header('Filter', 'host_name = foo')
            >>> query.get_query()
            'GET services\\nFilter: host_name = foo\\n\\n'

        Returns:
            A string. String representation of our query that is compatibe
            with livestatus.

        """
        return '\n'.join(self._query) + '\n\n'

    def get_header(self, keyword):
        """Get first header found with keyword in it.

        Examples:
            >>> query = LivestatusQuery('GET services')
            >>> query.get_header('OutputFormat')  # Returns None
            >>> query.set_outputformat('python')
            >>> query.get_header('OutputFormat')
            'python'

        """
        signature = keyword + ':'
        for header in self._query:
            if header.startswith(signature):
                argument = header.split(':', 1)[1]
                argument = argument.strip()
                return argument

    def column_headers(self):
        """Check if ColumnHeaders are on or off.

        Example:
            >>> query = LivestatusQuery('GET services')
            >>> query.column_headers() # If not set, they are off
            False
            >>> query.set_columnheaders('on')
            >>> query.column_headers()
            True

        """
        column_headers = self.get_header(self._COLUMN_HEADERS)
        if not column_headers or column_headers == 'off':
            return False
        if column_headers == 'on':
            return True
        raise LivestatusError("Not sure if ColumnHeaders are on or off, got '%s'" % column_headers)

    def output_format(self):
        """Return the currently configured OutputFormat if any is set.

         Examples:
             >>> query = LivestatusQuery('GET services')
             >>> query.output_format()  # Returns None
             >>> query.set_outputformat('python')
             >>> query.output_format()
             'python'

        """
        return self.get_header(self._OUTPUT_FORMAT)

    def add_header_line(self, header_line):
        """Add a new header line to our livestatus query

        Example:
            >>> query = LivestatusQuery('GET services')
            >>> query.add_header_line('Filter: host_name = foo')
            >>> query.get_query()
            'GET services\\nFilter: host_name = foo\\n\\n'
        """
        self._query.append(header_line)

    def add_header(self, keyword, arguments):
        """Add a new header to our livestatus query.

        Example:
            >>> query = LivestatusQuery('GET services')
            >>> query.add_header('Filter', 'host_name = foo')
            >>> query.get_query()
            'GET services\\nFilter: host_name = foo\\n\\n'
        """
        header_line = self._FORMAT_OF_HEADER_LINE.format(keyword=keyword, arguments=arguments)
        self.add_header_line(header_line)

    def has_header(self, keyword):
        """ Returns True if specific header is in current query.

        Examples:
            >>> query = LivestatusQuery('GET services')
            >>> query.has_header('OutputFormat')
            False
            >>> query.add_header('OutputFormat', 'fixed16')
            >>> query.has_header('OutputFormat')
            True

        """
        signature = keyword + ':'
        for row in self._query:
            if row.startswith(signature):
                return True
        return False

    def remove_header(self, keyword):
        """Remove a header from our query

        Examples:
            >>> query = LivestatusQuery('GET services')
            >>> query.has_header('OutputFormat')
            False
            >>> query.add_header('OutputFormat', 'fixed16')
            >>> query.has_header('OutputFormat')
            True
            >>> query.remove_header('OutputFormat')
            >>> query.has_header('OutputFormat')
            False

        """
        signature = keyword + ':'
        self._query = filter(lambda x: not x.startswith(signature), self._query)

    def set_responseheader(self, response_header='fixed16'):
        """Set ResponseHeader to our query.

        Args:
            response_header: String. Response header that livestatus knows. Example: fixed16

        Example:
            >>> query = LivestatusQuery('GET services')
            >>> query.set_responseheader()
            >>> query.get_query()
            'GET services\\nResponseHeader: fixed16\\n\\n'
        """
        # First remove whatever responseheader might have been set before
        self.remove_header(self._RESPONSE_HEADER)
        self.add_header(self._RESPONSE_HEADER, response_header)

    def set_outputformat(self, output_format):
        """Set OutFormat header in our query.

        Example:
            >>> query = LivestatusQuery('GET services')
            >>> query.set_outputformat('json')
            >>> query.get_query()
            'GET services\\nOutputFormat: json\\n\\n'
        """
        # Remove outputformat if it was already in out query
        self.remove_header(self._OUTPUT_FORMAT)
        self.add_header(self._OUTPUT_FORMAT, output_format)

    def set_columnheaders(self, status='on'):
        """Turn on or off ColumnHeaders

        Example:
            >>> query = LivestatusQuery('GET services')
            >>> query.set_columnheaders('on')
            >>> query.get_query()
            'GET services\\nColumnHeaders: on\\n\\n'
            >>> query.set_columnheaders('off')
            >>> query.get_query()
            'GET services\\nColumnHeaders: off\\n\\n'
        """
        self.remove_header(self._COLUMN_HEADERS)
        self.add_header(self._COLUMN_HEADERS, status)

    def set_authuser(self, auth_user):
        """Set AuthUser in our query.

        Example:
            >>> query = LivestatusQuery('GET services')
            >>> query.set_authuser('nagiosadmin')
            >>> query.get_query()
            'GET services\\nAuthUser: nagiosadmin\\n\\n'
        """
        self.remove_header(self._AUTH_USER)
        self.add_header(self._AUTH_USER, auth_user)

    def has_responseheader(self):
        """ Check if there are any ResponseHeaders set.

         Example:
            >>> query = LivestatusQuery('GET services')
            >>> query.has_responseheader()
            False
            >>> query.set_responseheader('fixed16')
            >>> query.has_responseheader()
            True

        Returns:
            Boolean. True if query has any ResponseHeader, otherwise False.
        """
        return self.has_header(self._RESPONSE_HEADER)

    def has_authuser(self):
        """ Check if AuthUser is set.

         Example:
            >>> query = LivestatusQuery('GET services')
            >>> query.has_authuser()
            False
            >>> query.set_authuser('nagiosadmin')
            >>> query.has_authuser()
            True

        Returns:
            Boolean. True if query has any AuthUser, otherwise False.
        """
        return self.has_header(self._AUTH_USER)

    def has_outputformat(self):
        """ Check if OutputFormat is set.

         Example:
            >>> query = LivestatusQuery('GET services')
            >>> query.has_outputformat()
            False
            >>> query.set_outputformat('python')
            >>> query.has_outputformat()
            True

        Returns:
            Boolean. True if query has any OutputFormat set, otherwise False.
        """
        return self.has_header(self._OUTPUT_FORMAT)

    def has_columnheaders(self):
        """ Check if there are any ColumnHeaders set.

         Example:
            >>> query = LivestatusQuery('GET services')
            >>> query.has_columnheaders()
            False
            >>> query.set_columnheaders('on')
            >>> query.has_columnheaders()
            True

        Returns:
            Boolean. True if query has any ColumnHeaders, otherwise False.
        """
        return self.has_header(self._COLUMN_HEADERS)

    def has_stats(self):
        """ Returns True if Stats headers are present in our query.

         Example:
            >>> query = LivestatusQuery('GET services')
            >>> query.has_stats()
            False
            >>> query.add_header('Stats', 'state = 0')
            >>> query.has_stats()
            True

        Returns:
            Boolean. True if query has any stats, otherwise False.
        """
        return self.has_header(self._STATS)

    def has_filters(self):
        """ Returns True if any filters are applied.

         Example:
            >>> query = LivestatusQuery('GET services')
            >>> query.has_filters()
            False
            >>> query.add_header('Filter', 'host_name = localhost')
            >>> query.has_filters()
            True

        Returns:
            Boolean. True if query has any filters, otherwise False.
        """
        return self.has_header(self._FILTER)

    def __str__(self):
        """Wrapper around self.get_query().

        Example:
            >>> query = LivestatusQuery('GET services', 'Columns: host_name')
            >>> str(query)
            'GET services\\nColumns: host_name\\n\\n'

        """
        return self.get_query()

    def splitlines(self, *args, **kwargs):
        """ Wrapper around str(self).splitlines().

         This function is here for backwards compatibility because a lot of callers were previously passing
         in strings, but are now passing in LivestatusQuery. For this purpose we behave like a string.

        Example:
            >>> query = LivestatusQuery('GET services', 'Columns: host_name')
            >>> query.splitlines()
            ['GET services', 'Columns: host_name', '']
        """
        querystring = str(self)
        return querystring.splitlines(*args, **kwargs)

    def split(self, *args, **kwargs):
        """ Wrapper around str(self).split().

         This function is here for backwards compatibility because a lot of callers were previously passing
         in strings, but are now passing in LivestatusQuery. For this purpose we behave like a string.

        Example:
            >>> query = LivestatusQuery('GET services', 'Columns: host_name')
            >>> query.split('\\n')
            ['GET services', 'Columns: host_name', '', '']
        """
        querystring = str(self)
        return querystring.split(*args, **kwargs)

    def strip(self, *args, **kwargs):
        """ Wrapper around str(self).strip().

         This function is here for backwards compatibility because a lot of callers were previously passing
         in strings, but are now passing in LivestatusQuery. For this purpose we behave like a string.

        Example:
           >>> query = LivestatusQuery('GET services')
           >>> str(query)
           'GET services\\n\\n'
           >>> query.strip()
           'GET services'

        """
        return str(self).strip(*args, **kwargs)

    def startswith(self, *args, **kwargs):
        """ Wrapper around str(self).startswith().

         This function is here for backwards compatibility because a lot of callers were previously passing
         in strings, but are now passing in LivestatusQuery. For this purpose we behave like a string.

        Example:
           >>> query = LivestatusQuery('GET services')
           >>> str(query)
           'GET services\\n\\n'
           >>> query.startswith('GET')
           True

        """
        return str(self).startswith(*args, **kwargs)

    def convert_key_value_to_filter_statement(self, attribute, value):
        """Convert a key/value pair to a Livestatus compatible Filter: statement.

        Args:
            attribute: String. Name of a single livestatus attribute, for example 'host_name'.
                the attribute can have a 'pynag style' suffix which is a hint to what kind of
                filtering will be applied. See the examples section for an idea how this is applied.
            value: String. Single value to filter by, for example: 'localhost'

        Returns:
            String. A single livestatus compatible filter statement. See Examples section for
            an idea of what return statement looks like.

        Examples:
            >>> query = LivestatusQuery('')
            >>> query.convert_key_value_to_filter_statement('host_name', 'test')
            'Filter: host_name = test'
            >>> query.convert_key_value_to_filter_statement('service_description__contains', 'serv')
            'Filter: service_description ~~ serv'
            >>> query.convert_key_value_to_filter_statement('service_description__isnot', 'serv')
            'Filter: service_description != serv'
            >>> query.convert_key_value_to_filter_statement('service_description__has_field', 'foo')
            'Filter: service_description >= foo'
            >>> query.convert_key_value_to_filter_statement('service_description__startswith', 'foo')
            'Filter: service_description ~ ^foo'
            >>> query.convert_key_value_to_filter_statement('service_description__endswith', 'foo')
            'Filter: service_description ~ foo$'
            >>> query.convert_key_value_to_filter_statement('state__gt', '0')
            'Filter: state > 0'
            >>> query.convert_key_value_to_filter_statement('state__lt', '1')
            'Filter: state < 1'

        """

        # Check if attribute ends with any of the suffixes in __FILTER_TRANSMUTATION_SUFFIX
        # For example if attribute ends with '__contains' we want the end result
        # to be 'Filter: attribute ~ value' (notice the ~ instead of =)
        for suffix, potential_filter_statement in self.__FILTER_TRANSMUTATION_SUFFIX.items():
            if attribute.endswith(suffix):
                suffix_length = len(suffix)
                attribute = attribute[:-suffix_length]
                filter_statement = potential_filter_statement
                break
        else:
            filter_statement = self.__FILTER_STATEMENT
        return filter_statement.format(attribute=attribute, value=value)

    def create_filter_statement(self, attribute, values):
        """Create a Livestatus filter statement from a key/value pair.

        Args:
          attribute: String. Name of a livestatus attribute, example: 'host_name'
          values: List of strings. If more than one value is provided the resulting filter
              query will be be joined with a logical OR.

        Returns:
          List of strings. List of Livestatus Filter statements. Look at Examples section
          for an idea of what return result looks like.

        Examples:
            >>> query = LivestatusQuery('')
            >>> query.create_filter_statement('host', 'localhost')
            ['Filter: host = localhost']
            >>> query.create_filter_statement('host', ['localhost', 'remote_host'])
            ['Filter: host = localhost', 'Filter: host = remote_host', 'Or: 2']

        """
        return_arguments = []
        if not isinstance(values, list):
            values = [values]
        for value in values:
            filter_statement = self.convert_key_value_to_filter_statement(attribute, value)
            return_arguments.append(filter_statement)
        if len(return_arguments) > 1:
            return_arguments = self._join_arguments_with_or(*return_arguments)
        return return_arguments

    def add_filter(self, attribute, value):
        """Adds a single filter statement to current query.

        Args:
            attribute. String. Attribute to search for.
            value: String. Value to search for.

        >>> query = LivestatusQuery('GET services')
        >>> query.add_filter('host_name', 'localhost')
        >>> query.get_query()
        'GET services\\nFilter: host_name = localhost\\n\\n'
        """
        filter_statements = self.create_filter_statement(attribute, value)
        for statement in filter_statements:
            self.add_header_line(statement)

    def add_filters(self, **kwargs):
        """Add a new filter statement to current query.

        Args:
         **kwargs: Every key/value pair is a string. See examples for ideas.

        >>> query = LivestatusQuery('GET services')
        >>> query.add_filters(host_name='localhost')
        >>> query.get_query()
        'GET services\\nFilter: host_name = localhost\\n\\n'
        >>> query.add_filters(description__contains='Ping')
        >>> query.get_query()
        'GET services\\nFilter: host_name = localhost\\nFilter: description ~~ Ping\\n\\n'
        """
        for key, value in kwargs.items():
            self.add_filter(key, value)

    def set_columns(self, *columns):
        """Set a Columns header to our query with the specified Columns.

        Args:
            *columns: List of strings. Examples: ['host_name','description']

        Examples:
            >>> query = LivestatusQuery('GET hosts')
            >>> query.set_columns('name', 'address')
            >>> query.get_query()
            'GET hosts\\nColumns: name address\\n\\n'
        """
        self.remove_header(self._COLUMNS)
        self.add_header(self._COLUMNS, ' '.join(columns))

    def add_or_statement(self, number):
        """Adds an OR statement to the current set of header lines.

        Args:
            number: Integer. Tells how many arguments should be joined together.
        Examples:
            >>> query = LivestatusQuery('GET hosts')
            >>> query.add_filters(name='localhost')
            >>> query.add_filters(name='otherhost')
            >>> query.add_or_statement(2)
            >>> query.get_query()
            'GET hosts\\nFilter: name = localhost\\nFilter: name = otherhost\\nOr: 2\\n\\n'

        """
        self.add_header(self._OR, number)

    def set_limit(self, limit):
        """Set a Limit header to our query.

        Args:
            limit: Limit results to this number (integer)

        Examples:
            >>> query = LivestatusQuery('GET hosts')
            >>> query.set_limit(5)
            >>> query.get_query()
            'GET hosts\\nLimit: 5\\n\\n'
        """
        limit = int(limit)
        self.remove_limit()
        self.add_header(self._LIMIT, limit)

    def remove_limit(self):
        """Remove limit header from this query.

        Examples:
            >>> query = LivestatusQuery('GET hosts')
            >>> query.set_limit(5)
            >>> query.get_query()
            'GET hosts\\nLimit: 5\\n\\n'
            >>> query.remove_limit()
            >>> query.get_query()
            'GET hosts\\n\\n'
        """
        self.remove_header(self._LIMIT)


class Livestatus(object):
    """ Class for communicating with Livestatus.

    Example usage::

        s = Livestatus()
        for hostgroup s.get_hostgroups():
            print(hostgroup['name'], hostgroup['num_hosts'])

    For more information on Livestatus see:
        https://mathias-kettner.de/checkmk_livestatus.html
    """

    # Its relatively common that livestatus queries fail because they are made
    # at the same time as nagios is being reloaded. For that reason we introduce
    # one retry on failed queries after waiting for _RETRY_INTERVAL seconds.
    _RETRY_INTERVAL = 0.5

    def __init__(self, livestatus_socket_path=None, nagios_cfg_file=None, authuser=None):
        """ Initilize a new instance of Livestatus

        Args:

          livestatus_socket_path: Path to livestatus socket (if none specified,
          use one specified in nagios.cfg)

          nagios_cfg_file: Path to your nagios.cfg. If None then try to
          auto-detect

          authuser: If specified. Every data pulled is with the access rights
          of that contact.

        """
        self.nagios_cfg_file = nagios_cfg_file
        self.error = None
        if not livestatus_socket_path:
            main_config = pynag.Parsers.main.MainConfig(nagios_cfg_file)

            # Look for a broker_module line in the main config and parse its arguments
            # One of the arguments is path to the file socket created
            for broker_module in main_config.get_list('broker_module'):
                if "livestatus.o" in broker_module:
                    for arg in broker_module.split()[1:]:
                        if arg.startswith('/') or '=' not in arg:
                            livestatus_socket_path = arg
                            break
                    else:
                        # If we get here, then we could not locate a broker_module argument
                        # that looked like a filename
                        msg = "No Livestatus socket defined. Make sure livestatus broker module is loaded."
                        raise ParserError(msg)
        self.livestatus_socket_path = livestatus_socket_path
        self.authuser = authuser

    def test(self, raise_error=True):
        """ Test if connection to livestatus socket is working

        Args:

            raise_error: If set to True, raise exception if test fails,otherwise return False

        Raises:

            ParserError if raise_error == True and connection fails

        Returns:

            True -- Connection is OK
            False -- there are problems and raise_error==False

        """
        try:
            self.query("GET hosts")
        except Exception:
            t, e = sys.exc_info()[:2]
            self.error = e
            if raise_error:
                raise ParserError("got '%s' when testing livestatus socket. error was: '%s'" % (type(e), e))
            else:
                return False
        return True

    def _get_socket(self):
        """ Returns a socket.socket() instance to communicate with livestatus

        Socket might be either unix filesocket or a tcp socket depending in
        the content of :py:attr:`livestatus_socket_path`

        Returns:

            Socket to livestatus instance (socket.socket)

        Raises:

            :py:class:`LivestatusNotConfiguredException` on failed connection.

            :py:class:`ParserError` If could not parse configured TCP address
            correctly.

        """
        if not self.livestatus_socket_path:
            msg = ("We could not find path to MK livestatus socket file."
                   "Make sure MK livestatus is installed and configured")
            raise LivestatusNotConfiguredException(msg)
        try:
            # If livestatus_socket_path contains a colon, then we assume that
            # it is tcp socket instead of a local filesocket
            if self.livestatus_socket_path.find(':') > 0:
                address, tcp_port = self.livestatus_socket_path.split(':', 1)
                if not tcp_port.isdigit():
                    msg = 'Could not parse host:port "%s". This "%s" does not look like a valid tcp port.'
                    raise ParserError(msg % (self.livestatus_socket_path, tcp_port))
                tcp_port = int(tcp_port)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((address, tcp_port))
            else:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.connect(self.livestatus_socket_path)
            return s
        except IOError:
            t, e = sys.exc_info()[:2]
            msg = "%s while connecting to '%s'. Make sure nagios is running and mk_livestatus loaded."
            raise ParserError(msg % (e, self.livestatus_socket_path))

    def write(self, livestatus_query):
        """ Send a raw livestatus query to livestatus socket.

        Queries are corrected and convienient default data are added to the
        query before sending it to the socket.

        Returns:
            A string. The result that comes back from our livestatus socket.

        Raises:
            LivestatusError if there is a problem writing to socket.

        """
        # Lets create a socket and see if we can write to it
        livestatus_socket = self._get_socket()
        try:
            livestatus_socket.send(livestatus_query)
            livestatus_socket.shutdown(socket.SHUT_WR)
            filesocket = livestatus_socket.makefile()
            result = filesocket.read()
            return result
        except IOError:
            msg = "Could not write to socket '%s'. Make sure you have the right permissions"
            raise LivestatusError(msg % self.livestatus_socket_path)
        finally:
            livestatus_socket.close()

    def raw_query(self, query, *args, **kwargs):
        """ Perform LQL queries on the livestatus socket.

        Args:
            query: String. Query to be passed to the livestatus socket
            *args: String. Will be appended to query
            **kwargs: String. Will be appended as 'Filter:' to query.
                For example name='foo' will be appended as 'Filter: name = foo'

        In most cases if you already have constructed a livestatus query, you should only
        need the query argument, args and kwargs can be used to assist in constructing the query.

        For example, the following calls all construct equalant queries:
            l = Livestatus()
            l.query('GET status\nColumns: requests\n')
            l.query('GET status'. 'Columns: requests')
            l.query('GET status', Columns:'requests')

        Returns:
            A string. The results that come out of our livestatus socket.

        Raises:
            LivestatusError: If there are problems with talking to socket.
        """
        livestatus_query = LivestatusQuery(query, *args, **kwargs)
        response = self.write(str(livestatus_query))
        return response

    def _parse_response_header(self, livestatus_response):
        if not livestatus_response:
            raise LivestatusError("Can't parse empty livestatus response")
        rows = livestatus_response.splitlines()
        header = rows.pop(0)
        data = '\n'.join(rows)
        return_code = header.split()[0]
        if not return_code.startswith('2'):
            error_message = header.strip()
            raise LivestatusError("Error '%s' from livestatus: %s" % (return_code, data))
        return data

    def _process_query(self, livestatus_query):
        """ Applies pynag specific quirks and defaults to a Livestatus Query.

        The following will be added to our livestatus_query automatically:
            * If AuthUser is not specified, we add self.authuser.
            * If OutputFormat is not specified, we add python.
            * If ResponseHeader is not specified, we add fixed16.
            * If ColumnHeaders are not specified, we turn them on.
            * If Stats are specified, we turn ColumnHeaders off.

        Args:
            livestatus_query: LivestatusQuery. The query we will process.

        """
        # Implicitly add ResponseHeader if none was specified
        if not livestatus_query.has_responseheader():
            livestatus_query.set_responseheader('fixed16')

        # Implicitly add OutputFormat if none was specified
        if not livestatus_query.has_outputformat():
            livestatus_query.set_outputformat('python')

        # Implicitly turn ColumnHeaders on if none we specified
        if not livestatus_query.has_columnheaders():
            livestatus_query.set_columnheaders('on')

        # Implicitly add AuthUser if one was configured:
        if self.authuser and not livestatus_query.has_authuser():
            livestatus_query.set_authuser(self.authuser)

        # This piece of code is here to workaround a bug in livestatus when
        # livestatus_query contains 'Stats' and ColumnHeaders are on.
        # * Old behavior: Livestatus turns columnheaders explicitly off.
        # * New behavior: Livestatus gives us headers, but corrupted data.
        #
        # Out of 2 evils we maintain consistency by choosing the older
        # behavior of always turning of columnheaders for Stats.
        if livestatus_query.has_stats():
            livestatus_query.set_columnheaders('off')

    def _process_response(self, response_data):
        """Returns livestatus response in a structured format.

        Args:
            response_data: List of strings. Output from livestatus with PythonFormat On
                and without Response headers. Every string in the list represents a single
                line of livestatus output.
        Returns:
            * List of dicts.
            * Every element in the list represents one row from livestatus.
            * Every dict is a {'str':'str'} where the keys are column names and
            the values are column values.
        """
        column_headers = response_data.pop(0)
        # Lets throw everything into a hashmap before we return
        result = []
        for line in response_data:
            current_row = {}
            for i, value in enumerate(line):
                column_name = column_headers[i]
                current_row[column_name] = value
            result.append(current_row)
        return result

    def query(self, query, *args, **kwargs):
        """ Performs LQL queries on the livestatus socket.

        Note:
            The incoming query is mangled and various default headers
            are set on, for more details see _process_query().

            Use raw_query() instead if you need more control over the
            input and output of Livestatus queries.

        Args:
            query: String. Query to be passed to the livestatus socket
            *args: String. Will be appended to query
            **kwargs: Will be appended as 'Filter:' to query.
                For example name='foo' will be appended as 'Filter: name = foo'

        Returns:
            List of dicts. Every item in the list is a row from livestatus and
                every row is a dictionary where the keys are column names and values
                are columns.
            Example return value:
                [{'host_name': 'localhost', 'service_description':'Ping'},]

        Raises:
            LivestatusError: If there is a problem talking to livestatus socket.
        """
        # columns parameter exists for backwards compatibility only.
        # By default ColumnHeaders are 'on'.
        kwargs.pop('columns', None)

        livestatus_query = LivestatusQuery(query, *args, **kwargs)
        self._process_query(livestatus_query)

        # This is we actually send our query into livestatus. livestatus_response is the raw response
        # from livestatus socket (string):
        try:
            livestatus_response = self.write(livestatus_query.get_query())
        except LivestatusError:
            time.sleep(self._RETRY_INTERVAL)
            livestatus_response = self.raw_query(livestatus_query)


        if not livestatus_response:
            raise InvalidResponseFromLivestatus(query=livestatus_query, response=livestatus_response)

        # Parse the response header from livestatus, will raise an exception if
        # livestatus returned an error:
        response_data = self._parse_response_header(livestatus_response)

        if livestatus_query.output_format() != 'python':
            return response_data

        # Return empty list if we got no results
        if not response_data:
            return []

        try:
            response_data = eval(response_data)
        except Exception:
            raise InvalidResponseFromLivestatus(query=livestatus_query, response=response_data)

        # Usually when we query livestatus we get back a 'list of rows',
        # however Livestatus had a quirk in the past that if there were Stats
        # in the query Instead of returning rows, it would just return a list
        # of stats. For backwards Compatibility we cling on to the old bug, of
        # not returning 'rows' when asking for stats.
        if livestatus_query.has_stats() and len(response_data) == 1:
            return response_data[0]

        # Backwards compatibility. if ColumnHeaders=Off, we return livestatus
        # original format of lists of lists (instead of lists of dicts)
        if not livestatus_query.column_headers():
            return response_data

        return self._process_response(response_data)

    def get(self, table, *args, **kwargs):
        """ Same as self.query('GET %s' % (table,))

        Extra arguments will be appended to the query.

        Args:

            table: Table from which the data will be retrieved

            args, kwargs: These will be appendend to the end of the query to
            perform additional instructions.

        Example::

            get('contacts', 'Columns: name alias')

        Returns:

            Answer from livestatus in python format.

        """
        return self.query('GET %s' % (table,), *args, **kwargs)

    def get_host(self, host_name):
        """ Performs a GET query for a particular host

        This performs::

            '''GET hosts
            Filter: host_name = %s''' % host_name

        Args:

            host_name: name of the host to obtain livestatus data from

        Returns:

            Answer from livestatus in python format.

        """
        return self.query('GET hosts', 'Filter: host_name = %s' % host_name)[0]

    def get_service(self, host_name, service_description):
        """ Performs a GET query for a particular service

        This performs::

            '''GET services
            Filter: host_name = %s
            Filter: service_description = %s''' % (host_name, service_description)

        Args:

            host_name: name of the host the target service is attached to.

            service_description: Description of the service to obtain livestatus
            data from.

        Returns:

            Answer from livestatus in python format.

        """
        return self.query('GET services', 'Filter: host_name = %s' % host_name,
                          'Filter: description = %s' % service_description)[0]

    def get_hosts(self, *args, **kwargs):
        """ Performs a GET query for all hosts

        This performs::

            '''GET hosts %s %s''' % (*args, **kwargs)

        Args:

            args, kwargs: These will be appendend to the end of the query to
            perform additional instructions.

        Returns:

            Answer from livestatus in python format.

        """
        return self.query('GET hosts', *args, **kwargs)

    def get_services(self, *args, **kwargs):
        """ Performs a GET query for all services

        This performs::

            '''GET services
            %s %s''' % (*args, **kwargs)

        Args:

            args, kwargs: These will be appendend to the end of the query to
            perform additional instructions.

        Returns:

            Answer from livestatus in python format.

        """
        return self.query('GET services', *args, **kwargs)

    def get_hostgroups(self, *args, **kwargs):
        """ Performs a GET query for all hostgroups

        This performs::

            '''GET hostgroups
            %s %s''' % (*args, **kwargs)

        Args:

            args, kwargs: These will be appendend to the end of the query to
            perform additional instructions.

        Returns:

            Answer from livestatus in python format.

        """
        return self.query('GET hostgroups', *args, **kwargs)

    def get_servicegroups(self, *args, **kwargs):
        """ Performs a GET query for all servicegroups

        This performs::

            '''GET servicegroups
            %s %s''' % (*args, **kwargs)

        Args:

            args, kwargs: These will be appendend to the end of the query to
            perform additional instructions.

        Returns:

            Answer from livestatus in python format.

        """
        return self.query('GET servicegroups', *args, **kwargs)

    def get_contactgroups(self, *args, **kwargs):
        """ Performs a GET query for all contactgroups

        This performs::

            '''GET contactgroups
            %s %s''' % (*args, **kwargs)

        Args:

            args, kwargs: These will be appendend to the end of the query to
            perform additional instructions.

        Returns:

            Answer from livestatus in python format.

        """
        return self.query('GET contactgroups', *args, **kwargs)

    def get_contacts(self, *args, **kwargs):
        """ Performs a GET query for all contacts

        This performs::

            '''GET contacts
            %s %s''' % (*args, **kwargs)

        Args:

            args, kwargs: These will be appendend to the end of the query to
            perform additional instructions.

        Returns:

            Answer from livestatus in python format.

        """
        return self.query('GET contacts', *args, **kwargs)

    def get_contact(self, contact_name):
        """ Performs a GET query for a particular contact

        This performs::

            '''GET contacts
            Filter: contact_name = %s''' % contact_name

        Args:

            contact_name: name of the contact to obtain livestatus data from

        Returns:

            Answer from livestatus in python format.

        """
        return self.query('GET contacts', 'Filter: contact_name = %s' % contact_name)[0]

    def get_servicegroup(self, name):
        """ Performs a GET query for a particular servicegroup

        This performs::

            '''GET servicegroups
            Filter: servicegroup_name = %s''' % servicegroup_name

        Args:

            servicegroup_name: name of the servicegroup to obtain livestatus data from

        Returns:

            Answer from livestatus in python format.

        """
        return self.query('GET servicegroups', 'Filter: name = %s' % name)[0]

    def get_hostgroup(self, name):
        """ Performs a GET query for a particular hostgroup

        This performs::

            '''GET hostgroups
            Filter: hostgroup_name = %s''' % hostgroup_name

        Args:

            hostgroup_name: name of the hostgroup to obtain livestatus data from

        Returns:

            Answer from livestatus in python format.

        """
        return self.query('GET hostgroups', 'Filter: name = %s' % name)[0]

    def get_contactgroup(self, name):
        """ Performs a GET query for a particular contactgroup

        This performs::

            '''GET contactgroups
            Filter: contactgroup_name = %s''' % contactgroup_name

        Args:

            contactgroup_name: name of the contactgroup to obtain livestatus data from

        Returns:

            Answer from livestatus in python format.

        """
        return self.query('GET contactgroups', 'Filter: name = %s' % name)[0]


