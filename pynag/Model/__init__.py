# -*- coding: utf-8 -*-

import sys
import os
import re
sys.path.insert(1, '/opt/pynag')
from pynag.Parsers import config
import time

"""
This module provides a high level Object-Oriented wrapper around pynag.Parsers.config.

example usage:

from pynag.Parsers import Service,Host

all_services = Service.objects.all
my_service=all_service[0]
print my_service.host_name

example_host = Host.objects.filter(host_name="host.example.com")
canadian_hosts = Host.objects.filter(host_name__endswith=".ca")

for i in canadian_hosts:
	i.alias = "this host is located in Canada"
	i.save()
"""

__author__ = "Pall Sigurdsson"
__copyright__ = "Copyright 2011, Pall Sigurdsson"
__credits__ = ["Pall Sigurdsson"]
__license__ = "GPL"
__version__ = "0.3"
__maintainer__ = "Pall Sigurdsson"
__email__ = "palli@opensource.is"
__status__ = "Development"


# Path To Nagios configuration file
cfg_file = '/etc/nagios/nagios.cfg'
config = config(cfg_file)
config.parse()



def debug(text):
	debug = True
	if debug: print text



def contains(str1, str2):
	'Returns True if str1 contains str2'
	if str1.find(str2) > -1: return True

def not_contains(str1, str2):
	'Returns True if str1 does not contain str2'
	return not contains(str1, str2)

def is_a_field(str1, str2):
	'''Returns True if str2 is a field in str1
	
	For this purpose the string 'example' is a field in '+this,is,an,example'
	'''
	str1 = str1.strip('+')
	str1 = str1.split(',')
	if str2 in str1: return True
	return False
class ObjectFetcher(object):
	'''
	This class is a wrapper around pynag.Parsers.config. Is responsible for fetching dict objects
	from config.data and turning into high ObjectDefinition objects
	'''
	def __init__(self, object_type):
		self.object_type = object_type
		self.objects = []
	@property
	def all(self):
		" Return all object definitions of specified type"
		if self.objects != []:
			return self.objects
		if self.object_type != None:
			key_name = "all_%s" % (self.object_type)
			if not config.data.has_key(key_name):
				return []
			objects = config.data[ key_name ]
		else:
			# If no object type was requested
			objects = []
			for v in config.data.values():
				objects += v
		for i in objects:
			Class = string_to_class[ i['meta']['object_type'] ]
			i = Class(item=i)
			self.objects.append(i)
		return self.objects
	def get_by_id(self, id):
		''' Get one specific object
		
		Returns:
			ObjectDefinition
		Raises:
			ValueError if object is not found
		'''
		id = int(id)
		for item in self.all:
			item_id = item['id']
			if item['id'] == id:
				return item
		raise ValueError('No object with ID=%s found'% (id))
	def filter(self, **kwargs):
		'''
		Returns all objects that match the selected filter
		
		Examples:
		# Get all services where host_name is examplehost.example.com
		Service.objects.filter(host_name='examplehost.example.com')
		
		# Get service with host_name=examplehost.example.com and service_description='Ping'
		Service.objects.filter(host_name='examplehost.example.com',service_description='Ping')
		
		# Get all services that are registered but without a host_name
		Service.objects.filter(host_name=None,register='1')

		# Get all hosts that start with 'exampleh'
		Host.objects.filter(host_name__startswith='exampleh')
		
		# Get all hosts that end with 'example.com'
		Service.objects.filter(host_name__endswith='example.com')
		
		# Get all contactgroups that contain 'dba'
		Contactgroup.objects.filter(host_name__contains='dba')

		# Get all hosts that are not in the 'testservers' hostgroup
		Host.objects.filter(hostgroup_name__notcontains='testservers')
		# Get all services with non-empty name
		Service.objects.filter(name__isnot=None)
		'''
		# TODO: Better testing of these cases:
		# register = 1
		# id attribute
		# any attribute = None or 'None'
		result = []
		# Lets convert all values to str()
		tmp = {}
		for k,v in kwargs.items():
			k = str(k)
			if v != None: v = str(v)
			tmp[k] = v
		kwargs = tmp
		for i in self.all:
			object_matches = True
			for k, v in kwargs.items():
				if k.endswith('__startswith'):
					k = k[:-12]
					match_function = str.startswith
				elif k.endswith('__endswith'):
					k = k[:-10]
					match_function = str.endswith
				elif k.endswith('__isnot'):
					k = k[:-7]
					match_function = str.__ne__
				elif k.endswith('__contains'):
					k = k[:-10]
					match_function = contains
				elif k.endswith('__is_a_field'):
					k = k[:-12]
					match_function = is_a_field
				elif k.endswith('__notcontains'):
					k = k[:-13]
					match_function = not_contains
				else:
					match_function = str.__eq__
				if k == 'id' and str(v) == str(i.get_id()):
					object_matches = True
					break
				if k == 'register' and v == '1' and not i.has_key(k):
					'not defined means item is registered'
					continue
				if v == None and i.has_key(k):
					object_matches = False
					break
				if not i.has_key(k):
					if v == None: continue # if None was the search attribute
					object_matches = False
					break
				if not match_function(i[k], v):
					object_matches = False
					break
			if object_matches:
				result.append(i)
		return result		


class ObjectDefinition(object):
	'''
	Holds one instance of one particular Object definition
	Example usage:
		objects = ObjectDefinition.objects.all
		my_object ObjectDefinition( dict ) # dict = hash map of configuration attributes
	'''
	object_type = None
	objects = ObjectFetcher(None)
	def __init__(self, item):
		self.object_type = item['meta']['object_type']
		
		# self.objects is a convenient way to access more objects of the same type
		self.objects = ObjectFetcher(self.object_type)
		# self.data -- This dict stores all effective attributes of this objects
		self._original_attributes = item
		
		#: _changes - This dict contains any changed (but yet unsaved) attributes of this object 
		self._changes = {}
		
		#: _defined_attributes - All attributes that this item has defined
		self._defined_attributes = item['meta']['defined_attributes']
		
		#: _inherited_attributes - All attributes that this object has inherited via 'use'
		self._inherited_attributes = item['meta']['inherited_attributes']
		
		#: _meta - Various metadata about the object
		self._meta = item['meta']
		#for k,v in self.data.items():
		#	self.__setattr__(k,v)
	def is_dirty(self):
		"Returns true if any attributes has been changed on this object, and therefore it needs saving"
		return len(self._changes.keys()) == 0
	def __setitem__(self, key, item):
		self._changes[key] = item
		#self.data[key] = item
	def __getitem__(self, key):
		if key == 'id':
			return self.get_id()
		if key == 'description':
			return self.get_description()
		if key == 'register' and not self._defined_attributes.has_key('register'):
			return "1"
		if self._changes.has_key(key):
			return self._changes[key]
		elif self._defined_attributes.has_key(key):
			return self._defined_attributes[key]
		elif self._inherited_attributes.has_key(key):
			return self._inherited_attributes[key]
		elif self._meta.has_key(key):
			return self._meta[key]
		else:
			return None
	def has_key(self, key):
		return key in self.keys()
		if self._changes.has_key(key):
			return True
		elif self._defined_attributes.has_key(key):
			return True
		elif self._inherited_attributes.has_key(key):
			return True
		else:
			return False
	def keys(self):
		all_keys = []
		for k in self._changes.keys():
			if k not in all_keys: all_keys.append(k)
		for k in self._inherited_attributes.keys():
			if k not in all_keys: all_keys.append(k)
		for k in self._defined_attributes.keys():
			if k not in all_keys: all_keys.append(k)
		for k in self._meta.keys():
			if k not in all_keys: all_keys.append(k)
		return all_keys
	def items(self):
		return self._original_attributes.items()
	def get_id(self):
		""" Return a unique ID for this object"""
		return self.__str__().__hash__()
	def save(self):
		"""Saves any changes to the current object to its configuration file
		
		Returns:
			Number of changes made to the object
		"""
		number_of_changes = 0
		for field_name, new_value in self._changes.items():
			save_result = config.edit_object(item=self._original_attributes, field_name=field_name, new_value=new_value)
			if save_result == True:
				self._defined_attributes[field_name] = new_value
				self._original_attributes[field_name] = new_value
				del self._changes[field_name]
				number_of_changes += 1
		return number_of_changes
		
	def __str__(self):
		return_buffer = "define %s {\n" % (self.object_type)
		fields = self.keys()
		fields.sort()
		interesting_fields = ['service_description', 'use', 'name', 'host_name']
		for i in interesting_fields:
			if i in fields:
				fields.remove(i)
				fields.insert(0, i)
			
		for key in fields:
			if key == 'meta': continue
			value = self[key]
			return_buffer = return_buffer + "\t%s = %s\n" % (key, value)
		return_buffer = return_buffer + "}\n\n"
		return return_buffer
	def __repr__(self):
		result = ""
		result += "%s: " % self.__class__.__name__
		for i in  ['host_name', 'name', 'use', 'service_description']:
			if self.has_key(i):
				result += " %s=%s " % (i, self[i])
			else:
				result += "%s=None " % (i)
		return result
	def get_description(self):
		raise NotImplementedError()
	def get_effective_parents(self):
		""" Get all objects that this one inherits via "use" attribute
		Returns:
			a list of ObjectDefinition objects
		"""
		if not self.has_key('use'):
			return []
		results = []
		use = self['use'].split(',')
		for parent_name in use:
			results.append( self.objects.filter(name=parent_name)[0] )
		return results
	def get_effective_hostgroups(self):
		"""Get all hostgroups that this object belongs to (not just the ones it defines on its own
		
		How can a hostgroup be linked to this object:
			1) This object has hostgroups defined via "hostgroups" attribute
			2) This object inherits hostgroups attribute from a parent
			3) A hostgroup names this object via members attribute
			4) A hostgroup names another hostgroup via hostgroup_members attribute
			5) A hostgroup inherits (via use) from a hostgroup who names this host
		"""
		# TODO: Need error handling when object defines hostgroups but hostgroup does not exist
		result = []
		parent_results = []
		hostgroup_list = []
		# Case 1:
		if self.has_key('hostgroups'):
			grp = self['hostgroups']
			grp = grp.split(',')
			for i in grp:
				i = i.strip('+')
				print self['hostgroups']
				i = Hostgroup.objects.filter(hostgroup_name=i)[0]
				if not i in result: result.append(i)
		# Case 2:
		if not self.has_key('hostgroups') or self['hostgroups'].startswith('+'):
			parents = self.get_effective_parents()
			for parent in parents:
				parent_results += parent.get_effective_hostgroups()
		
		# Case 3:
		if self.has_key('host_name'):
			host_name = self['host_name']
			# We will use hostgroup_list in case 4 and 5 as well
			hostgroup_list = Hostgroup.objects.filter(members__is_a_field=self['host_name'])
			for hg in hostgroup_list:
					if hg not in result:
						result.append( hg )
		# Case 4:	
		for hg in hostgroup_list:
			if not hg.has_key('hostgroup_name'): continue
			grp = Hostgroup.objects.filter(hostgroup_members__is_a_field=hg['hostgroup_name'])
			for i in grp:
				if i not in result:
					result.append(i )
		# Case 5:
		for hg in hostgroup_list:
			if not hg.has_key('hostgroup_name'): continue
			grp = Hostgroup.objects.filter(use__is_a_field=hg['hostgroup_name'])
			for i in grp:
				if i not in result:
					result.append(i )
		return result
		
	def get_attribute_tuple(self):
		""" Returns all relevant attributes in the form of:
		
		(attribute_name,defined_value,inherited_value)
		"""
		result = []
		for k in self.keys():
			inher = defin = None 
			if self._inherited_attributes.has_key(k):
				inher = self._inherited_attributes[k]
			if self._defined_attributes.has_key(k):
				defin = self._defined_attributes[k]
			result.append((k, defin, inher))
		return result
		
class Host(ObjectDefinition):
	object_type = 'host'
	objects = ObjectFetcher('host')
	def get_description(self):
		""" Returns a friendly description of the object """
		return self['host_name']
class Service(ObjectDefinition):
	object_type = 'service'
	objects = ObjectFetcher('service')
	def get_description(self):
		""" Returns a friendly description of the object """
		return "%s/%s" % (self['host_name'], self['service_description'])
class Command(ObjectDefinition):
	object_type = 'command'
	objects = ObjectFetcher('command')
	def get_description(self):
		""" Returns a friendly description of the object """
		return self['command_name']
class Contact(ObjectDefinition):
	object_type = 'contact'
	objects = ObjectFetcher('contact')
	def get_description(self):
		""" Returns a friendly description of the object """
		return self['contact_name']	
class Contactgroup(ObjectDefinition):
	object_type = 'contactgroup'
	objects = ObjectFetcher('contactgroup')
	def get_description(self):
		""" Returns a friendly description of the object """
		return self['contactgroup_name']
class Hostgroup(ObjectDefinition):
	object_type = 'hostgroup'
	objects = ObjectFetcher('hostgroup')
	def get_description(self):
		""" Returns a friendly description of the object """
		return self['hostgroup_name']
class Servicegroup(ObjectDefinition):
	object_type = 'servicegroup'
	objects = ObjectFetcher('servicegroup')
	def get_description(self):
		""" Returns a friendly description of the object """
		return self['servicegroup_name']
class Timeperiod(ObjectDefinition):
	object_type = 'timeperiod'
	objects = ObjectFetcher('timeperiod')
	def get_description(self):
		""" Returns a friendly description of the object """
		return self['timeperiod_name']
'''
def Property(func):
	return property(**func())
class:
	@Property
	def service_description():
		doc = "The service_description of this object (if it has any)"
		def fget(self):
			if self.data.has_key('service_description'):
				return self.data['service_description']
		def fset(self, value):
			self.data['service_description'] = value
		return locals()
	def __strs__(self):
		return "%-30s %-30s %-30s" % (str(self['name']), str(self['host_name']), str(self['service_description']))

'''

string_to_class = {}
string_to_class['contact'] = Contact
string_to_class['service'] = Service
string_to_class['host'] = Host
string_to_class['hostgroup'] = Hostgroup
string_to_class['contactgroup'] = Contactgroup
string_to_class['servicegroup'] = Servicegroup
string_to_class['timeperiod'] = Timeperiod
string_to_class['command'] = Command
string_to_class[None] = ObjectDefinition

if __name__ == '__main__':
	starttime = time.time()
	#services = Service.objects.all
	#pall_sigurdsson_services = Service.objects.filter(host_name='pall.sigurdsson.is')
	#icelandic_services = Service.objects.filter(host_name__endswith='.is')
	#endtime = time.time()
	#duration=endtime-starttime
	#print "Converted (%s) config objects to ObjectDefinitions in %s seconds" % (len(services), duration)
	#host = Host.objects.filter(host_name='pall.sigurdsson.is')[0]
	#host['alias'] = 'pall.sigurdsson.is'
	#print host['alias']
	#print host.save()
	#o = ObjectDefinition('contact')
	host = Host.objects.all[0]
	#print host.__str__().__hash__()
	#print host.get_attribute_tuple()
	#print host.keys()
	#print host.has_key('name')
	#c = Contact.objects.filter(name="generic-contact")
	#for i in c:
	#	print i['name']
	#print c
	#3675388337418840039
	
	#host = ObjectDefinition.objects.filter(object_type="contact")
	#print len(host), "hosts found"
	#print len(host)
	#print host[0]['object_type']
	#print host.__str__().__hash__()
	#host['hash'] = host.__hash__
	hosts = Service.objects.filter(host_name=None,register="1")
	for i in hosts:
		print i['host_name'],i['name']
	print len(hosts)

def _test_get_by_id():
	'Do a quick unit test of the ObjectDefinition.get_by_id'
	hosts = Host.objects.all
	for h in hosts:
		id = h.get_id()
		h2 = Host.objects.get_by_id(id)
		if h.get_id() != h2.get_id():
			return False
	return True
	