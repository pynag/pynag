# -*- coding: utf-8 -*-

class NObject:

	def __init__(self, type=None):
		self.req_attributes = None
		self.filename = None
		self.definition_type = type

		## Define self dictionary
		self.data = {}
		self.data['is_template'] = None

	def set_filename(self, filename):
		self.filename = 'filename'

	def get_type(self):
		return self.definition_type

	def __getitem__(self,key):
		return self.data[key]

	def __setitem__(self,key, value):
		self.data[key] = value

	def set_service(self):

		self.req_attributes = [
			{'name':'host_name'},
			{'name':'hostgroup_name'},
			{'name':'service_description'},
			{'name':'display_name'},
			{'name':'servicegroups'},
			{'name':'is_volatile'},
			{'name':'check_command'},
			{'name':'initial_state'},
			{'name':'max_check_attempts'},
			{'name':'check_interval'},
			{'name':'retry_interval'},
			{'name':'active_checks_enabled'},
			{'name':'passive_checks_enabled'},
			{'name':'check_period'},
			{'name':'obsess_over_service'},
			{'name':'check_freshness'},
			{'name':'freshness_threshhold'},
			{'name':'event_handler'},
			{'name':'event_handler_enabled'},
			{'name':'low_flap_threshhold'},
			{'name':'high_flap_threshhold'},
			{'name':'flap_detection_enabled'},
			{'name':'flap_detection_options'},
			{'name':'process_perf_data'},
			{'name':'retain_status_information'},
			{'name':'retain_nonstatus_information'},
			{'name':'notification_interval'},
			{'name':'first_notification_delay'},
			{'name':'notification_period'},
			{'name':'notification_options'},
			{'name':'notifications_enabled'},
			{'name':'contacts'},
			{'name':'contact_groups'},
			{'name':'stalking_options'},
			{'name':'notes'},
			{'name':'notes_url'},
			{'name':'action_url'},
			{'name':'icon_image'},
			{'name':'icon_image_alt'},
		]

	def print_all(self):
		for key,value in self.data.iteritems():
			print "%s = %s" % (key, value)

	def print_all2(self):
		print self.data
