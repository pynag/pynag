# check_dns.py -- Returns OK if a hostname resolves to any ip address

# check_dns plugin will need some system libraries for DNS lookup
from __future__ import absolute_import
from _socket import gaierror
import socket
import time

# Import PluginHelper and some utility constants from the Plugins module
from pynag.Plugins import PluginHelper,ok,warning,critical,unknown

# Create an instance of PluginHelper()
my_plugin = PluginHelper()

# Our Plugin will need -H and -a attributes and we will use PluginHelpers wrapper around optparse for this:
my_plugin.parser.add_option('-H', help="Hostname or ip address", dest="hostname")
my_plugin.parser.add_option('-a', help="Expected Address", dest="address")

# When parse_arguments is called some default options like --threshold and --no-longoutput are automatically added
my_plugin.parse_arguments()


#
# Here starts Plugin-specific logic
#

# Get the hostname and expected address that was provided on the command-line
# address will be optional, but we will throw and error if hostname is not provided
hostname = my_plugin.options.hostname
address = my_plugin.options.address
if hostname is None:
    my_plugin.parser.error('-H argument is required')


# Here comes the specific check logic
try:
    start_time = time.time()
    result = socket.gethostbyname( hostname ) # result will contain the ip address resolved
    end_time = time.time()

    # If no address was specified with -a, then we return
    # OK if hostname resolved to anything at all
    if address is None or address == result:
        my_plugin.status(ok)
        my_plugin.add_summary("%s resolves to %s" % (hostname, result))
    else:
        my_plugin.status(critical)
        my_plugin.add_summary("%s resolves to %s but should resolve to %s" % (hostname,result,address))

    # Add run_time metric, so we can also alert if lookup takes to long
    run_time = end_time - start_time
    my_plugin.add_metric('run_time', run_time)
except gaierror:
    # If any exceptions happened in the code above, lets return a critical status
    my_plugin.status(critical)
    my_plugin.add_summary('Could not resolve host "%s"' % hostname )

# when check_all_metrics() is run, any metrics we have added with add_metric() will be processed against
# Thresholds (like --threshold). This part will allow our plugin users to alert on lookup_time
my_plugin.check_all_metrics()

# Print status output and exit
my_plugin.exit()
