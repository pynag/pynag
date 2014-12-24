import pynag.Parsers.config_parser

# Path To Nagios configuration file
cfg_file = None  # '/etc/nagios/nagios.cfg'

# Were new objects are written by default
pynag_directory = None

# This is the config parser that we use internally, if cfg_file is changed, then config
# will be recreated whenever a parse is called.
config = pynag.Parsers.config_parser.Config(cfg_file=cfg_file)

#: eventhandlers -- A list of Model.EventHandlers object.
# Event handler is responsible for passing notification whenever something
# important happens in the model.
#
# For example FileLogger class is an event handler responsible for logging to
# file whenever something has been written.
eventhandlers = []

# Default value returned when a macro cannot be found
_UNRESOLVED_MACRO = ''

# We know that a macro is a custom variable macro if the name
# of the macro starts with this prefix:
_CUSTOM_VARIABLE_PREFIX = '_'

