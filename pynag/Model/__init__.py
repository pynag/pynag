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
print my_servce.host_name

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



def contains(str1,str2):
	'Returns True if str1 contains str2'
	if str1.find(str2) > -1: return True

def not_contains(str1,str2):
	'Returns True if str1 does not contain str2'
	return not contains(str1,str2)

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
			if not config.data.has_key( key_name ):
				return []
			objects = config.data[ key_name ]
		else:
			for k,v in config.data.items():
				objects += v
		for i in objects:
			i = ObjectDefinition( item=i  )
			self.objects.append( i )
		return self.objects
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
		result = []
		for i in self.all:
			object_matches = True
			for k,v in kwargs.items():
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
				elif k.endswith('__notcontains'):
					k = k[:-13]
					match_function = not_contains
				else:
					match_function = str.__eq__
				if v == None and not i.has_key( k ):
					continue
				if not i.has_key( k ):
					object_matches=False
					break
				if not match_function(i[k], v):
					object_matches=False
					break
			if object_matches:
				result.append( i )
		return result		


class ObjectDefinition(object):
	'''
	Holds one instance of one particular Object definition
	Example usage:
		objects = ObjectDefinition.objects.all
		my_object ObjectDefinition( dict ) # dict = hash map of configuration attributes
	'''
	object_type = None
	objects = ObjectFetcher( None )
	def __init__(self, item):
		self.object_type = item['meta']['object_type']
		self.objects = ObjectFetcher( self.object_type )
		self.data = item
		for k,v in self.data.items():
			self.__setattr__(k,v)
	def __setitem__(self, key, item):
		self.data[key] = item
	def __getitem__(self, key):
		if not self.data.has_key(key): return None
		return self.data[key]
	def has_key(self, key_name):
		return self.data.has_key(key_name)
	def keys(self):
		return self.data.keys()
	def save(self):
		"""Saves any changes to the current object to its configuration file
		
		Returns:
			True if save was successful.
		"""
		# TODO: We need to keep a log whenever someone makes changes to this object.
		# Then call config.edit_object()
		raise NotImplementedError()
		
	def __str__(self):
		return_buffer = "define %s {\n" % (self.object_type)
		fields = self.data.keys()
		fields.sort()
		interesting_fields = ['service_description','use','name','host_name']
		for i in interesting_fields:
			if i in fields:
				fields.remove(i)
				fields.insert(0, i)
			
		for key in fields:
			if key == 'meta': continue
			value = self.data[key]
			return_buffer = return_buffer + "\t%s = %s\n" %(key,value)
		return_buffer = return_buffer + "}\n\n"
		return return_buffer
	def __repr__(self):
		result=""
		result += "%s: " % self.__class__.__name__
		for i in  ['host_name','name','use','service_description']:
			if self.data.has_key(i):
				result += " %s=%s " % (i,self.data[i])
			else:
				result += "%s=None " % (i)
		return result
		
class Host(ObjectDefinition):
	object_type = 'host'
	objects = ObjectFetcher( 'host' )
class Service(ObjectDefinition):
	object_type = 'service'
	objects = ObjectFetcher( 'service' )
class Command(ObjectDefinition):
	object_type = 'command'
	objects = ObjectFetcher( 'command' )
class Contact(ObjectDefinition):
	object_type = 'contact'
	objects = ObjectFetcher( 'contact' )
class Contactgroup(ObjectDefinition):
	object_type = 'contactgroup'
	objects = ObjectFetcher( 'contactgroup' )
class Hostgroup(ObjectDefinition):
	object_type = 'hostgroup'
	objects = ObjectFetcher( 'hostgroup' )
class Servicegroup(ObjectDefinition):
	object_type = 'servicegroup'
	objects = ObjectFetcher( 'servicegroup' )
class Timeperiod(ObjectDefinition):
	object_type = 'timeperiod'
	objects = ObjectFetcher( 'timeperiod' )

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


if __name__ == '__main__':
	starttime = time.time()
	services = Service.objects.all
	pall_sigurdsson_services = Service.objects.filter(host_name='pall.sigurdsson.is')
	icelandic_services = Service.objects.filter(host_name__endswith='.is')
	endtime = time.time()
	duration=endtime-starttime
	print "Converted (%s) config objects to ObjectDefinitions in %s seconds" % (len(services), duration)
	
	
