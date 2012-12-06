# check_dns.py -- Returns OK if a hostname resolves to any ip address
from _socket import gaierror
import socket
import time
from pynag.Plugins import PluginHelper,ok,warning,critical,unknown

my_plugin = PluginHelper()
my_plugin.parser.add_option('-H', help="Hostname or ip address", dest="hostname")
my_plugin.parser.add_option('-a', help="Expected Address", dest="address")
my_plugin.parse_arguments()


hostname = my_plugin.options.hostname
address = my_plugin.options.address
if hostname is None:
    my_plugin.parser.error('-H argument is required')

# Here comes the specific check logic
try:
    start_time = time.time()
    result = socket.gethostbyname( hostname )
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
    my_plugin.status(critical)
    my_plugin.add_summary('Could not resolve host "%s"' % hostname )

# Run check_all_metrics so end-user has the option of thresholding on run_time
my_plugin.check_all_metrics()

# Print status output and exit
my_plugin.exit()
