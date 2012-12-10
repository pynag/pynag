# check_stuff.py Takes any arguments from the command_line and treats them as performance metrics.


from pynag.Plugins import PluginHelper

my_plugin = PluginHelper()
my_plugin.parse_arguments()

# Any perfdatastring added as argument will be treated as a performance metric
for i in my_plugin.arguments:
    my_plugin.add_metric(perfdatastring=i)


my_plugin.check_all_metrics()
my_plugin.exit()
