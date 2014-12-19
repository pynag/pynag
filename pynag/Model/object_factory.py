import nagios_objects

class ObjectFactory(object):

    def __init__(self, backend='nagios'):
        
        self.backend = backend

        if self.backend == 'nagios':
            self.Contact = nagios_objects.Contact
            self.Service = nagios_objects.Service
            self.Host = nagios_objects.Host
            self.Hostgroup = nagios_objects.Hostgroup
            self.Contactgroup = nagios_objects.Contactgroup
            self.Servicegroup = nagios_objects.Servicegroup
            self.Timeperiod = nagios_objects.Timeperiod
            self.HostDependency = nagios_objects.HostDependency
            self.ServiceDependency = nagios_objects.ServiceDependency
            self.HostEscalation = nagios_objects.HostEscalation
            self.ServiceEscalation = nagios_objects.ServiceEscalation
            self.Command = nagios_objects.Command
            self.ObjectDefinition = nagios_objects.ObjectDefinition
            self.ObjectRelations = nagios_objects.ObjectRelations

    def prepare_object_module(self, config, eventhandlers, pynag_directory):
        if self.backend == 'nagios':
            nagios_objects.prepare_module_attributes(config, eventhandlers,
                    pynag_directory)

