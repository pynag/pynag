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
__version__ = "0.1"
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

		if not os.path.isfile(self.cfg_file):
			sys.stderr.write("%s does not exist\n" % self.cfg_file)
			return None

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

	def _exists(self, type, key, value):
		"""
		Check if an item exists
		"""
		for item in self.data['all_%s' % type ]:
			if item.has_key(key):
				if item[key] == value:
					return True
		return None

	def add_alias_to_hostgroup(self, alias, hostgroup_name):
		"""
		Add a host to a group
		"""
		if not self._exists('host','alias',alias):
			sys.stderr.write("Host alias '%s' does not exist\n" % alias)
			return None

		## Find the hostgroup from our global dictionaries
		target_group = self._get_hostgroup(hostgroup_name)
		if not target_group:
			print "%s does not exist" % hostgroup_name
			return None

		## Get a list of the aliases in this group
		existing_list = target_group['members'].split(",")
		if alias in existing_list:
			sys.stderr.write("%s is already in the group %s\n" % (alias, hostgroup_name))
			return None
		else:
			existing_list.append(alias)

		## Alphabetize the list, for easier readability
		existing_list.sort()

		## Remove old group
		self.data['all_hostgroup'].remove(target_group)

		## Save the new member list
		target_group['members'] = ",".join(existing_list)

		## Mark the commit flag for the group
		target_group['meta']['needs_commit'] = True

		## Add the group back in with new members
		self.data['all_hostgroup'].append(target_group)

	def commit(self):
		"""
		Write any changes that have been made to it's appropriate file
		"""
		## Loops through ALL items
		for k in self.data.keys():
			for item in self[k]:

				## If the object needs committing, commit it!
				if item['meta']['needs_commit']:
					file_contents = ""
					## find any other items that may share this config file
					extra_items = self._get_items_in_file(item['meta']['filename'])
					if len(extra_items) > 0:
						for commit_item in extra_items:
							## Make sure we aren't adding this thing twice
							if item != commit_item:
								file_contents += self.print_conf(commit_item)
					file_contents += self.print_conf(item)

					## Write the file
					f = open(item['meta']['filename'], 'w')
					f.write(file_contents)
					f.close()

					## Recreate the item entry without the commit flag
					self.data[k].remove(item)
					item['meta']['needs_commit'] = None
					self.data[k].append(item)

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

	def _get_hostgroup(self,hostgroup_name):
		for hostgroup in self.data['all_hostgroup']:
			if hostgroup['hostgroup_name'] == hostgroup_name:
				return hostgroup
		return None


	def print_objects(self, show_templates = None):

		for object in self.post_object_list:
			if object.has_key('register'):
				if not show_templates and ( object['register'] == "0"):
					continue
			for k,v in object.iteritems():
				print "%s : %s" % (k, v)
			print 

	def print_conf(self, item):
		import time
		output = ""
		output += "# Configuration file %s\n" % item['meta']['filename']
		output += "# Edited by PyNag on %s\n" % time.ctime()
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

	def _has_template(self, target):
		"""
		Determine if an item has a template associated with it
		"""
		if target.has_key('use'):
			return True
		else:
			return None

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

				#current_definition(key, value)
				current[key] = value
			## Something is wrong in the config
			else:
				sys.stderr.write("Error: Unexpected token in file '%s'" % filename)
				sys.exit(2)

		## Something is wrong in the config
		if in_definition:
			sys.stderr.write("Error: Unexpected EOF in file '%s'" % filename)
			sys.exit(2)

	def __setitem__(self, key, item):
		self.data[key] = item

	def __getitem__(self, key):
   		return self.data[key]
