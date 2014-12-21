import os
import re
import time

import pynag.Parsers.main

# TODO: Revisit this import, use Utils.state instead
import pynag.Plugins


class LogFiles(object):

    """ Parses Logfiles defined in nagios.cfg and allows easy access to its content

    Content is stored in python-friendly arrays of dicts. Output should be more
    or less compatible with mk_livestatus log output
    """

    def __init__(self, maincfg=None):
        main_config = pynag.Parsers.main.MainConfig(maincfg)
        self.log_file = main_config.get('log_file')
        self.log_archive_path = main_config.get('log_archive_path')

    def get_log_entries(self, start_time=None, end_time=None, strict=True, search=None, **kwargs):
        """ Get Parsed log entries for given timeperiod.

         Args:
            start_time: unix timestamp. if None, return all entries from today

            end_time: If specified, only fetch log entries older than this (unix
            timestamp)

            strict: If True, only return entries between start_time and
            end_time, if False, then return entries that belong to same log
            files as given timeset

            search: If provided, only return log entries that contain this
            string (case insensitive)

            kwargs: All extra arguments are provided as filter on the log
            entries. f.e. host_name="localhost"

         Returns:

            List of dicts
        """
        now = time.time()
        if end_time is None:
            end_time = now
        if start_time is None:
            if 'filename' in kwargs:
                start_time = 1
            else:
                seconds_in_a_day = 60 * 60 * 24
                seconds_today = end_time % seconds_in_a_day  # midnight of today
                start_time = end_time - seconds_today
        start_time = int(start_time)
        end_time = int(end_time)

        logfiles = self.get_logfiles()
        if 'filename' in kwargs:
            logfiles = filter(lambda x: x == kwargs.get('filename'), logfiles)

        # If start time was provided, skip all files that we last modified
        # before start_time
        if start_time:
            logfiles = filter(lambda x: start_time <= os.stat(x).st_mtime, logfiles)

        # Log entries are returned in ascending order, which is the opposite of
        # what get_logfiles returns.
        logfiles.reverse()

        result = []
        for log_file in logfiles:
            entries = self._parse_log_file(filename=log_file)
            if len(entries) == 0:
                continue
            first_entry = entries[0]
            last_entry = entries[-1]

            if first_entry['time'] > end_time:
                continue
                # If strict, filter entries to only include the ones in the timespan
            if strict is True:
                entries = [x for x in entries if x['time'] >= start_time and x['time'] <= end_time]
                # If search string provided, filter the string
            if search is not None:
                entries = [x for x in entries if x['message'].lower().find(search.lower()) > -1]
            for k, v in kwargs.items():
                entries = [x for x in entries if x.get(k) == v]
            result += entries

            if start_time is None or int(start_time) >= int(first_entry.get('time')):
                continue

        # Now, logfiles should in MOST cases come sorted for us.
        # However we rely on modification time of files and if it is off,
        # We want to make sure log entries are coming in the correct order.
        # The following sort should not impact performance in the typical use case.
        result.sort(key=lambda x: x.get('time'))

        return result

    def get_logfiles(self):
        """ Returns a list with the fullpath to every log file used by nagios.

        Lists are sorted by modification times. Newest logfile is at the front
        of the list so usually nagios.log comes first, followed by archivelogs

        Returns:

            List of strings

        """
        logfiles = []

        for filename in os.listdir(self.log_archive_path):
            full_path = "%s/%s" % (self.log_archive_path, filename)
            if not os.path.isfile(full_path):
                continue
            logfiles.append(full_path)
        logfiles.append(self.log_file)

        # Sort the logfiles by modification time, newest file at the front
        compare_mtime = lambda a, b: os.stat(a).st_mtime < os.stat(b).st_mtime
        logfiles.sort(key=lambda x: int(os.stat(x).st_mtime))

        # Newest logfiles go to the front of the list
        logfiles.reverse()

        return logfiles

    def get_flap_alerts(self, **kwargs):
        """ Same as :py:meth:`get_log_entries`, except return timeperiod transitions.

        Takes same parameters.
        """
        return self.get_log_entries(class_name="timeperiod transition", **kwargs)

    def get_notifications(self, **kwargs):
        """ Same as :py:meth:`get_log_entries`, except return only notifications.
        Takes same parameters.
        """
        return self.get_log_entries(class_name="notification", **kwargs)

    def get_state_history(self, start_time=None, end_time=None, host_name=None, strict=True, service_description=None):
        """ Returns a list of dicts, with the state history of hosts and services.

        Args:

           start_time: unix timestamp. if None, return all entries from today

           end_time: If specified, only fetch log entries older than this (unix
           timestamp)

           host_name: If provided, only return log entries that contain this
           string (case insensitive)

           service_description: If provided, only return log entries that contain this
           string (case insensitive)

        Returns:

            List of dicts with state history of hosts and services
        """

        log_entries = self.get_log_entries(start_time=start_time, end_time=end_time, strict=strict, class_name='alerts')
        result = []
        last_state = {}
        now = time.time()

        for line in log_entries:
            if 'state' not in line:
                continue
            line['duration'] = now - int(line.get('time'))
            if host_name is not None and host_name != line.get('host_name'):
                continue
            if service_description is not None and service_description != line.get('service_description'):
                continue
            if start_time is None:
                start_time = int(line.get('time'))

            short_name = "%s/%s" % (line['host_name'], line['service_description'])
            if short_name in last_state:
                last = last_state[short_name]
                last['end_time'] = line['time']
                last['duration'] = last['end_time'] - last['time']
                line['previous_state'] = last['state']
            last_state[short_name] = line

            if strict is True:
                if start_time is not None and int(start_time) > int(line.get('time')):
                    continue
                if end_time is not None and int(end_time) < int(line.get('time')):
                    continue

            result.append(line)
        return result

    def _parse_log_file(self, filename=None):
        """ Parses one particular nagios logfile into arrays of dicts.

        Args:

            filename: Log file to be parsed. If is None, then log_file from
            nagios.cfg is used.

        Returns:

            A list of dicts containing all data from the log file
        """
        if filename is None:
            filename = self.log_file
        result = []
        for line in open(filename).readlines():
            parsed_entry = self._parse_log_line(line)
            if parsed_entry != {}:
                parsed_entry['filename'] = filename
                result.append(parsed_entry)
        return result

    def _parse_log_line(self, line):
        """ Parse one particular line in nagios logfile and return a dict.

        Args:

            line: Line of the log file to be parsed.

        Returns:

            dict containing the information from the log file line.
        """
        host = None
        service_description = None
        state = None
        check_attempt = None
        plugin_output = None
        contact = None

        m = re.search('^\[(.*?)\] (.*?): (.*)', line)
        if m is None:
            return {}
        line = line.strip()
        timestamp, logtype, options = m.groups()

        result = {}
        try:
            timestamp = int(timestamp)
        except ValueError:
            timestamp = 0
        result['time'] = int(timestamp)
        result['type'] = logtype
        result['options'] = options
        result['message'] = line
        result['class'] = 0  # unknown
        result['class_name'] = 'unclassified'
        if logtype in ('CURRENT HOST STATE', 'CURRENT SERVICE STATE', 'SERVICE ALERT', 'HOST ALERT'):
            result['class'] = 1
            result['class_name'] = 'alerts'
            if logtype.find('HOST') > -1:
                # This matches host current state:
                m = re.search('(.*?);(.*?);(.*);(.*?);(.*)', options)
                if m is None:
                    return result
                host, state, hard, check_attempt, plugin_output = m.groups()
                service_description = None
            if logtype.find('SERVICE') > -1:
                m = re.search('(.*?);(.*?);(.*?);(.*?);(.*?);(.*)', options)
                if m is None:
                    return result
                host, service_description, state, hard, check_attempt, plugin_output = m.groups()
            result['host_name'] = host
            result['service_description'] = service_description
            result['state'] = int(pynag.Plugins.state[state])
            result['check_attempt'] = check_attempt
            result['plugin_output'] = plugin_output
            result['text'] = plugin_output
        elif "NOTIFICATION" in logtype:
            result['class'] = 3
            result['class_name'] = 'notification'
            if logtype == 'SERVICE NOTIFICATION':
                m = re.search('(.*?);(.*?);(.*?);(.*?);(.*?);(.*)', options)
                if m is None:
                    return result
                contact, host, service_description, state, command, plugin_output = m.groups()
            elif logtype == 'HOST NOTIFICATION':
                m = re.search('(.*?);(.*?);(.*?);(.*?);(.*)', options)
                if m is None:
                    return result
                contact, host, state, command, plugin_output = m.groups()
                service_description = None
            result['contact_name'] = contact
            result['host_name'] = host
            result['service_description'] = service_description
            try:
                result['state'] = int(pynag.Plugins.state[state])
            except Exception:
                result['state'] = -1
            result['plugin_output'] = plugin_output
            result['text'] = plugin_output
        elif logtype == "EXTERNAL COMMAND":
            result['class'] = 5
            result['class_name'] = 'command'
            m = re.search('(.*?);(.*)', options)
            if m is None:
                return result
            command_name, text = m.groups()
            result['command_name'] = command_name
            result['text'] = text
        elif logtype in ('PASSIVE SERVICE CHECK', 'PASSIVE HOST CHECK'):
            result['class'] = 4
            result['class_name'] = 'passive'
            if logtype.find('HOST') > -1:
                # This matches host current state:
                m = re.search('(.*?);(.*?);(.*)', options)
                if m is None:
                    return result
                host, state, plugin_output = m.groups()
                service_description = None
            if logtype.find('SERVICE') > -1:
                m = re.search('(.*?);(.*?);(.*?);(.*)', options)
                if m is None:
                    return result
                host, service_description, state, plugin_output = m.groups()
            result['host_name'] = host
            result['service_description'] = service_description
            result['state'] = state
            result['plugin_output'] = plugin_output
            result['text'] = plugin_output
        elif logtype in ('SERVICE FLAPPING ALERT', 'HOST FLAPPING ALERT'):
            result['class_name'] = 'flapping'
        elif logtype == 'TIMEPERIOD TRANSITION':
            result['class_name'] = 'timeperiod_transition'
        elif logtype == 'Warning':
            result['class_name'] = 'warning'
            result['state'] = "1"
            result['text'] = options
        if 'text' not in result:
            result['text'] = result['options']
        result['log_class'] = result['class']  # since class is a python keyword
        return result


