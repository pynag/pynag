from nagios_objects import *

class StringToClass(object):

    def __init__(self, backend='nagios'):
        
        self.backend = backend

        # Default Nagios objects
        # No prefix for backwards compatibility
        self.string_to_class = {}
        self.string_to_class['contact'] = Contact
        self.string_to_class['service'] = Service
        self.string_to_class['host'] = Host
        self.string_to_class['hostgroup'] = Hostgroup
        self.string_to_class['contactgroup'] = Contactgroup
        self.string_to_class['servicegroup'] = Servicegroup
        self.string_to_class['timeperiod'] = Timeperiod
        self.string_to_class['hostdependency'] = HostDependency
        self.string_to_class['servicedependency'] = ServiceDependency
        self.string_to_class['hostescalation'] = HostEscalation
        self.string_to_class['serviceescalation'] = ServiceEscalation
        self.string_to_class['command'] = Command

    def __getitem__(self,item):
        self.get(item)

    def get(self, classname, default=ObjectDefinition):
        try:
            if self.backend == 'nagios':
                a = self.getNagiosClass(classname, default)
            elif self.backend == 'shinken':
                a = self.getShinkenClass(classname, default)
        except:
            return default
        return a

    def getNagiosClass(self, classname, default):
        return self.string_to_class.get(classname, default)

    def getShinkenClass(self, classname, default):
        return self.shinken_string_to_class.get(classname, default)

