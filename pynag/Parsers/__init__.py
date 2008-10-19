#!/usr/bin/python
import sys
import os
import re
from optparse import OptionParser
from pynag.NObject import *

"""
Python Nagios extensions
"""

__author__ = "Drew Stinnett"
__copyright__ = "Copyright 2008, Drew Stinnett"
__credits__ = ["Drew Stinnett"]
__license__ = "GPL"
__version__ = "0.2"
__maintainer__ = "Drew Stinnett"
__email__ = "drew@drewlink.com"
__status__ = "Development"

class config:
	"""
	Parse and write nagios config files
	"""
	def __init__(self, cfg_file = "/etc/nagios/nagios.cfg"):

		self.cfg_file = cfg_file
		self.cfg_files = []
		self.data = {}

		## This is a pure listof all the key/values in the config files.  It
		## shouldn't be useful until the items in it are parsed through with the proper
		## 'use' relationships
		self.pre_object_list = []
		self.post_object_list = []
		self.object_type_keys = {
			'hostgroup':'hostgroup_name',
			'hostextinfo':'host_name',
			'host':'host_name',
			'service':'name',
			'servicegroup':'servicegroup_name',
			'contact':'contact_name',
			'contactgroup':'contactgroup_name',
			'timeperiod':'timeperiod_name',
			'command':'command_name',
			#'service':['host_name','description'],
		}

		if not os.path.isfile(self.cfg_file):
			sys.stderr.write("%s does not exist\n" % self.cfg_file)
			return None

	def _has_template(self, target):
		"""
		Determine if an item has a template associated with it
		"""
		if target.has_key('use'):
			return True
		else:
			return None

	def _get_key(self, object_type, user_key = None):
		"""
		Return the correct 'key' for an item.  This is mainly a helper method
		for other methods in this class.  It is used to shorten code repitition
		"""
		if not user_key and not self.object_type_keys.has_key(object_type):
			sys.stderr.write("Unknown key for object type:  %s\n" % object_type)
			sys.exit(2)

		## Use a default key
		if not user_key:
			user_key = self.object_type_keys[object_type]

		return user_key

	def _get_item(self, item_name, item_type, item_list):
   		""" 
   		Return an item from a list
   		"""
		for test_item in item_list:  
			## Skip tems without a name
			if not test_item.has_key('name'):
				continue

			## Make sure there isn't an infinite loop going on
			try:
				if (test_item['name'] == item_name) and (test_item['meta']['object_type'] == item_type):
					return test_item
			except:
				print "Loop detected, exiting"
				sys.exit(2)

		## If we make it this far, it means there is no matching item
		return None

	def _apply_template(self, original_item, template_item, complete_list):
		"""
		Apply the new item 'template_item' to 'original_item'
		"""

		if original_item.has_key('use'):
			new_item_to_add = self._get_item(original_item['use'], template_item['meta']['object_type'], complete_list)
			template_item = self._apply_template(template_item, new_item_to_add, complete_list)

		for k,v in template_item.iteritems():

			## Apply another template if this is a 'use' key
			if k == 'use':
				continue
				#new_item_to_add = self._get_item(v, template_item['meta']['object_type'], complete_list)
				#return self._apply_template(template_item, new_item_to_add, complete_list)

			## Ignore 'register' values
			if k == 'register':
				continue

			## Ignore 'meta' values
			if k == 'meta':
				continue

			## Apply any unknown value
			if not original_item.has_key(k):
				original_item[k] = v
				original_item['meta']['template_fields'].append(k)

		return original_item

	def _get_items_in_file(self, filename):
		"""
		Return all items in the given file
		"""
		return_list = []
				
		for k in self.data.keys():
			for item in self[k]:
				if item['meta']['filename'] == filename:
					return_list.append(item)
		return return_list

	## Removing this in favor of the more accessable get_hostgroup method
	#def _get_hostgroup(self,hostgroup_name):
		#for hostgroup in self.data['all_hostgroup']:
			#if hostgroup['hostgroup_name'] == hostgroup_name:
				#return hostgroup
		#return None

	def _load_file(self, filename):
		## Set globals (This is stolen from the perl module)
		append = ""
		type = None
		current = None
		in_definition = {}

		for line in open(filename, 'rb').readlines():

			## Cleanup and line skips
			line = line.strip()
			if line == "":
				continue
			if line[0] == "#":
				continue

			# append saved text to the current line
			if append:
				append += ' '
				line = append . line;
				append = None

			# end of object definition
			if line.find("}") != -1:

				in_definition = None
				append = line.split("}", 1)[1]

				self.pre_object_list.append(current)


				## Destroy the Nagios Object
				current = None
				continue

			# beginning of object definition
			boo_re = re.compile("define\s+(\w+)\s*{?(.*)$")
			m = boo_re.search(line)
			if m:
				object_type = m.groups()[0]
				#current = NObject(object_type, filename)
				current = {}
				current['meta'] = {}
				current['meta']['object_type'] = object_type
				current['meta']['filename'] = filename
				current['meta']['template_fields'] = []
				current['meta']['needs_commit'] = None
				current['meta']['delete_me'] = None

				if in_definition:
					sys.stderr.write("Error: Unexpected start of object definition in file '%s' on line $line_no.  Make sure you close preceding objects before starting a new one.\n" % filename)
					sys.exit(2)

				## Start off an object
				in_definition = True
				append = m.groups()[1]
				continue

			## save whatever's left in the buffer for the next iteration
			if not in_definition:
				append = line
				continue

			## this is an attribute inside an object definition
			if in_definition:
				(key, value) = line.split(None, 1)

				## Strip out in-line comments
				if value.find(";") != -1:
					value = value.split(";", 1)[0]

				## Clean info
				key = key.strip()
				value = value.strip()

				## Rename some old values that may be in the configuration
				## This can probably be removed in the future to increase performance
				if (current['meta']['object_type'] == 'service') and key == 'description':
					key = 'service_description'

				current[key] = value
			## Something is wrong in the config
			else:
				sys.stderr.write("Error: Unexpected token in file '%s'" % filename)
				sys.exit(2)

		## Something is wrong in the config
		if in_definition:
			sys.stderr.write("Error: Unexpected EOF in file '%s'" % filename)
			sys.exit(2)

	def edit_object(self, object_type, object_name, field, new_value, user_key = None):
		"""
		Edit an object's attributes

		Example:
		To change the alias of 'server01' to "Primary Server", use the following method

		edit_object('host','server01', 'alias','Primary Server')
		"""
		object_key = self._get_key(object_type,user_key)

		original_object = self.get_object(object_type, object_name, user_key = None)
		self['all_%s' % object_type].remove(original_object)
		original_object[field] = new_value
		original_object['meta']['needs_commit'] = True
		self['all_%s' % object_type].append(original_object)
		self.commit()
		return True

	def _get_list(self, object, key):
		"""
		Return a comma list from an item

		Example:

		_get_list(Foo_object, host_name)
		define service {
			service_description Foo
			host_name			larry,curly,moe
		}

		return
		['larry','curly','moe']
		"""
		if not object.has_key(key):
			return None

		return_list = []

		if object[key].find(",") != -1:
			for name in object[key].split(","):
				return_list.append(name)
		else:
			return_list.append(object[key])

		return return_list
		
	def delete_object(self, object_type, object_name, user_key = None):
		"""
		Delete object from configuration files.
		"""
		object_key = self._get_key(object_type,user_key)

		target_object = None
		k = 'all_%s' % object_type
		for item in self.data[k]:
			if not item.has_key(object_key):
				continue

			## If the object matches, mark it for deletion
			if item[object_key] == object_name:
				self.data[k].remove(item)
				item['meta']['delete_me'] = True
				item['meta']['needs_commit'] = True
				self.data[k].append(item)

				## Commit the delete
				self.commit()
				return True

		## Only make it here if the object isn't found
		return None

	def delete_host(self, object_name, user_key = None):
		"""
		Delete a host
		"""
		return self.delete_object('host',object_name, user_key = user_key)

	def get_object(self, object_type, object_name, user_key = None):
		"""
		Return a complete object dictionary
		"""
		object_key = self._get_key(object_type,user_key)

		target_object = None

		for item in self.data['all_%s' % object_type]:
			## Skip items without the specified key
			if not item.has_key(object_key):
				continue
			if item[object_key] == object_name:
				target_object = item
			## This is for multi-key items
		return target_object

	def get_host(self, object_name, user_key = None):
		"""
		Return a host object
		"""
		return self.get_object('host',object_name, user_key = user_key)

	def get_servicegroup(self, object_name, user_key = None):
		"""
		Return a Servicegroup object
		"""
		return self.get_object('servicegroup',object_name, user_key = user_key)

	def get_contact(self, object_name, user_key = None):
		"""
		Return a Contact object
		"""
		return self.get_object('contact',object_name, user_key = user_key)

	def get_contactgroup(self, object_name, user_key = None):
		"""
		Return a Contactgroup object
		"""
		return self.get_object('contactgroup',object_name, user_key = user_key)

	def get_timeperiod(self, object_name, user_key = None):
		"""
		Return a Timeperiod object
		"""
		return self.get_object('timeperiod',object_name, user_key = user_key)

	def get_command(self, object_name, user_key = None):
		"""
		Return a Command object
		"""
		return self.get_object('command',object_name, user_key = user_key)

	def get_hostgroup(self, object_name, user_key = None):
		"""
		Return a hostgroup object
		"""
		return self.get_object('hostgroup',object_name, user_key = user_key)

	def get_service(self, target_host, service_description):
		"""
		Return a service object.  This has to be seperate from the 'get_object'
		method, because it requires more than one key
		"""
		for item in self.data['all_service']:
			## Skip non-matching services
			if item['service_description'] != service_description:
				continue

			all_hosts = self.get_service_members(service_description, key='service_description', search_key='host_name')
			if self.host_in_service(target_host, item):
				return item
		return None

	def host_in_service(self, target_host, target_service):
		"""
		Return True if the host is in the given service

		Example:
		define service {
			service_description	Foo
			host_name			larry,curly
		}

		host_in_service("larry", %service_object%)
		returns True

		host_in_service("moe", %service_object%)
		returns None
		"""
		## Negation lists
		negate_hosts = []
		if target_service.has_key('host_name'):
			for host in self._get_list(target_service, 'host_name'):
				## If the host starts with a bang, add it to the negation list
				if host[:1] == "!":
					negate_hosts.append(host[1:])

		## Check in hostgroup_name
		if target_service.has_key('hostgroup_name'):
			hostgroups = self._get_list(self.get_hostgroup(target_service['hostgroup_name']), 'hostgroup_name')
			for hostgroup in hostgroups:
				if (target_host in self._get_list(self.get_hostgroup(hostgroup), 'members')) and (target_host not in negate_hosts):
					return True

		## Check in host_name
		if target_service.has_key('host_name'):
			if target_host in self._get_list(target_service, 'host_name'):
				return True
		return None
		

	def get_hostgroup_membership(self, name, user_key = None):
		"""
		Given a host_name, return all hostgroups that the host is a member of.
		"""
		hostgroup_list = []
		for item in self.data['all_hostgroup']:
			if item['members'].find(",") != -1:
				if name in item['members'].split(","):
					hostgroup_list.append(item['hostgroup_name'])
			elif item['members'] == name:
				hostgroup_list.append(item['members'])
		return hostgroup_list

	def get_service_membership(self, name, key='host_name'):
		"""
		Return all services a host belongs to
		"""
		service_list = []
		for item in self.data['all_service']:
			## Skip items that don't even have this key
			if not item.has_key(key):
				continue

			if item[key].find(",") != -1:
				if name in item[key].split(","):
					service_list.append(item)

			## If the the item is the only one in the list
			elif item[key] == name:
				service_list.append(item)

		return service_list

	def get_service_members(self, name, key='name', search_key='host_name'):
		"""
		Return a list of members for a specific service
		"""
		member_list = []
		for item in self.data['all_service']:
			## Skip items that don't even have this key
			if not item.has_key(search_key):
				continue

			if name == item[key]:
				if item[search_key].find(",") != -1:
					member_list.extend(item[search_key].split(","))
				else:
					member_list.append(item[search_key])

		return member_list

	def _append_use(self, source_item, name):
		"""
		Append any unused values from 'name' to the dict 'item'
		"""
		## Remove the 'use' key
		if source_item.has_key('use'):
			del source_item['use']
		
		for possible_item in self.pre_object_list:
			if possible_item.has_key('name'):
				## Start appending to the item
				for k,v in possible_item.iteritems():

					try:
						if k == 'use':
							source_item = self._append_use(source_item, v)
					except:
						print "Recursion error on %s %s" % (source_item, v)
						sys.exit(2)

					## Only add the item if it doesn't already exist
					if not source_item.has_key(k):
						source_item[k] = v
		return source_item

	def _post_parse(self):
		for raw_item in self.pre_object_list:
			if raw_item.has_key('use'):
				item_to_add = self._get_item(raw_item['use'], raw_item['meta']['object_type'], self.pre_object_list)
				raw_item = self._apply_template(raw_item,item_to_add, self.pre_object_list)
			self.post_object_list.append(raw_item)

		## Add the items to the class lists.  
		for list_item in self.post_object_list:
			type_list_name = "all_%s" % list_item['meta']['object_type']
			if not self.data.has_key(type_list_name):
				self.data[type_list_name] = []

			is_template = None
			if list_item.has_key('register'):
				if list_item['register'] == '0':
					is_template = True
			if not is_template:
				self.data[type_list_name].append(list_item)

	def commit(self):
		"""
		Write any changes that have been made to it's appropriate file
		"""
		## Loops through ALL items
		for k in self.data.keys():
			for item in self[k]:

				## If the object needs committing, commit it!
				if item['meta']['needs_commit']:
					## Create file contents as an empty string
					file_contents = ""

					## find any other items that may share this config file
					extra_items = self._get_items_in_file(item['meta']['filename'])
					if len(extra_items) > 0:
						for commit_item in extra_items:
							## Ignore files that are already set to be deleted:w
							if commit_item['meta']['delete_me']:
								continue
							## Make sure we aren't adding this thing twice
							if item != commit_item:
								file_contents += self.print_conf(commit_item)

					## This is the actual item that needs commiting
					if not item['meta']['delete_me']:
						file_contents += self.print_conf(item)

					## Write the file
					f = open(item['meta']['filename'], 'w')
					f.write(file_contents)
					f.close()

					## Recreate the item entry without the commit flag
					self.data[k].remove(item)
					item['meta']['needs_commit'] = None
					self.data[k].append(item)

	def flag_all_commit(self):
		"""
		Flag every item in the configuration to be committed
		This should probably only be used for debugging purposes
		"""
		new_data_list = {}
		for k in self.data.keys():
			new_data_list[k] = []
			for item in self[k]:
				item['meta']['needs_commit'] = True
				new_data_list[k].append(item)

		## Replace the original list with the new one
		self.data = new_data_list

	def print_conf(self, item):
		"""
		Return a string that can be used in a configuration file
		"""
		import time
		output = ""
		## Header, to go on all files
		output += "# Configuration file %s\n" % item['meta']['filename']
		output += "# Edited by PyNag on %s\n" % time.ctime()

		## Some hostgroup information
		if item['meta'].has_key('hostgroup_list'):
			output += "# Hostgroups: %s\n" % ",".join(item['meta']['hostgroup_list'])

		if len(item['meta']['template_fields']) != 0:
			output += "# Values from templates:\n"
		for k in item['meta']['template_fields']:
			output += "#\t %-30s %-30s\n" % (k, item[k])
		output += "\n"
		output += "define %s {\n" % item['meta']['object_type']
		for k, v in item.iteritems():
			if k != 'meta':
				if k not in item['meta']['template_fields']:
					output += "\t %-30s %-30s\n" % (k,v)
		
		output += "}\n\n"
		return output



	def parse(self):
		"""
		Load the nagios.cfg file and parse it up
		"""
		for line in open(self.cfg_file).readlines():
			## Strip out new line characters
			line = line.strip()

			## Skip blank lines
			if line == "":
				continue

			## Skip comments
			if line[0] == "#":
				continue

			## Now get the actual objects and values
			(config_object, config_value) = line.split("=", 1)

			## Add cfg_file objects to cfg file list
			if config_object == "cfg_file" and os.path.isfile(config_value):
					self.cfg_files.append(config_value)

			## Parse all files in a cfg directory
			if config_object == "cfg_dir":
				raw_file_list = os.listdir(config_value)
				for raw_file in raw_file_list:
					if raw_file[-4:] == ".cfg":
						filename = "%s" % (os.path.join(config_value, raw_file.strip()))
						if os.path.exists(filename):
							self.cfg_files.append(filename)

		## This loads everything into
		for cfg_file in self.cfg_files:
			self._load_file(cfg_file)

		self._post_parse()

	def extended_parse(self):
		"""
		This parse is used after the initial parse() command is run.  It is
		only needed if you want extended meta information about hosts or other objects
		"""
		## First, cycle through the hosts, and append hostgroup information
		index = 0
		for host in self.data['all_host']:
			if not self.data['all_host'][index]['meta'].has_key('hostgroup_list'):
				self.data['all_host'][index]['meta']['hostgroup_list'] = []

			## Append any hostgroups that are directly listed in the host definition
			if host.has_key('hostgroups'):
				for hostgroup_name in self._get_list(host, 'hostgroups'):
					if not self.data['all_host'][index]['meta'].has_key('hostgroup_list'):
						self.data['all_host'][index]['meta']['hostgroup_list'] = []
					if hostgroup_name not in self.data['all_host'][index]['meta']['hostgroup_list']:
						self.data['all_host'][index]['meta']['hostgroup_list'].append(hostgroup_name)

			## Increment count
			index += 1

		## Loop through all hostgroups, appending them to their respective hosts
		for hostgroup in self.data['all_hostgroup']:

			for member in self._get_list(hostgroup,'members'):
				index = 0
				for host in self.data['all_host']:

					## Skip members that do not match
					if host['host_name'] == member:

						## Create the meta var if it doesn' exist
						if not self.data['all_host'][index]['meta'].has_key('hostgroup_list'):
							self.data['all_host'][index]['meta']['hostgroup_list'] = []

						if hostgroup['hostgroup_name'] not in self.data['all_host'][index]['meta']['hostgroup_list']:
							self.data['all_host'][index]['meta']['hostgroup_list'].append(hostgroup['hostgroup_name'])

					## Increment count
					index += 1

	def get_cfg_files(self):
		"""
		Return a list of all cfg files used in this configuration

		Example:
		print get_cfg_files()
		['/etc/nagios/hosts/host1.cfg','/etc/nagios/hosts/host2.cfg',...]
		"""
		return self.cfg_files

	def __setitem__(self, key, item):
		self.data[key] = item

	def __getitem__(self, key):
   		return self.data[key]
