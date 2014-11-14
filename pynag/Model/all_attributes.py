from nagios_attributes import object_definitions as nagios_definitions

class AllAttributes(object):

    def __init__(self, backend='nagios'):
        if backend == 'nagios':
            self.object_definitions = nagios_definitions

