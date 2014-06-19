import os
import sys

# Make sure we import from working tree
pynagbase = os.path.dirname(os.path.realpath(__file__ + "/.."))
sys.path.insert(0, pynagbase)

try:
    import unittest
except ImportError:
    unittest

import tempfile
import os
import shutil
import string
import random
import mock
import time
import sys

import pynag.Model
import pynag.Model.EventHandlers
import pynag.Utils.misc
from tests import tests_dir

os.chdir(tests_dir)


class Model(unittest.TestCase):
    """
    Basic Unit Tests that relate to saving objects
    """
    def setUp(self):
        """ Basic setup before test suite starts
        """
        self.tmp_dir = tempfile.mkdtemp()  # Will be deleted after test runs

        os.chdir(tests_dir)
        os.chdir('dataset01')
        pynag.Model.cfg_file = "./nagios/nagios.cfg"
        pynag.Model.config = None
        pynag.Model.pynag_directory = self.tmp_dir
        pynag.Model.ObjectDefinition.objects.get_all()
        pynag.Model.config._edit_static_file(attribute='cfg_dir', new_value=self.tmp_dir)

    def tearDown(self):
        """ Clean up after test suite has finished
        """
        shutil.rmtree(self.tmp_dir, ignore_errors=True)
        pynag.Model.ObjectDefinition.objects.get_all()
        pynag.Model.config._edit_static_file(attribute='cfg_dir',old_value=self.tmp_dir,new_value=None)

    def testSuggestedFileName(self):
        """ Test get_suggested_filename feature in pynag.Model
        """
        s1 = pynag.Model.Service()
        s1.service_description = 'Service without host_name'

        s2 = pynag.Model.Service()
        s2.service_description = 'Service with host_name'
        s2.host_name = 'host.example.com'

        s3 = pynag.Model.Service()
        s3.service_description = 'Service with Generic Name'
        s3.name = 'generic-test-service'

        s1_expected = '%s/services/Servicewithouthost_name.cfg' % pynag.Model.pynag_directory
        s2_expected = '%s/services/Servicewithhost_name.cfg' % pynag.Model.pynag_directory
        s3_expected = '%s/services/generic-test-service.cfg' % pynag.Model.pynag_directory

        self.assertEqual(s1_expected, s1.get_suggested_filename())
        self.assertEqual(s2_expected, s2.get_suggested_filename())
        self.assertEqual(s3_expected, s3.get_suggested_filename())

    def testChangeAttribute(self):
        """ Change a single attribute in a pynag Model object
        """

        s = pynag.Model.Service()
        service_description = "Test Service Description"
        host_name = "testhost.example.com"
        macro = "This is a test macro"
        check_command = "my_check_command"

        # Assign the regular way
        s.service_description = service_description

        # Assign with set_attribute
        s.set_attribute('check_command', check_command)

        # Assign hashmap style
        s['host_name'] = host_name

        # Assign a macro
        s['__TEST_MACRO'] = macro

        self.assertEqual(service_description, s['service_description'])
        self.assertEqual(host_name, s.host_name)
        self.assertEqual(macro, s['__TEST_MACRO'])
        self.assertEqual(check_command, s.get_attribute('check_command'))

    def testServicegroupMembership(self):
        """ Loads servicegroup definitions from testdata01 and checks if get_effective_services works as expected
        """

        # service1 and service2 should both belong to group but they are defined differently
        group = pynag.Model.Servicegroup.objects.get_by_shortname('group-2')
        service1 = pynag.Model.Service.objects.get_by_shortname('node-1/cpu')
        service2 = pynag.Model.Service.objects.get_by_shortname('node-1/cpu2')
        self.assertEqual([group], service1.get_effective_servicegroups())
        self.assertEqual([group], service2.get_effective_servicegroups())
        self.assertEqual(sorted([service1, service2]), sorted(group.get_effective_services()))

    def testHostDelete(self):
        """ Create a test object and then delete it. """
        host = pynag.Model.Host()

        all_hosts = pynag.Model.Host.objects.get_all()
        all_hostnames = map(lambda x: x.host_name, all_hosts)

        # generate a random hostname for our new host
        chars = string.letters + string.digits
        host_name = "host-delete-test"  + ''.join([random.choice(chars) for i in xrange(10)])

        # Produce an error if our randomly generated host already exists in config
        self.assertTrue(host_name not in all_hostnames)

        # Save our new host and reload our config if we somehow failed to create the
        # host we will get an exception here.
        host.host_name = host_name
        host.save()
        host = pynag.Model.Host.objects.get_by_shortname(host_name)

        # Host has been created. Lets delete it.
        host.delete()

        # Lets get all hosts again, and make sure the list is the same as when we started
        # If it is the same, the host was surely deleted
        all_hosts_after_delete = pynag.Model.Host.objects.get_all()
        self.assertEqual(all_hosts,all_hosts_after_delete)

    def testSaveNewObject(self):
        """ Test creating a new object with the model """
        hostname1 = "new_host1"
        hostname2 = "new_host2"

        # First of all, make sure the new hosts do not exist in the config before we save.
        hostlist1 = pynag.Model.Host.objects.filter(host_name=hostname1)
        hostlist2 = pynag.Model.Host.objects.filter(host_name=hostname2)

        self.assertEqual([], hostlist1)
        self.assertEqual([], hostlist2)

        # Save a new object, let pynag decide where it is saved.
        host = pynag.Model.Host(host_name=hostname1)
        host.save()
        hostlist1 = pynag.Model.Host.objects.filter(host_name=hostname1)
        self.assertEqual(1, len(hostlist1))

        # Save a new object, this time lets specify a filename for it
        host = pynag.Model.Host(host_name=hostname2)
        dest_file = "%s/newhost2.cfg" % pynag.Model.pynag_directory
        host.set_filename(dest_file)
        host.save()
        hostlist2 = pynag.Model.Host.objects.filter(host_name=hostname2)
        self.assertEqual(1, len(hostlist2))
        host = hostlist2[0]
        self.assertEqual(dest_file, host.get_filename())

    def testSaveExistingObjects(self):
        """ Test saving existing objects to both same file and a new file
        """
        # Save our host
        host_name = "testhost"
        use = 'generic-host'
        host = pynag.Model.Host(host_name=host_name, use=use)
        host.save()
        origin_filename = host.get_filename()

        # Parse again and see if we find the same host:
        host = pynag.Model.Host.objects.get_by_shortname(host_name)
        self.assertEqual(host_name, host.host_name)
        self.assertEqual(use, host.use)
        self.assertEqual(origin_filename, host.get_filename())
        self.assertFalse(host.is_dirty())

        # Change host a little bit, and save to a new file:
        new_host_name = host_name + "2"
        new_filename = origin_filename + "-saveagain.cfg"
        host.host_name = new_host_name
        self.assertTrue(host.is_dirty())
        host.set_filename(new_filename)
        host.save()

        # Parse again and see if we find the same host:
        host = pynag.Model.Host.objects.get_by_shortname(new_host_name)
        self.assertEqual(new_host_name, host.host_name)
        self.assertEqual(use, host.use)
        self.assertEqual(new_filename, host.get_filename())

        # Save it for the third time, this time using parameter to save()
        new_new_host_name = host.host_name + "-2"
        new_new_filename = host.get_filename() + "-new.cfg"
        host.host_name = new_new_host_name
        host.save(filename=new_new_filename)

        new_host = pynag.Model.Host.objects.get_by_shortname(new_new_host_name)
        self.assertEqual(new_new_filename, new_host.get_filename())
        self.assertEqual(new_new_host_name, new_host.host_name)

    def testMoveObject(self):
        """ Test ObjectDefinition.move() """

        file1 = pynag.Model.pynag_directory + "/file1.cfg"
        file2 = pynag.Model.pynag_directory + "/file2.cfg"
        host_name="movable_host"
        new_object = pynag.Model.Host(host_name=host_name)
        new_object.set_filename(file1)
        new_object.save()

        # Reload config, and see if new object is saved where we wanted it to be
        search_results = pynag.Model.Host.objects.filter(host_name=host_name)
        self.assertEqual(1, len(search_results))

        host = search_results[0]
        self.assertEqual(file1, host.get_filename())

        # Move the host to a new file and make sure it is moved.
        host.move(file2)

        search_results = pynag.Model.Host.objects.filter(host_name=host_name)
        self.assertEqual(1, len(search_results))

        host = search_results[0]
        self.assertEqual(file2, host.get_filename())

    def testMacroResolving(self):
        """ Test the get_macro and get_all_macros commands of services """

        service1 = pynag.Model.Service.objects.get_by_name('macroservice')
        macros = service1.get_all_macros()
        expected_macrokeys = ['$USER1$', '$ARG2$', '$_SERVICE_empty$', '$_HOST_nonexistant$', '$_SERVICE_nonexistant$', '$_SERVICE_macro1$', '$ARG1$', '$_HOST_macro1$', '$_HOST_empty$', '$HOSTADDRESS$', '$_SERVICE_not_used$']
        self.assertEqual(sorted(expected_macrokeys),  sorted(macros.keys()))

        self.assertEqual('/path/to/user1', macros['$USER1$'])
        self.assertEqual('/path/to/user1', macros['$ARG2$'])
        self.assertEqual('hostaddress', macros['$HOSTADDRESS$'])

        self.assertEqual('macro1', macros['$_SERVICE_macro1$'])
        self.assertEqual('macro1', macros['$ARG1$'])
        self.assertEqual('macro1', macros['$_HOST_macro1$'])
        self.assertEqual('this.macro.is.not.used', macros['$_SERVICE_not_used$'])

        self.assertEqual(None, macros['$_HOST_nonexistant$'])
        self.assertEqual(None, macros['$_SERVICE_nonexistant$'])

        self.assertEqual('', macros['$_SERVICE_empty$'])
        self.assertEqual('', macros['$_HOST_empty$'])

        expected_command_line = "/path/to/user1/macro -H 'hostaddress' host_empty='' service_empty='' host_macro1='macro1' arg1='macro1' host_nonexistant='' service_nonexistant='' escaped_dollarsign=$$ user1_as_argument=/path/to/user1"
        actual_command_line = service1.get_effective_command_line()

        self.assertEqual(expected_command_line, actual_command_line)

    def testParenting(self):
        """ Test the use of get_effective_parents and get_effective_children
        """

        # Get host named child, check its parents
        h = pynag.Model.Host.objects.get_by_name('child')
        expected_result = ['parent01', 'parent02', 'parent-of-all']
        hosts = h.get_effective_parents(recursive=True)
        host_names = map(lambda x: x.name, hosts)
        self.assertEqual(expected_result, host_names)

        # Get host named parent-of-all, get its children
        h = pynag.Model.Host.objects.get_by_name('parent-of-all')
        expected_result = ['parent01', 'parent02', 'parent03', 'child']
        hosts = h.get_effective_children(recursive=True)
        host_names = map(lambda x: x.name, hosts)
        self.assertEqual(expected_result, host_names)

    def test_hostgroup_with_regex_members(self):
        """ Test parsing a hostgroup with regex members. """
        prod_servers = pynag.Model.Hostgroup.objects.get_by_shortname('prod-servers')
        # prod_server.members = "prod-[a-zA-Z0-9]+"

        prod_api1 = pynag.Model.Host.objects.get_by_shortname('prod-api-1')
        prod_api2 = pynag.Model.Host.objects.get_by_shortname('prod-api-2')
        dev_api2 = pynag.Model.Host.objects.get_by_shortname('dev-api-1')

        service = pynag.Model.Service.objects.get_by_name('short-term-load')
        hosts = service.get_effective_hosts()

        self.assertTrue(prod_api1 in hosts)  # prod-api-1 matches the regex
        self.assertTrue(prod_api2 in hosts)  # prod-api-2 matches the regex
        self.assertFalse(dev_api2 in hosts)  # dev-api-1 does not match

        # Hostgroup.get_effective_hosts() should match the same regex:
        self.assertEqual(hosts, prod_servers.get_effective_hosts())

    def test_rewrite(self):
        """ Test usage on ObjectDefinition.rewrite() """
        h = pynag.Model.Host()
        expect_new_host = 'define host {\n}\n'
        self.assertEqual(str(h), expect_new_host)

        raw_definition2 = 'define host {\nhost_name brand_new_host\n}\n'
        h.rewrite(raw_definition2)
        h2 = pynag.Model.Host.objects.get_by_shortname('brand_new_host')
        self.assertEqual(h2, h)

        raw_definition3 = 'define host {\nhost_name brand_new_host3\n}\n'
        h2.rewrite(raw_definition3)
        h3 = pynag.Model.Host.objects.get_by_shortname('brand_new_host3')
        self.assertEqual(h3, h2)

    def test_get_related_objects(self):
        """ Test objectdefinition.get_related_objects()
        """
        host1 = pynag.Model.Host(name='a-host-template', use='generic-host')
        host1.save()

        host2 = pynag.Model.Host(host_name='server', use='a-host-template')
        host2.save()

        self.assertEqual(host1.get_related_objects(), [host2])

    def test_attribute_is_empty(self):
        """Test if pynag properly determines if an attribute is empty"""

        #creating test object
        host =  pynag.Model.Host()
        host['host_name']   = "+"
        host['address']     = "not empty"
        host['contacts']    = "!"
        host['hostgroups']  = "                                             "
        host['contact_groups']="-"

        self.assertEqual(True,host.attribute_is_empty("host_name"))
        self.assertEqual(True,host.attribute_is_empty("contacts"))
        self.assertEqual(True,host.attribute_is_empty("hostgroups"))
        self.assertEqual(True,host.attribute_is_empty("contact_groups"))
        self.assertEqual(True,host.attribute_is_empty("_non_existing_attribute"))

        self.assertEqual(False,host.attribute_is_empty("address"))

    def test_contactgroup_delete_recursive_cleanup(self):
        """Test if the right objects are removed when a contactgroup is deleted"""
        """ => test with delete(recursive=True,cleanup_related_items=True) """
        all_contactgroups = pynag.Model.Contactgroup.objects.get_all()
        all_contactgroup_names = map(lambda x: x.name, all_contactgroups)

        #creating test object
        chars = string.letters + string.digits
        cg_name = "cg_to_be_deleted_recursive_cleanup" + ''.join([random.choice(chars) for i in xrange(10)])
        cg =  pynag.Model.Contactgroup()
        # Produce an error if our randomly generated contactgroup already exists in config
        self.assertTrue(cg_name not in all_contactgroup_names)
        cg['contactgroup_name']   = cg_name
        cg.save() # an object has to be saved before we can delete it!

        # since the contactgroup is unique as per the check above, the dependent escalations will consequently be unique as well
        hostesc_stay = pynag.Model.HostEscalation(contacts="contact_STAYS", contact_groups=cg_name,      name="stay").save()
        hostesc_del  = pynag.Model.HostEscalation(contacts=None,            contact_groups="+"+cg_name,  name="del").save()
        hostesc_del2 = pynag.Model.HostEscalation(contacts='',              contact_groups=cg_name,      name="del2").save()
        host         = pynag.Model.Host(          contacts="contact_STAYS", contact_groups=cg_name,      name="hoststay").save()
        contact      = pynag.Model.Contact(       contactgroups=cg_name,                                 contact_name="contactstay").save()

        cg.delete(recursive=True,cleanup_related_items=True)

        all_contactgroups_after_delete = pynag.Model.Contactgroup.objects.get_all()
        self.assertEqual(all_contactgroups,all_contactgroups_after_delete)

        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay")[0].attribute_is_empty("contact_groups"))
        self.assertEqual(1,len(pynag.Model.Host.objects.filter(name="hoststay")))
        self.assertTrue(pynag.Model.Host.objects.filter(name="hoststay")[0].attribute_is_empty("contact_groups"))
        self.assertEqual(1,len(pynag.Model.Contact.objects.filter(contact_name="contactstay")))
        self.assertTrue(pynag.Model.Contact.objects.filter(contact_name="contactstay")[0].attribute_is_empty("contactgroups"))
        self.assertEqual(0,len(pynag.Model.HostEscalation.objects.filter(name="del")))
        self.assertEqual(0,len(pynag.Model.HostEscalation.objects.filter(name="del2")))

    def test_contactgroup_delete_nonRecursive_cleanup(self):
        """Test if the right objects are _NOT_ removed when a contactgroup is deleted with recursive=False"""
        """ => test with delete(recursive=False,cleanup_related_items=True) """
        all_contactgroups = pynag.Model.Contactgroup.objects.get_all()
        all_contactgroup_names = map(lambda x: x.name, all_contactgroups)

        #creating test object
        chars = string.letters + string.digits
        cg_name = "cg_to_be_deleted_nonRecursive_cleanup" + ''.join([random.choice(chars) for i in xrange(10)])
        cg =  pynag.Model.Contactgroup()
        # Produce an error if our randomly generated contactgroup already exists in config
        self.assertTrue(cg_name not in all_contactgroup_names)
        cg['contactgroup_name']   = cg_name
        cg.save() # an object has to be saved before we can delete it!

        # since the contactgroup is unique as per the check above, the dependent escalations will consequently be unique as well
        hostesc_stay = pynag.Model.HostEscalation(contacts="contact_STAYS", contact_groups=cg_name,      name="stay").save()
        hostesc_stay2= pynag.Model.HostEscalation(contacts=None,            contact_groups="+"+cg_name,  name="stay2").save()
        hostesc_stay3= pynag.Model.HostEscalation(contacts='',              contact_groups=cg_name,      name="stay3").save()

        cg.delete(recursive=False,cleanup_related_items=True)

        all_contactgroups_after_delete = pynag.Model.Contactgroup.objects.get_all()
        self.assertEqual(all_contactgroups,all_contactgroups_after_delete)

        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay")[0].attribute_is_empty("contact_groups"))
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay2")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay2")[0].attribute_is_empty("contact_groups"))
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay3")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay3")[0].attribute_is_empty("contact_groups"))

    def test_contactgroup_delete_nonRecursive_nonCleanup(self):
        """Test if the no changes are made to related items if contactgroup is deleted"""
        """ => test with delete(recursive=False,cleanup_related_items=False) """

        all_contactgroups = pynag.Model.Contactgroup.objects.get_all()
        all_contactgroup_names = map(lambda x: x.name, all_contactgroups)

        #creating test object
        chars = string.letters + string.digits
        cg_name = "cg_to_be_deleted_nonRecursive_nonCleanup" + ''.join([random.choice(chars) for i in xrange(10)])
        cg =  pynag.Model.Contactgroup()
        # Produce an error if our randomly generated contactgroup already exists in config
        self.assertTrue(cg_name not in all_contactgroup_names)
        cg['contactgroup_name']   = cg_name
        cg.save() # an object has to be saved before we can delete it!

        # since the contactgroup is unique as per the check above, the dependent escalations will consequently be unique as well
        hostesc_stay = pynag.Model.HostEscalation(contacts="contact_STAYS", contact_groups=cg_name,      name="stay").save()
        hostesc_stay2= pynag.Model.HostEscalation(contacts=None,            contact_groups="+"+cg_name,  name="stay2").save()
        hostesc_stay3= pynag.Model.HostEscalation(contacts='',              contact_groups=cg_name,      name="stay3").save()
        cg.delete(recursive=False,cleanup_related_items=False)

        all_contactgroups_after_delete = pynag.Model.Contactgroup.objects.get_all()
        self.assertEqual(all_contactgroups,all_contactgroups_after_delete)

        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay")))
        self.assertFalse(pynag.Model.HostEscalation.objects.filter(name="stay")[0].attribute_is_empty("contact_groups"))
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay2")))
        self.assertFalse(pynag.Model.HostEscalation.objects.filter(name="stay2")[0].attribute_is_empty("contact_groups"))
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay3")))
        self.assertFalse(pynag.Model.HostEscalation.objects.filter(name="stay3")[0].attribute_is_empty("contact_groups"))

    def test_contactgroup_delete_recursive_nonCleanup(self):
        """Test if the no changes are made to related items if contactgroup is deleted - no deletion should happen even with recursive=True"""
        """ => test with delete(recursive=True,cleanup_related_items=False) """
        """ should have the same results as  test_contactgroup_delete_nonRecursive_nonCleanup()"""

        all_contactgroups = pynag.Model.Contactgroup.objects.get_all()
        all_contactgroup_names = map(lambda x: x.name, all_contactgroups)

        #creating test object
        chars = string.letters + string.digits
        cg_name = "cg_to_be_deleted_recursive_nonCleanup" + ''.join([random.choice(chars) for i in xrange(10)])
        cg =  pynag.Model.Contactgroup()
        # Produce an error if our randomly generated contactgroup already exists in config
        self.assertTrue(cg_name not in all_contactgroup_names)
        cg['contactgroup_name']   = cg_name
        cg.save() # an object has to be saved before we can delete it!

        # since the contactgroup is unique as per the check above, the dependent escalations will consequently be unique as well
        hostesc_stay = pynag.Model.HostEscalation(contacts="contact_STAYS", contact_groups=cg_name,      name="stay").save()
        hostesc_stay2= pynag.Model.HostEscalation(contacts=None,            contact_groups="+"+cg_name,  name="stay2").save()
        hostesc_stay3= pynag.Model.HostEscalation(contacts='',              contact_groups=cg_name,      name="stay3").save()

        cg.delete(recursive=True,cleanup_related_items=False)

        all_contactgroups_after_delete = pynag.Model.Contactgroup.objects.get_all()
        self.assertEqual(all_contactgroups,all_contactgroups_after_delete)

        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay")))
        self.assertFalse(pynag.Model.HostEscalation.objects.filter(name="stay")[0].attribute_is_empty("contact_groups"))
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay2")))
        self.assertFalse(pynag.Model.HostEscalation.objects.filter(name="stay2")[0].attribute_is_empty("contact_groups"))
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay3")))
        self.assertFalse(pynag.Model.HostEscalation.objects.filter(name="stay3")[0].attribute_is_empty("contact_groups"))

    def test_contact_delete_recursive_cleanup(self):
        """Test if the right objects are removed when a contact is deleted"""
        """ => test with delete(recursive=True,cleanup_related_items=True) """
        all_contacts = pynag.Model.Contact.objects.get_all()
        all_contact_names = map(lambda x: x.name, all_contacts)

        #creating test object
        chars = string.letters + string.digits
        c_name = "c_to_be_deleted_recursive_cleanup" + ''.join([random.choice(chars) for i in xrange(10)])
        c =  pynag.Model.Contact()
        # Produce an error if our randomly generated contact already exists in config
        self.assertTrue(c_name not in all_contact_names)
        c['contact_name']   = c_name
        c.save() # an object has to be saved before we can delete it!

        # since the contact is unique as per the check above, the dependent escalations will consequently be unique as well
        hostesc_stay = pynag.Model.HostEscalation(contact_groups="contactgroup_STAYS", contacts=c_name,      name="stay").save()
        hostesc_del  = pynag.Model.HostEscalation(contact_groups=None,                 contacts="+"+c_name,  name="del").save()
        hostesc_del2 = pynag.Model.HostEscalation(contact_groups='',                   contacts=c_name,      name="del2").save()
        contactGroup = pynag.Model.Contactgroup(  contactgroup_name="cgstay",          members=c_name                   ).save()

        c.delete(recursive=True,cleanup_related_items=True)

        all_contacts_after_delete = pynag.Model.Contact.objects.get_all()
        self.assertEqual(all_contacts,all_contacts_after_delete)

        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay")[0].attribute_is_empty("contacts"))
        self.assertEqual(1,len(pynag.Model.Contactgroup.objects.filter(contactgroup_name="cgstay")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay")[0].attribute_is_empty("members"))
        self.assertEqual(0,len(pynag.Model.HostEscalation.objects.filter(name="del")))
        self.assertEqual(0,len(pynag.Model.HostEscalation.objects.filter(name="del2")))

    def test_contact_delete_nonRecursive_cleanup(self):
        """Test if the right objects are _NOT_ removed when a contact is deleted with recursive=False"""
        """ => test with delete(recursive=False,cleanup_related_items=True) """
        all_contacts = pynag.Model.Contact.objects.get_all()
        all_contact_names = map(lambda x: x.name, all_contacts)

        #creating test object
        chars = string.letters + string.digits
        c_name = "c_to_be_deleted_nonRecursive_cleanup" + ''.join([random.choice(chars) for i in xrange(10)])
        c =  pynag.Model.Contact()
        # Produce an error if our randomly generated contact already exists in config
        self.assertTrue(c_name not in all_contact_names)
        c['contact_name']   = c_name
        c.save() # an object has to be saved before we can delete it!

        # since the contact is unique as per the check above, the dependent escalations will consequently be unique as well
        hostesc_stay = pynag.Model.HostEscalation(contact_groups="contactgroup_STAYS", contacts=c_name,      name="stay").save()
        hostesc_del  = pynag.Model.HostEscalation(contact_groups=None,                 contacts="+"+c_name,  name="stay2").save()
        hostesc_del2 = pynag.Model.HostEscalation(contact_groups='',                   contacts=c_name,      name="stay3").save()

        c.delete(recursive=False,cleanup_related_items=True)

        all_contacts_after_delete = pynag.Model.Contact.objects.get_all()
        self.assertEqual(all_contacts,all_contacts_after_delete)

        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay")[0].attribute_is_empty("contacts"))
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay2")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay2")[0].attribute_is_empty("contacts"))
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay3")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay3")[0].attribute_is_empty("contacts"))

    def test_contact_delete_nonRecursive_nonCleanup(self):
        """Test if the no changes are made to related items if contact is deleted"""
        """ => test with delete(recursive=False,cleanup_related_items=False) """

        all_contacts = pynag.Model.Contact.objects.get_all()
        all_contact_names = map(lambda x: x.name, all_contacts)

        #creating test object
        chars = string.letters + string.digits
        c_name = "c_to_be_deleted_nonRecursive_nonCleanup" + ''.join([random.choice(chars) for i in xrange(10)])
        c =  pynag.Model.Contact()
        # Produce an error if our randomly generated contact already exists in config
        self.assertTrue(c_name not in all_contact_names)
        c['contact_name']   = c_name
        c.save() # an object has to be saved before we can delete it!

        # since the contact is unique as per the check above, the dependent escalations will consequently be unique as well
        hostesc_stay = pynag.Model.HostEscalation(contact_groups="contactgroup_STAYS", contacts=c_name,      name="stay").save()
        hostesc_del  = pynag.Model.HostEscalation(contact_groups=None,                 contacts="+"+c_name,  name="stay2").save()
        hostesc_del2 = pynag.Model.HostEscalation(contact_groups='',                   contacts=c_name,      name="stay3").save()
        c.delete(recursive=False,cleanup_related_items=False)

        all_contacts_after_delete = pynag.Model.Contact.objects.get_all()
        self.assertEqual(all_contacts,all_contacts_after_delete)

        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay")))
        self.assertFalse(pynag.Model.HostEscalation.objects.filter(name="stay")[0].attribute_is_empty("contacts"))
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay2")))
        self.assertFalse(pynag.Model.HostEscalation.objects.filter(name="stay2")[0].attribute_is_empty("contacts"))
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay3")))
        self.assertFalse(pynag.Model.HostEscalation.objects.filter(name="stay3")[0].attribute_is_empty("contacts"))

    def test_contact_delete_recursive_nonCleanup(self):
        """Test if the no changes are made to related items if contact is deleted - no deletion should happen even with recursive=True"""
        """ => test with delete(recursive=True,cleanup_related_items=False) """
        """ should have the same results as  test_contact_delete_nonRecursive_nonCleanup()"""

        all_contacts = pynag.Model.Contact.objects.get_all()
        all_contact_names = map(lambda x: x.name, all_contacts)

        #creating test object
        chars = string.letters + string.digits
        c_name = "c_to_be_deleted_recursive_nonCleanup" + ''.join([random.choice(chars) for i in xrange(10)])
        c =  pynag.Model.Contact()
        # Produce an error if our randomly generated contact already exists in config
        self.assertTrue(c_name not in all_contact_names)
        c['contact_name']   = c_name
        c.save() # an object has to be saved before we can delete it!

        # since the contact is unique as per the check above, the dependent escalations will consequently be unique as well
        hostesc_stay = pynag.Model.HostEscalation(contact_groups="contactgroup_STAYS", contacts=c_name,      name="stay").save()
        hostesc_del  = pynag.Model.HostEscalation(contact_groups=None,                 contacts="+"+c_name,  name="stay2").save()
        hostesc_del2 = pynag.Model.HostEscalation(contact_groups='',                   contacts=c_name,      name="stay3").save()

        c.delete(recursive=True,cleanup_related_items=False)

        all_contacts_after_delete = pynag.Model.Contact.objects.get_all()
        self.assertEqual(all_contacts,all_contacts_after_delete)

        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay")))
        self.assertFalse(pynag.Model.HostEscalation.objects.filter(name="stay")[0].attribute_is_empty("contacts"))
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay2")))
        self.assertFalse(pynag.Model.HostEscalation.objects.filter(name="stay2")[0].attribute_is_empty("contacts"))
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay3")))
        self.assertFalse(pynag.Model.HostEscalation.objects.filter(name="stay3")[0].attribute_is_empty("contacts"))

    def test_hostgroup_delete_recursive_cleanup(self):
        """Test if the right objects are removed when a hostgroup is deleted"""
        """ => test with delete(recursive=True,cleanup_related_items=True) """
        all_hostgroups = pynag.Model.Hostgroup.objects.get_all()
        all_hostgroup_names = map(lambda x: x.name, all_hostgroups)

        #creating test object
        chars = string.letters + string.digits
        hg_name = "hg_to_be_deleted_recursive_cleanup" + ''.join([random.choice(chars) for i in xrange(10)])
        hg =  pynag.Model.Hostgroup()
        # Produce an error if our randomly generated hostgroup already exists in config
        self.assertTrue(hg_name not in all_hostgroup_names)
        hg['hostgroup_name']   = hg_name
        hg.save() # an object has to be saved before we can delete it!

        # since the hostgroup is unique as per the check above, the dependent escalations will consequently be unique as well
        hostesc_stay = pynag.Model.HostEscalation(host_name="host_STAYS", hostgroup_name=hg_name,           name="stay").save()
        hostesc_del  = pynag.Model.HostEscalation(host_name=None,            hostgroup_name="+"+hg_name,         name="del").save()


        hostdep_stay = pynag.Model.HostDependency(host_name='host_STAYS',dependent_host_name="host_stays", hostgroup_name=hg_name, name="stay").save()
        hostdep_del  = pynag.Model.HostDependency(host_name='host_STAYS',dependent_hostgroup_name=hg_name,          name="del").save()
        hostdep_unrl = pynag.Model.HostDependency(dependent_host_name='foobar',hostgroup_name="unrelated_hg",    name="stays_because_its_not_related_to_deleted_hg").save()

        hoststay     = pynag.Model.Host(host_name="host_STAYS",    hostgroups=hg_name,                      name="hoststay").save()

        svcEscdel    = pynag.Model.ServiceEscalation(hostgroup_name=hg_name,                                name="svcEscdel").save()

        hg.delete(recursive=True,cleanup_related_items=True)

        all_hostgroups_after_delete = pynag.Model.Hostgroup.objects.get_all()
        self.assertEqual(all_hostgroups,all_hostgroups_after_delete)

        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay")[0].attribute_is_empty("hostgroup_name"))
        self.assertEqual(0,len(pynag.Model.HostEscalation.objects.filter(name="del")))

        self.assertEqual(1,len(pynag.Model.HostDependency.objects.filter(name="stay")))
        self.assertEqual(0,len(pynag.Model.HostDependency.objects.filter(name="del")))
        self.assertEqual(1,len(pynag.Model.HostDependency.objects.filter(name="stays_because_its_not_related_to_deleted_hg")))

        self.assertEqual(1,len(pynag.Model.Host.objects.filter(name="hoststay")))
        self.assertTrue(pynag.Model.Host.objects.filter(name="hoststay")[0].attribute_is_empty("hostgroup_name"))

        self.assertEqual(0,len(pynag.Model.ServiceEscalation.objects.filter(name="svcEscdel")))

    def test_hostgroup_delete_nonRecursive_cleanup(self):
        """Test if the right objects are cleaned up when a hostgroup is deleted"""
        """ => test with delete(recursive=False,cleanup_related_items=True) """
        all_hostgroups = pynag.Model.Hostgroup.objects.get_all()
        all_hostgroup_names = map(lambda x: x.name, all_hostgroups)

        #creating test object
        chars = string.letters + string.digits
        hg_name = "hg_to_be_deleted_nonRecursive_cleanup" + ''.join([random.choice(chars) for i in xrange(10)])
        hg =  pynag.Model.Hostgroup()
        # Produce an error if our randomly generated hostgroup already exists in config
        self.assertTrue(hg_name not in all_hostgroup_names)
        hg['hostgroup_name']   = hg_name
        hg.save() # an object has to be saved before we can delete it!

        # since the hostgroup is unique as per the check above, the dependent escalations will consequently be unique as well
        hostesc_stay = pynag.Model.HostEscalation(host_name="host_STAYS", hostgroup_name=hg_name,           name="stay").save()
        hostesc_stay2= pynag.Model.HostEscalation(host_name=None,         hostgroup_name="+"+hg_name,       name="stay2").save()

        hostdep_stay = pynag.Model.HostDependency(host_name='host_STAYS',dependent_host_name="host_stays", hostgroup_name=hg_name, name="stay").save()
        hostdep_stay2= pynag.Model.HostDependency(host_name='host_STAYS',dependent_hostgroup_name=hg_name,                         name="stay2").save()

        svcEscstay    = pynag.Model.ServiceEscalation(hostgroup_name=hg_name,                                name="svcEscstay").save()

        hg.delete(recursive=False,cleanup_related_items=True)

        all_hostgroups_after_delete = pynag.Model.Hostgroup.objects.get_all()
        self.assertEqual(all_hostgroups,all_hostgroups_after_delete)

        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay")[0].attribute_is_empty("hostgroup_name"))
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay2")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay2")[0].attribute_is_empty("hostgroup_name"))

        self.assertEqual(1,len(pynag.Model.HostDependency.objects.filter(name="stay")))
        self.assertTrue(pynag.Model.HostDependency.objects.filter(name="stay")[0].attribute_is_empty("hostgroup_name"))
        self.assertEqual(1,len(pynag.Model.HostDependency.objects.filter(name="stay2")))
        self.assertTrue(pynag.Model.HostDependency.objects.filter(name="stay2")[0].attribute_is_empty("dependent_hostgroup_name"))

        self.assertEqual(1,len(pynag.Model.ServiceEscalation.objects.filter(name="svcEscstay")))
        self.assertTrue(pynag.Model.ServiceEscalation.objects.filter(name="svcEscstay")[0].attribute_is_empty("hostgroup_name"))

    def test_host_delete_recursive_cleanup(self):
        """Test if the right objects are removed when a host is deleted"""
        """ => test with delete(recursive=True,cleanup_related_items=True) """
        all_hosts = pynag.Model.Host.objects.get_all()
        all_host_names = map(lambda x: x.name, all_hosts)

        #creating test object
        chars = string.letters + string.digits
        h_name = "h_to_be_deleted_recursive_cleanup" + ''.join([random.choice(chars) for i in xrange(10)])
        h =  pynag.Model.Host()
        # Produce an error if our randomly generated host already exists in config
        self.assertTrue(h_name not in all_host_names)
        h['host_name']   = h_name
        h.save() # an object has to be saved before we can delete it!

        # since the host is unique as per the check above, the dependent escalations will consequently be unique as well
        hostesc_stay = pynag.Model.HostEscalation(hostgroup_name="hostgroup_STAYS", host_name=h_name,           name="stay").save()
        hostesc_del  = pynag.Model.HostEscalation(hostgroup_name=None,            host_name="+"+h_name,         name="del").save()


        hostdep_stay = pynag.Model.HostDependency(hostgroup_name='hostgroup_STAYS',dependent_host_name="host_stays", host_name=h_name, name="stay").save()
        hostdep_del  = pynag.Model.HostDependency(hostgroup_name='hostgroup_STAYS',dependent_host_name=h_name,          name="del").save()

        svcEscdel    = pynag.Model.ServiceEscalation(host_name=h_name,                                name="svcEscdel").save()

        h.delete(recursive=True,cleanup_related_items=True)

        all_hosts_after_delete = pynag.Model.Host.objects.get_all()
        self.assertEqual(all_hosts,all_hosts_after_delete)

        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay")[0].attribute_is_empty("host_name"))
        self.assertEqual(0,len(pynag.Model.HostEscalation.objects.filter(name="del")))

        self.assertEqual(1,len(pynag.Model.HostDependency.objects.filter(name="stay")))
        self.assertEqual(0,len(pynag.Model.HostDependency.objects.filter(name="del")))

        self.assertEqual(0,len(pynag.Model.ServiceEscalation.objects.filter(name="svcEscdel")))

    def test_host_delete_nonRecursive_cleanup(self):
        """Test if the right objects are cleaned up when a host is deleted"""
        """ => test with delete(recursive=False,cleanup_related_items=True) """
        all_hosts = pynag.Model.Host.objects.get_all()
        all_host_names = map(lambda x: x.name, all_hosts)

        #creating test object
        chars = string.letters + string.digits
        h_name = "h_to_be_deleted_nonRecursive_cleanup" + ''.join([random.choice(chars) for i in xrange(10)])
        h =  pynag.Model.Host()
        # Produce an error if our randomly generated host already exists in config
        self.assertTrue(h_name not in all_host_names)
        h['host_name']   = h_name
        h.save() # an object has to be saved before we can delete it!

        # since the host is unique as per the check above, the dependent escalations will consequently be unique as well
        hostesc_stay = pynag.Model.HostEscalation(hostgroup_name="hostgroup_STAYS", host_name=h_name,           name="stay").save()
        hostesc_stay2= pynag.Model.HostEscalation(hostgroup_name=None,         host_name="+"+h_name,       name="stay2").save()

        hostdep_stay = pynag.Model.HostDependency(hostgroup_name='hostgroup_STAYS',dependent_host_name="host_stays", host_name=h_name, name="stay").save()
        hostdep_stay2= pynag.Model.HostDependency(hostgroup_name='hostgroup_STAYS',dependent_host_name=h_name,                         name="stay2").save()

        svcEscstay    = pynag.Model.ServiceEscalation(host_name=h_name,                                name="svcEscstay").save()

        h.delete(recursive=False,cleanup_related_items=True)

        all_hosts_after_delete = pynag.Model.Host.objects.get_all()
        self.assertEqual(all_hosts,all_hosts_after_delete)

        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay")[0].attribute_is_empty("host_name"))
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay2")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay2")[0].attribute_is_empty("host_name"))

        self.assertEqual(1,len(pynag.Model.HostDependency.objects.filter(name="stay")))
        self.assertTrue(pynag.Model.HostDependency.objects.filter(name="stay")[0].attribute_is_empty("host_name"))
        self.assertEqual(1,len(pynag.Model.HostDependency.objects.filter(name="stay2")))
        self.assertTrue(pynag.Model.HostDependency.objects.filter(name="stay2")[0].attribute_is_empty("dependent_host_name"))

        self.assertEqual(1,len(pynag.Model.ServiceEscalation.objects.filter(name="svcEscstay")))
        self.assertTrue(pynag.Model.ServiceEscalation.objects.filter(name="svcEscstay")[0].attribute_is_empty("host_name"))

    def test_add_hosts_to_hostgroups(self):
        """ Test pynag.Model.Host.add_to_hostgroup """
        host_name = "testhost1"
        hostgroup_name = "testhostgroup1"
        hostgroup = pynag.Model.Hostgroup(hostgroup_name=hostgroup_name)
        hostgroup.save()
        host1 = pynag.Model.Host(host_name=host_name)
        host1.save()

        message = "Newly created host should not belong to any hostgroups"
        self.assertEqual(False, hostgroup_name in pynag.Utils.AttributeList(host1.hostgroups), message)
        self.assertEqual(False, host_name in pynag.Utils.AttributeList(hostgroup.members), message)

        message = "Host should belong to hostgroup after we specificly add it"
        host1.add_to_hostgroup(hostgroup_name)
        self.assertEqual(True, hostgroup_name in pynag.Utils.AttributeList(host1.hostgroups), message)
        self.assertEqual(False, host_name in pynag.Utils.AttributeList(hostgroup.members), message)

        message = "Host should not belong to hostgroup after we have removed it"
        host1.remove_from_hostgroup(hostgroup_name)
        self.assertEqual(False, hostgroup_name in pynag.Utils.AttributeList(host1.hostgroups), message)
        self.assertEqual(False, host_name in pynag.Utils.AttributeList(hostgroup.members), message)

        # Lets try the same via the hostgroup:
        message = "Host should belong to hostgroup after we have specifically added host to that hostgroup"
        hostgroup.add_host(host_name)
        host1 = pynag.Model.Host.objects.get_by_shortname(host_name)
        self.assertEqual(True, hostgroup_name in pynag.Utils.AttributeList(host1.hostgroups), message)
        self.assertEqual(False, host_name in pynag.Utils.AttributeList(hostgroup.members), message)

        message = "Hostgroup should not have host after we specifically remove the host"
        hostgroup.remove_host(host_name)
        host1 = pynag.Model.Host.objects.get_by_shortname(host_name)
        self.assertEqual(False, hostgroup_name in pynag.Utils.AttributeList(host1.hostgroups), message)
        self.assertEqual(False, host_name in pynag.Utils.AttributeList(hostgroup.members), message)

    def test_effective_hostgroups(self):
        """ Test get_effective_hostgroups() against stuff in dataset01 """
        production_servers = pynag.Model.Hostgroup.objects.get_by_shortname('production_servers')
        production_server1 = pynag.Model.Host.objects.get_by_shortname('production_server1')

        development_servers = pynag.Model.Hostgroup.objects.get_by_shortname('development_servers')
        development_server1 = pynag.Model.Host.objects.get_by_shortname('development_server1')

        prod_and_dev = pynag.Model.Hostgroup.objects.get_by_shortname('prod_and_dev')

        production_service = pynag.Model.Service.objects.get_by_shortname('prod_service')

        groups_for_production_server1 = production_server1.get_effective_hostgroups()
        groups_for_development_server1 = development_server1.get_effective_hostgroups()

        self.assertEqual([prod_and_dev, production_servers], groups_for_production_server1)
        self.assertEqual([development_servers, prod_and_dev], groups_for_development_server1)

        self.assertEqual([], development_servers.get_effective_hostgroups())
        self.assertEqual([], production_servers.get_effective_hostgroups())
        self.assertEqual([development_servers, production_servers], prod_and_dev.get_effective_hostgroups())

        self.assertEqual([development_server1], development_servers.get_effective_hosts())
        self.assertEqual([production_server1], production_servers.get_effective_hosts())
        self.assertEqual([development_server1, production_server1], prod_and_dev.get_effective_hosts())

        self.assertEqual(production_servers.get_effective_services(), [production_service])
        self.assertEqual(prod_and_dev.get_effective_services(), [])
        self.assertEqual(development_servers.get_effective_services(), [])

        self.assertEqual(production_service.get_effective_hostgroups(), [production_servers])

class Model2(unittest.TestCase):
    """ Another class for testing pynag.Model. Should replace Model at some point.

    The reason methods here are in a new class is because we are moving to a new set of tests
    that use Utils.misc.FakeNagiosEnvironment. It's not a bad idea to migrate tests from the old
    class into this one here, one at a time.
    """
    def setUp(self):
        self.environment = pynag.Utils.misc.FakeNagiosEnvironment()
        self.environment.create_minimal_environment()
        self.environment.update_model()

    def tearDown(self):
        self.environment.terminate()

    def test_contactgroups_effective_services(self):
        cfg_file = os.path.join(tests_dir, 'dataset01/nagios/conf.d/contactgroups.cfg')
        self.environment.import_config(cfg_file)

        contactgroup = pynag.Model.Contactgroup.objects.get_by_shortname('test_contactgroup_role_1')

        self.assertEqual(len(contactgroup.get_effective_services()), 1)

    def test_rename(self):
        """ Generic test of Model.*.rename()
        """
        old = "host1"
        new = "host2"
        host = pynag.Model.Host(host_name=old)
        host.save()

        host = pynag.Model.Host.objects.get_by_shortname(old)
        self.assertTrue(host.host_name == old)
        host.rename(new)

        host = pynag.Model.Host.objects.get_by_shortname(new)
        self.assertTrue(host.host_name == new)

        hosts_with_old_name = pynag.Model.Host.objects.filter(host_name=old)
        self.assertFalse(hosts_with_old_name, "There should be no hosts with the old name")

    def test_rename_contact(self):
        """ test Model.*.rename() function """
        # Create a contact, and contactgroup. Put the contact in the contactgroup
        contact_name1 = "some contact"
        contact_name2 = "new name for contact"
        contactgroup_name = "contactgroup1"
        contact = pynag.Model.Contact(contact_name=contact_name1)
        contact.save()
        contactgroup = pynag.Model.Contactgroup(contactgroup_name=contactgroup_name, members=contact_name1)
        contactgroup.save()

        # Verify the contact is in our contactgroup
        c = pynag.Model.Contactgroup.objects.get_by_shortname(contactgroup_name)
        self.assertTrue(c.members == contact_name1)

        # Rename the contact, doublecheck that the contactgroup changed.
        contact.rename(contact_name2)
        c = pynag.Model.Contactgroup.objects.get_by_shortname(contactgroup_name)
        self.assertTrue(c.members == contact_name2)

    @unittest.skipIf(os.getenv('TRAVIS', None) == 'true', "Running in Travis")  # Doesnt work in travis for some reason
    def test_get_current_status(self):
        """ Test Model.*.get_current_status """
        self.environment.start()

        # status.dat takes a while to get created, so we have to wait a little bit
        time_start = time.time()
        timeout = 3000  # Give nagios 10sec to create a status.dat file
        status_file = self.environment.config.get_cfg_value('status_file')
        while not os.path.exists(status_file):
            time.sleep(0.1)
            time_now = time.time()
            time_elapsed = time_now - time_start
            if time_elapsed > timeout:
                raise Exception("Timed out while waiting for nagios to create status.dat" % (status_file))
        # Fetch host, and get its current status
        host = pynag.Model.Host.objects.get_by_shortname("ok_host")
        host_status = host.get_current_status()
        self.assertTrue(host_status, "Trying to find host ok_host")
        self.assertTrue('current_state' in host_status)

        # Do the same for service
        service = host.get_effective_services()[0]
        service_status = service.get_current_status()
        self.assertTrue(service_status)
        self.assertTrue('current_state' in service_status)

class NagiosReloadHandler(unittest.TestCase):
    """ Test Eventhandler NagiosReloadHandler
    """
    def setUp(self):
        self.handler = pynag.Model.EventHandlers.NagiosReloadHandler(nagios_init="/bin/ls")
        self.handler._reload = mock.MagicMock()

    def test_write(self):
        self.handler.write(None, None)

    def test_save(self):
        self.handler.pre_save(None, None)
        self.handler.save(None, None)


class ObjectRelations(unittest.TestCase):
    """ Test pynag.Model.ObjectRelations """
    def setUp(self):
        pass

    def test_get_subgroups(self):
        c = pynag.Utils.defaultdict(set)
        c['everything'] = set(['admins', 'nonadmins', 'operators', 'users'])
        c['nonadmins'] = set(['users'])
        c['users'] = set()
        c['admins'] = set(['sysadmins', 'network-admins', 'database-admins'])
        c['nonadmins'] = set(['users'])
        members_of_everything_actual = pynag.Model.ObjectRelations._get_subgroups('everything', c)
        members_of_everything_expected = set(['users', 'operators', 'sysadmins', 'network-admins', 'admins', 'nonadmins', 'database-admins'])
        self.assertEqual(members_of_everything_actual, members_of_everything_expected)


if __name__ == "__main__":
    unittest.main()

# vim: sts=4 expandtab autoindent
