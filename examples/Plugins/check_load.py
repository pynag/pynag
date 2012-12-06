# check_load.py - Check load average. Thresholds can be specified from the commandline

from pynag.Plugins import PluginHelper,ok,warning,critical,unknown


helper = PluginHelper()
helper.parse_arguments()

try:
    content = open('/proc/loadavg').read()
except Exception, e:
    helper.exit(summary="Could not read /proc/loadavg", long_output=str(e), exit_code=unknown, perfdata='')


helper.add_summary("Load: %s" % content)

# Read metrics from /proc/loadavg and add them as performance metrics
load1,load5,load15,processes,last_proc_id = content.split()
running,total = processes.split('/')

# If we so desire we can set default thresholds by adding warn attribute here
# However we decide that there are no thresholds by default and they have to be
# applied on runtime with the --threshold option
helper.add_metric(label='load1',value=load1)
helper.add_metric(label='load5',value=load5)
helper.add_metric(label='load15',value=load15)
helper.add_metric(label='running_processes',value=running)
helper.add_metric(label='total_processes',value=total)

# By default assume everything is ok:
helper.status(ok)

# Here all metrics will be checked against thresholds that are either
# built-in or added via --threshold from the command-line
helper.check_all_metrics()

# Print out plugin information and exit nagios-style
helper.exit()
