# These are gathered from Nagios Object Definition documentation (Version 3.2.3)

object_definitions = {}
object_definitions["any"] = {}
object_definitions["any"]["use"] = { "name":"use", "required":"optional", "value":"use" }
object_definitions["any"]["register"] = { "name":"register", "required":"optional", "value":"register" }
object_definitions["any"]["name"] = { "name":"name", "required":"optional", "value":"name" }
object_definitions["host"] = {}
object_definitions["host"]["host_name"] = { "name":"host_name", "required":"required", "value":"host_name" }
object_definitions["host"]["alias"] = { "name":"alias", "required":"required", "value":"alias" }
object_definitions["host"]["display_name"] = { "name":"display_name", "required":"optional", "value":"display_name" }
object_definitions["host"]["address"] = { "name":"address", "required":"required", "value":"address" }
object_definitions["host"]["parents"] = { "name":"parents", "required":"optional", "value":"host_names" }
object_definitions["host"]["hostgroups"] = { "name":"hostgroups", "required":"optional", "value":"hostgroup_names" }
object_definitions["host"]["check_command"] = { "name":"check_command", "required":"optional", "value":"command_name" }
object_definitions["host"]["initial_state"] = { "name":"initial_state", "required":"optional", "value":"[o,d,u]" }
object_definitions["host"]["max_check_attempts"] = { "name":"max_check_attempts", "required":"required", "value":"#" }
object_definitions["host"]["check_interval"] = { "name":"check_interval", "required":"optional", "value":"#" }
object_definitions["host"]["retry_interval"] = { "name":"retry_interval", "required":"optional", "value":"#" }
object_definitions["host"]["active_checks_enabled"] = { "name":"active_checks_enabled", "required":"optional", "value":"[0/1]" }
object_definitions["host"]["passive_checks_enabled"] = { "name":"passive_checks_enabled", "required":"optional", "value":"[0/1]" }
object_definitions["host"]["check_period"] = { "name":"check_period", "required":"required", "value":"timeperiod_name" }
object_definitions["host"]["obsess_over_host"] = { "name":"obsess_over_host", "required":"optional", "value":"[0/1]" }
object_definitions["host"]["check_freshness"] = { "name":"check_freshness", "required":"optional", "value":"[0/1]" }
object_definitions["host"]["freshness_threshold"] = { "name":"freshness_threshold", "required":"optional", "value":"#" }
object_definitions["host"]["event_handler"] = { "name":"event_handler", "required":"optional", "value":"command_name" }
object_definitions["host"]["event_handler_enabled"] = { "name":"event_handler_enabled", "required":"optional", "value":"[0/1]" }
object_definitions["host"]["low_flap_threshold"] = { "name":"low_flap_threshold", "required":"optional", "value":"#" }
object_definitions["host"]["high_flap_threshold"] = { "name":"high_flap_threshold", "required":"optional", "value":"#" }
object_definitions["host"]["flap_detection_enabled"] = { "name":"flap_detection_enabled", "required":"optional", "value":"[0/1]" }
object_definitions["host"]["flap_detection_options"] = { "name":"flap_detection_options", "required":"optional", "value":"[o,d,u]" }
object_definitions["host"]["process_perf_data"] = { "name":"process_perf_data", "required":"optional", "value":"[0/1]" }
object_definitions["host"]["retain_status_information"] = { "name":"retain_status_information", "required":"optional", "value":"[0/1]" }
object_definitions["host"]["retain_nonstatus_information"] = { "name":"retain_nonstatus_information", "required":"optional", "value":"[0/1]" }
object_definitions["host"]["contacts"] = { "name":"contacts", "required":"required", "value":"contacts" }
object_definitions["host"]["contact_groups"] = { "name":"contact_groups", "required":"required", "value":"contact_groups" }
object_definitions["host"]["notification_interval"] = { "name":"notification_interval", "required":"required", "value":"#" }
object_definitions["host"]["first_notification_delay"] = { "name":"first_notification_delay", "required":"optional", "value":"#" }
object_definitions["host"]["notification_period"] = { "name":"notification_period", "required":"required", "value":"timeperiod_name" }
object_definitions["host"]["notification_options"] = { "name":"notification_options", "required":"optional", "value":"[d,u,r,f,s]" }
object_definitions["host"]["notifications_enabled"] = { "name":"notifications_enabled", "required":"optional", "value":"[0/1]" }
object_definitions["host"]["stalking_options"] = { "name":"stalking_options", "required":"optional", "value":"[o,d,u]" }
object_definitions["host"]["notes"] = { "name":"notes", "required":"optional", "value":"note_string" }
object_definitions["host"]["notes_url"] = { "name":"notes_url", "required":"optional", "value":"url" }
object_definitions["host"]["action_url"] = { "name":"action_url", "required":"optional", "value":"url" }
object_definitions["host"]["icon_image"] = { "name":"icon_image", "required":"optional", "value":"image_file" }
object_definitions["host"]["icon_image_alt"] = { "name":"icon_image_alt", "required":"optional", "value":"alt_string" }
object_definitions["host"]["vrml_image"] = { "name":"vrml_image", "required":"optional", "value":"image_file" }
object_definitions["host"]["statusmap_image"] = { "name":"statusmap_image", "required":"optional", "value":"image_file" }
object_definitions["host"]["2d_coords"] = { "name":"2d_coords", "required":"optional", "value":"x_coord,y_coord" }
object_definitions["host"]["3d_coords"] = { "name":"3d_coords", "required":"optional", "value":"x_coord,y_coord,z_coord" }
object_definitions["hostgroup"] = {}
object_definitions["hostgroup"]["hostgroup_name"] = { "name":"hostgroup_name", "required":"required", "value":"hostgroup_name" }
object_definitions["hostgroup"]["alias"] = { "name":"alias", "required":"required", "value":"alias" }
object_definitions["hostgroup"]["members"] = { "name":"members", "required":"optional", "value":"hosts" }
object_definitions["hostgroup"]["hostgroup_members"] = { "name":"hostgroup_members", "required":"optional", "value":"hostgroups" }
object_definitions["hostgroup"]["notes"] = { "name":"notes", "required":"optional", "value":"note_string" }
object_definitions["hostgroup"]["notes_url"] = { "name":"notes_url", "required":"optional", "value":"url" }
object_definitions["hostgroup"]["action_url"] = { "name":"action_url", "required":"optional", "value":"url" }
object_definitions["service"] = {}
object_definitions["service"]["host_name"] = { "name":"host_name", "required":"required", "value":"host_name" }
object_definitions["service"]["hostgroup_name"] = { "name":"hostgroup_name", "required":"optional", "value":"hostgroup_name" }
object_definitions["service"]["service_description"] = { "name":"service_description", "required":"required", "value":"service_description" }
object_definitions["service"]["display_name"] = { "name":"display_name", "required":"optional", "value":"display_name" }
object_definitions["service"]["servicegroups"] = { "name":"servicegroups", "required":"optional", "value":"servicegroup_names" }
object_definitions["service"]["is_volatile"] = { "name":"is_volatile", "required":"optional", "value":"[0/1]" }
object_definitions["service"]["check_command"] = { "name":"check_command", "required":"required", "value":"command_name" }
object_definitions["service"]["initial_state"] = { "name":"initial_state", "required":"optional", "value":"[o,w,u,c]" }
object_definitions["service"]["max_check_attempts"] = { "name":"max_check_attempts", "required":"required", "value":"#" }
object_definitions["service"]["check_interval"] = { "name":"check_interval", "required":"required", "value":"#" }
object_definitions["service"]["retry_interval"] = { "name":"retry_interval", "required":"required", "value":"#" }
object_definitions["service"]["active_checks_enabled"] = { "name":"active_checks_enabled", "required":"optional", "value":"[0/1]" }
object_definitions["service"]["passive_checks_enabled"] = { "name":"passive_checks_enabled", "required":"optional", "value":"[0/1]" }
object_definitions["service"]["check_period"] = { "name":"check_period", "required":"required", "value":"timeperiod_name" }
object_definitions["service"]["obsess_over_service"] = { "name":"obsess_over_service", "required":"optional", "value":"[0/1]" }
object_definitions["service"]["check_freshness"] = { "name":"check_freshness", "required":"optional", "value":"[0/1]" }
object_definitions["service"]["freshness_threshold"] = { "name":"freshness_threshold", "required":"optional", "value":"#" }
object_definitions["service"]["event_handler"] = { "name":"event_handler", "required":"optional", "value":"command_name" }
object_definitions["service"]["event_handler_enabled"] = { "name":"event_handler_enabled", "required":"optional", "value":"[0/1]" }
object_definitions["service"]["low_flap_threshold"] = { "name":"low_flap_threshold", "required":"optional", "value":"#" }
object_definitions["service"]["high_flap_threshold"] = { "name":"high_flap_threshold", "required":"optional", "value":"#" }
object_definitions["service"]["flap_detection_enabled"] = { "name":"flap_detection_enabled", "required":"optional", "value":"[0/1]" }
object_definitions["service"]["flap_detection_options"] = { "name":"flap_detection_options", "required":"optional", "value":"[o,w,c,u]" }
object_definitions["service"]["process_perf_data"] = { "name":"process_perf_data", "required":"optional", "value":"[0/1]" }
object_definitions["service"]["retain_status_information"] = { "name":"retain_status_information", "required":"optional", "value":"[0/1]" }
object_definitions["service"]["retain_nonstatus_information"] = { "name":"retain_nonstatus_information", "required":"optional", "value":"[0/1]" }
object_definitions["service"]["notification_interval"] = { "name":"notification_interval", "required":"required", "value":"#" }
object_definitions["service"]["first_notification_delay"] = { "name":"first_notification_delay", "required":"optional", "value":"#" }
object_definitions["service"]["notification_period"] = { "name":"notification_period", "required":"required", "value":"timeperiod_name" }
object_definitions["service"]["notification_options"] = { "name":"notification_options", "required":"optional", "value":"[w,u,c,r,f,s]" }
object_definitions["service"]["notifications_enabled"] = { "name":"notifications_enabled", "required":"optional", "value":"[0/1]" }
object_definitions["service"]["contacts"] = { "name":"contacts", "required":"required", "value":"contacts" }
object_definitions["service"]["contact_groups"] = { "name":"contact_groups", "required":"required", "value":"contact_groups" }
object_definitions["service"]["stalking_options"] = { "name":"stalking_options", "required":"optional", "value":"[o,w,u,c]" }
object_definitions["service"]["notes"] = { "name":"notes", "required":"optional", "value":"note_string" }
object_definitions["service"]["notes_url"] = { "name":"notes_url", "required":"optional", "value":"url" }
object_definitions["service"]["action_url"] = { "name":"action_url", "required":"optional", "value":"url" }
object_definitions["service"]["icon_image"] = { "name":"icon_image", "required":"optional", "value":"image_file" }
object_definitions["service"]["icon_image_alt"] = { "name":"icon_image_alt", "required":"optional", "value":"alt_string" }
object_definitions["servicegroup"] = {}
object_definitions["servicegroup"]["servicegroup_name"] = { "name":"servicegroup_name", "required":"required", "value":"servicegroup_name" }
object_definitions["servicegroup"]["alias"] = { "name":"alias", "required":"required", "value":"alias" }
object_definitions["servicegroup"]["members"] = { "name":"members", "required":"optional", "value":"services" }
object_definitions["servicegroup"]["servicegroup_members"] = { "name":"servicegroup_members", "required":"optional", "value":"servicegroups" }
object_definitions["servicegroup"]["notes"] = { "name":"notes", "required":"optional", "value":"note_string" }
object_definitions["servicegroup"]["notes_url"] = { "name":"notes_url", "required":"optional", "value":"url" }
object_definitions["servicegroup"]["action_url"] = { "name":"action_url", "required":"optional", "value":"url" }
object_definitions["contact"] = {}
object_definitions["contact"]["contact_name"] = { "name":"contact_name", "required":"required", "value":"contact_name" }
object_definitions["contact"]["alias"] = { "name":"alias", "required":"optional", "value":"alias" }
object_definitions["contact"]["contactgroups"] = { "name":"contactgroups", "required":"optional", "value":"contactgroup_names" }
object_definitions["contact"]["host_notifications_enabled"] = { "name":"host_notifications_enabled", "required":"required", "value":"[0/1]" }
object_definitions["contact"]["service_notifications_enabled"] = { "name":"service_notifications_enabled", "required":"required", "value":"[0/1]" }
object_definitions["contact"]["host_notification_period"] = { "name":"host_notification_period", "required":"required", "value":"timeperiod_name" }
object_definitions["contact"]["service_notification_period"] = { "name":"service_notification_period", "required":"required", "value":"timeperiod_name" }
object_definitions["contact"]["host_notification_options"] = { "name":"host_notification_options", "required":"required", "value":"[d,u,r,f,s,n]" }
object_definitions["contact"]["service_notification_options"] = { "name":"service_notification_options", "required":"required", "value":"[w,u,c,r,f,s,n]" }
object_definitions["contact"]["host_notification_commands"] = { "name":"host_notification_commands", "required":"required", "value":"command_name" }
object_definitions["contact"]["service_notification_commands"] = { "name":"service_notification_commands", "required":"required", "value":"command_name" }
object_definitions["contact"]["email"] = { "name":"email", "required":"optional", "value":"email_address" }
object_definitions["contact"]["pager"] = { "name":"pager", "required":"optional", "value":"pager_number or pager_email_gateway" }
object_definitions["contact"]["address"] = { "name":"address", "required":"optional", "value":"additional_contact_address" }
object_definitions["contact"]["can_submit_commands"] = { "name":"can_submit_commands", "required":"optional", "value":"[0/1]" }
object_definitions["contact"]["retain_status_information"] = { "name":"retain_status_information", "required":"optional", "value":"[0/1]" }
object_definitions["contact"]["retain_nonstatus_information"] = { "name":"retain_nonstatus_information", "required":"optional", "value":"[0/1]" }
object_definitions["contactgroup"] = {}
object_definitions["contactgroup"]["contactgroup_name"] = { "name":"contactgroup_name", "required":"required", "value":"contactgroup_name" }
object_definitions["contactgroup"]["alias"] = { "name":"alias", "required":"required", "value":"alias" }
object_definitions["contactgroup"]["members"] = { "name":"members", "required":"optional", "value":"contacts" }
object_definitions["contactgroup"]["contactgroup_members"] = { "name":"contactgroup_members", "required":"optional", "value":"contactgroups" }
object_definitions["timeperiod"] = {}
object_definitions["timeperiod"]["timeperiod_name"] = { "name":"timeperiod_name", "required":"required", "value":"timeperiod_name" }
object_definitions["timeperiod"]["alias"] = { "name":"alias", "required":"required", "value":"alias" }
object_definitions["timeperiod"]["[weekday]"] = { "name":"[weekday]", "required":"optional", "value":"timeranges" }
object_definitions["timeperiod"]["[exception]"] = { "name":"[exception]", "required":"optional", "value":"timeranges" }
object_definitions["timeperiod"]["exclude"] = { "name":"exclude", "required":"optional", "value":"]" }
object_definitions["command"] = {}
object_definitions["command"]["command_name"] = { "name":"command_name", "required":"required", "value":"command_name" }
object_definitions["command"]["command_line"] = { "name":"command_line", "required":"required", "value":"command_line" }
object_definitions["servicedependency"] = {}
object_definitions["servicedependency"]["dependent_host_name"] = { "name":"dependent_host_name", "required":"required", "value":"host_name" }
object_definitions["servicedependency"]["dependent_hostgroup_name"] = { "name":"dependent_hostgroup_name", "required":"optional", "value":"hostgroup_name" }
object_definitions["servicedependency"]["dependent_service_description"] = { "name":"dependent_service_description", "required":"required", "value":"service_description" }
object_definitions["servicedependency"]["host_name"] = { "name":"host_name", "required":"required", "value":"host_name" }
object_definitions["servicedependency"]["hostgroup_name"] = { "name":"hostgroup_name", "required":"optional", "value":"hostgroup_name" }
object_definitions["servicedependency"]["service_description"] = { "name":"service_description", "required":"required", "value":"service_description" }
object_definitions["servicedependency"]["inherits_parent"] = { "name":"inherits_parent", "required":"optional", "value":"[0/1]" }
object_definitions["servicedependency"]["execution_failure_criteria"] = { "name":"execution_failure_criteria", "required":"optional", "value":"[o,w,u,c,p,n]" }
object_definitions["servicedependency"]["notification_failure_criteria"] = { "name":"notification_failure_criteria", "required":"optional", "value":"[o,w,u,c,p,n]" }
object_definitions["servicedependency"]["dependency_period"] = { "name":"dependency_period", "required":"optional", "value":"timeperiod_name" }
object_definitions["serviceescalation"] = {}
object_definitions["serviceescalation"]["host_name"] = { "name":"host_name", "required":"required", "value":"host_name" }
object_definitions["serviceescalation"]["hostgroup_name"] = { "name":"hostgroup_name", "required":"optional", "value":"hostgroup_name" }
object_definitions["serviceescalation"]["service_description"] = { "name":"service_description", "required":"required", "value":"service_description" }
object_definitions["serviceescalation"]["contacts"] = { "name":"contacts", "required":"required", "value":"contacts" }
object_definitions["serviceescalation"]["contact_groups"] = { "name":"contact_groups", "required":"required", "value":"contactgroup_name" }
object_definitions["serviceescalation"]["first_notification"] = { "name":"first_notification", "required":"required", "value":"#" }
object_definitions["serviceescalation"]["last_notification"] = { "name":"last_notification", "required":"required", "value":"#" }
object_definitions["serviceescalation"]["notification_interval"] = { "name":"notification_interval", "required":"required", "value":"#" }
object_definitions["serviceescalation"]["escalation_period"] = { "name":"escalation_period", "required":"optional", "value":"timeperiod_name" }
object_definitions["serviceescalation"]["escalation_options"] = { "name":"escalation_options", "required":"optional", "value":"[w,u,c,r]" }
object_definitions["hostdependency"] = {}
object_definitions["hostdependency"]["dependent_host_name"] = { "name":"dependent_host_name", "required":"required", "value":"host_name" }
object_definitions["hostdependency"]["dependent_hostgroup_name"] = { "name":"dependent_hostgroup_name", "required":"optional", "value":"hostgroup_name" }
object_definitions["hostdependency"]["host_name"] = { "name":"host_name", "required":"required", "value":"host_name" }
object_definitions["hostdependency"]["hostgroup_name"] = { "name":"hostgroup_name", "required":"optional", "value":"hostgroup_name" }
object_definitions["hostdependency"]["inherits_parent"] = { "name":"inherits_parent", "required":"optional", "value":"[0/1]" }
object_definitions["hostdependency"]["execution_failure_criteria"] = { "name":"execution_failure_criteria", "required":"optional", "value":"[o,d,u,p,n]" }
object_definitions["hostdependency"]["notification_failure_criteria"] = { "name":"notification_failure_criteria", "required":"optional", "value":"[o,d,u,p,n]" }
object_definitions["hostdependency"]["dependency_period"] = { "name":"dependency_period", "required":"optional", "value":"timeperiod_name" }
object_definitions["hostescalation"] = {}
object_definitions["hostescalation"]["host_name"] = { "name":"host_name", "required":"required", "value":"host_name" }
object_definitions["hostescalation"]["hostgroup_name"] = { "name":"hostgroup_name", "required":"optional", "value":"hostgroup_name" }
object_definitions["hostescalation"]["contacts"] = { "name":"contacts", "required":"required", "value":"contacts" }
object_definitions["hostescalation"]["contact_groups"] = { "name":"contact_groups", "required":"required", "value":"contactgroup_name" }
object_definitions["hostescalation"]["first_notification"] = { "name":"first_notification", "required":"required", "value":"#" }
object_definitions["hostescalation"]["last_notification"] = { "name":"last_notification", "required":"required", "value":"#" }
object_definitions["hostescalation"]["notification_interval"] = { "name":"notification_interval", "required":"required", "value":"#" }
object_definitions["hostescalation"]["escalation_period"] = { "name":"escalation_period", "required":"optional", "value":"timeperiod_name" }
object_definitions["hostescalation"]["escalation_options"] = { "name":"escalation_options", "required":"optional", "value":"[d,u,r]" }
object_definitions["hostextinfo"] = {}
object_definitions["hostextinfo"]["host_name"] = { "name":"host_name", "required":"required", "value":"host_name" }
object_definitions["hostextinfo"]["notes"] = { "name":"notes", "required":"optional", "value":"note_string" }
object_definitions["hostextinfo"]["notes_url"] = { "name":"notes_url", "required":"optional", "value":"url" }
object_definitions["hostextinfo"]["action_url"] = { "name":"action_url", "required":"optional", "value":"url" }
object_definitions["hostextinfo"]["icon_image"] = { "name":"icon_image", "required":"optional", "value":"image_file" }
object_definitions["hostextinfo"]["icon_image_alt"] = { "name":"icon_image_alt", "required":"optional", "value":"alt_string" }
object_definitions["hostextinfo"]["vrml_image"] = { "name":"vrml_image", "required":"optional", "value":"image_file" }
object_definitions["hostextinfo"]["statusmap_image"] = { "name":"statusmap_image", "required":"optional", "value":"image_file" }
object_definitions["hostextinfo"]["2d_coords"] = { "name":"2d_coords", "required":"optional", "value":"x_coord,y_coord" }
object_definitions["hostextinfo"]["3d_coords"] = { "name":"3d_coords", "required":"optional", "value":"x_coord,y_coord,z_coord" }
object_definitions["serviceextinfo"] = {}
object_definitions["serviceextinfo"]["host_name"] = { "name":"host_name", "required":"required", "value":"host_name" }
object_definitions["serviceextinfo"]["service_description"] = { "name":"service_description", "required":"required", "value":"service_description" }
object_definitions["serviceextinfo"]["notes"] = { "name":"notes", "required":"optional", "value":"note_string" }
object_definitions["serviceextinfo"]["notes_url"] = { "name":"notes_url", "required":"optional", "value":"url" }
object_definitions["serviceextinfo"]["action_url"] = { "name":"action_url", "required":"optional", "value":"url" }
object_definitions["serviceextinfo"]["icon_image"] = { "name":"icon_image", "required":"optional", "value":"image_file" }
object_definitions["serviceextinfo"]["icon_image_alt"] = { "name":"icon_image_alt", "required":"optional", "value":"alt_string" }
# Generated via examples/Model/parse-configmain.py
main_config = {'accept_passive_host_checks': {'doc': 'This option determines whether or not Nagios will accept <a href="passivechecks.html">passive host checks</a> when it initially (re)starts.  If this option is disabled, Nagios will not accept any passive host checks.  Note: If you have <a href="#retain_state_information">state retention</a> enabled, Nagios will ignore this setting when it (re)starts and use the last known setting for this option (as stored in the <a href="#state_retention_file">state retention file</a>), <i>unless</i> you disable the <a href="#use_retained_program_state">use_retained_program_state</a> option.  If you want to change this option when state retention is active (and the <a href="#use_retained_program_state">use_retained_program_state</a> is enabled), you\'ll have to use the appropriate <a href="extcommands.html">external command</a> or change it via the web interface.  Values are as follows: ',
                                'examples': ['accept_passive_host_checks=1'],
                                'format': 'accept_passive_host_checks=&lt;0/1&gt;',
                                'options': ["0 = Don't accept passive host checks",
                                            '1 = Accept passive host checks (default)'],
                                'title': 'Passive Host Check Acceptance Option'},
 'accept_passive_service_checks': {'doc': 'This option determines whether or not Nagios will accept <a href="passivechecks.html">passive service checks</a> when it initially (re)starts.  If this option is disabled, Nagios will not accept any passive service checks.  Note: If you have <a href="#retain_state_information">state retention</a> enabled, Nagios will ignore this setting when it (re)starts and use the last known setting for this option (as stored in the <a href="#state_retention_file">state retention file</a>), <i>unless</i> you disable the <a href="#use_retained_program_state">use_retained_program_state</a> option.  If you want to change this option when state retention is active (and the <a href="#use_retained_program_state">use_retained_program_state</a> is enabled), you\'ll have to use the appropriate <a href="extcommands.html">external command</a> or change it via the web interface.  Values are as follows: ',
                                   'examples': ['accept_passive_service_checks=1'],
                                   'format': 'accept_passive_service_checks=&lt;0/1&gt;',
                                   'options': ["0 = Don't accept passive service checks",
                                               '1 = Accept passive service checks (default)'],
                                   'title': 'Passive Service Check Acceptance Option'},
 'additional_freshness_latency': {'doc': 'This option determines the number of seconds Nagios will add to any host or services freshness threshold it automatically calculates (e.g. those not specified explicity by the user).  More information on freshness checking can be found <a href="freshness.html">here</a>. ',
                                  'examples': ['additional_freshness_latency=15'],
                                  'format': 'additional_freshness_latency=&lt;#&gt;',
                                  'options': [],
                                  'title': 'Additional Freshness Threshold Latency Option'},
 'admin_email': {'doc': 'This is the email address for the administrator of the local machine (i.e. the one that Nagios is running on). This value can be used in notification commands by using the <b>$ADMINEMAIL$</b> <a href="macros.html">macro</a>. ',
                 'examples': ['admin_email=root@localhost.localdomain'],
                 'format': 'admin_email=&lt;email_address&gt;',
                 'options': [],
                 'title': 'Administrator Email Address'},
 'admin_pager': {'doc': 'This is the pager number (or pager email gateway) for the administrator of the local machine (i.e. the one that Nagios is running on). The pager number/address can be used in notification commands by using the <b>$ADMINPAGER$</b> <a href="macros.html">macro</a>. ',
                 'examples': ['admin_pager=pageroot@localhost.localdomain'],
                 'format': 'admin_pager=&lt;pager_number_or_pager_email_gateway&gt;',
                 'options': [],
                 'title': 'Administrator Pager'},
 'auto_reschedule_checks': {'doc': 'This option determines whether or not Nagios will attempt to automatically reschedule active host and service checks to  "smooth" them out over time.  This can help to balance the load on the monitoring server, as it will attempt to keep the time between consecutive checks consistent, at the expense of executing checks on a more rigid schedule. <strong>WARNING:</strong>  THIS IS AN EXPERIMENTAL FEATURE AND MAY BE REMOVED IN FUTURE VERSIONS.  ENABLING THIS OPTION CAN DEGRADE PERFORMANCE - RATHER THAN INCREASE IT - IF USED IMPROPERLY! ',
                            'examples': ['auto_reschedule_checks=1'],
                            'format': 'auto_reschedule_checks=&lt;0/1&gt;',
                            'options': [],
                            'title': 'Auto-Rescheduling Option'},
 'auto_rescheduling_interval': {'doc': 'This option determines how often (in seconds) Nagios will attempt to automatically reschedule checks.  This option only has an effect if the <a href="#auto_reschedule_checks">auto_reschedule_checks</a> option is enabled.  Default is 30 seconds. <strong>WARNING:</strong>  THIS IS AN EXPERIMENTAL FEATURE AND MAY BE REMOVED IN FUTURE VERSIONS.  ENABLING THE AUTO-RESCHEDULING OPTION CAN DEGRADE PERFORMANCE - RATHER THAN INCREASE IT - IF USED IMPROPERLY! ',
                                'examples': ['auto_rescheduling_interval=30'],
                                'format': 'auto_rescheduling_interval=&lt;seconds&gt;',
                                'options': [],
                                'title': 'Auto-Rescheduling Interval'},
 'auto_rescheduling_window': {'doc': 'This option determines the "window" of time (in seconds) that Nagios will look at when automatically rescheduling checks. Only host and service checks that occur in the next X seconds (determined by this variable) will be rescheduled.  This option only has an effect if the <a href="#auto_reschedule_checks">auto_reschedule_checks</a> option is enabled.  Default is 180 seconds (3 minutes). <strong>WARNING:</strong>  THIS IS AN EXPERIMENTAL FEATURE AND MAY BE REMOVED IN FUTURE VERSIONS.  ENABLING THE AUTO-RESCHEDULING OPTION CAN DEGRADE PERFORMANCE - RATHER THAN INCREASE IT - IF USED IMPROPERLY! ',
                              'examples': ['auto_rescheduling_window=180'],
                              'format': 'auto_rescheduling_window=&lt;seconds&gt;',
                              'options': [],
                              'title': 'Auto-Rescheduling Window'},
 'bare_update_checks': {'doc': 'This option deterines what data Nagios will send to api.nagios.org when it checks for updates.  By default, Nagios will send information on the current version of Nagios you have installed, as well as an indicator as to whether this was a new installation or not.  Nagios Enterprises uses this data to determine the number of users running specific version of Nagios.  Enable this option if you do not wish for this information to be sent. ',
                        'examples': ['bare_update_checks'],
                        'format': 'bare_update_checks=&lt;0/1&gt;',
                        'options': [],
                        'title': 'Bare Update Checks'},
 'broker_module': {'doc': 'This directive is used to specify an event broker module that should by loaded by Nagios at startup.  Use multiple directives if you want to load more than one module.  Arguments that should be passed to the module at startup are seperated from the module path by a space. !!! WARNING !!! Do NOT overwrite modules while they are being used by Nagios or Nagios will crash in a fiery display of SEGFAULT glory.  This is a bug/limitation either in dlopen(), the kernel, and/or the filesystem.  And maybe Nagios... The correct/safe way of updating a module is by using one of these methods: ',
                   'examples': ['broker_module=/usr/local/nagios/bin/ndomod.o cfg_file=/usr/local/nagios/etc/ndomod.cfg'],
                   'format': 'broker_module=&lt;modulepath&gt; [moduleargs]',
                   'options': ['Shutdown Nagios, replace the module file, restart Nagios</li>',
                               'While Nagios is running... delete the original module file, move the new module file into place, restart Nagios</li>'],
                   'title': 'Event Broker Modules'},
 'cached_host_check_horizon': {'doc': 'This option determines the maximum amount of time (in seconds) that the state of a previous host check is considered current.  Cached host states (from host checks that were performed more recently than the time specified by this value) can improve host check performance immensely.  Too high of a value for this option may result in (temporarily) inaccurate host states, while a low value may result in a performance hit for host checks.  Use a value of 0 if you want to disable host check caching.  More information on cached checks can be found <a href="cachedchecks.html">here</a>. ',
                               'examples': ['cached_host_check_horizon=15'],
                               'format': 'cached_host_check_horizon=&lt;seconds&gt;',
                               'options': [],
                               'title': 'Cached Host Check Horizon'},
 'cached_service_check_horizon': {'doc': 'This option determines the maximum amount of time (in seconds) that the state of a previous service check is considered current.  Cached service states (from service checks that were performed more recently than the time specified by this value) can improve service check performance when a lot of <a href="objectdefinitions.html#servicedependency">service dependencies</a> are used.  Too high of a value for this option may result in inaccuracies in the service dependency logic.  Use a value of 0 if you want to disable service check caching.  More information on cached checks can be found <a href="cachedchecks.html">here</a>. ',
                                  'examples': ['cached_service_check_horizon=15'],
                                  'format': 'cached_service_check_horizon=&lt;seconds&gt;',
                                  'options': [],
                                  'title': 'Cached Service Check Horizon'},
 'cfg_dir': {'doc': 'This directive is used to specify a directory which contains <a href="configobject.html">object configuration files</a> that Nagios should use for monitoring.  All files in the directory with a <i>.cfg</i> extension are processed as object config files.  Additionally, Nagios will recursively process all config files in subdirectories of the directory you specify here.  You can seperate your configuration files into different directories and specify multiple <i>cfg_dir=</i> statements to have all config files in each directory processed. ',
             'examples': ['cfg_dir=/usr/local/nagios/etc/commands',
                          'cfg_dir=/usr/local/nagios/etc/services',
                          'cfg_dir=/usr/local/nagios/etc/hosts'],
             'format': 'cfg_dir=&lt;directory_name&gt;',
             'options': [],
             'title': 'Object Configuration Directory'},
 'cfg_file': {'doc': 'This directive is used to specify an <a href="configobject.html">object configuration file</a> containing object definitions that Nagios should use for monitoring.  Object configuration files contain definitions for hosts, host groups, contacts, contact groups, services, commands, etc.  You can seperate your configuration information into several files and specify multiple <i>cfg_file=</i> statements to have each of them processed. ',
              'examples': ['cfg_file=/usr/local/nagios/etc/hosts.cfg',
                           'cfg_file=/usr/local/nagios/etc/services.cfg',
                           'cfg_file=/usr/local/nagios/etc/commands.cfg'],
              'format': 'cfg_file=&lt;file_name&gt;',
              'options': [],
              'title': 'Object Configuration File'},
 'check_external_commands': {'doc': 'This option determines whether or not Nagios will check the <a href="#command_file">command file</a> for  commands that should be executed.  This option must be enabled if you plan on using the <a href="cgis.html#cmd_cgi">command CGI</a> to issue commands via the web interface. More information on external commands can be found <a href="extcommands.html">here</a>. ',
                             'examples': ['check_external_commands=1'],
                             'format': 'check_external_commands=&lt;0/1&gt;',
                             'options': ["0 = Don't check external commands",
                                         '1 = Check external commands (default)'],
                             'title': 'External Command Check Option'},
 'check_for_orphaned_hosts': {'doc': 'This option allows you to enable or disable checks for orphaned hoste checks. Orphaned host checks are checks which have been executed and have been removed from the event queue, but have not had any results reported in a long time.  Since no results have come back in for the host, it is not rescheduled in the event queue.  This can cause host checks to stop being executed.  Normally it is very rare for this to happen - it might happen if an external user or process killed off the process that was being used to execute a host check.  If this option is enabled and Nagios finds that results for a particular host check have not come back, it will log an error message and reschedule the host check.  If you start seeing host checks that never seem to get rescheduled, enable this option and see if you notice any log messages about orphaned hosts. ',
                              'examples': ['check_for_orphaned_hosts=1'],
                              'format': 'check_for_orphaned_hosts=&lt;0/1&gt;',
                              'options': ["0 = Don't check for orphaned host checks",
                                          '1 = Check for orphaned host checks (default)'],
                              'title': 'Orphaned Host Check Option'},
 'check_for_orphaned_services': {'doc': 'This option allows you to enable or disable checks for orphaned service checks. Orphaned service checks are checks which have been executed and have been removed from the event queue, but have not had any results reported in a long time.  Since no results have come back in for the service, it is not rescheduled in the event queue.  This can cause service checks to stop being executed.  Normally it is very rare for this to happen - it might happen if an external user or process killed off the process that was being used to execute a service check.  If this option is enabled and Nagios finds that results for a particular service check have not come back, it will log an error message and reschedule the service check.  If you start seeing service checks that never seem to get rescheduled, enable this option and see if you notice any log messages about orphaned services. ',
                                 'examples': ['check_for_orphaned_services=1'],
                                 'format': 'check_for_orphaned_services=&lt;0/1&gt;',
                                 'options': ["0 = Don't check for orphaned service checks",
                                             '1 = Check for orphaned service checks (default)'],
                                 'title': 'Orphaned Service Check Option'},
 'check_for_updates': {'doc': 'This option determines whether Nagios will automatically check to see if new updates (releases) are available.  It is recommend that you enable this option to ensure that you stay on top of the latest critical patches to Nagios.  Nagios is critical to you - make sure you keep it in good shape.  Nagios will check once a day for new updates. Data collected by Nagios Enterprises from the update check is processed in accordance  with our privacy policy - see <a href="http://api.nagios.org">http://api.nagios.org</a> for details. ',
                       'examples': ['check_for_updates=1'],
                       'format': 'check_for_updates=&lt;0/1&gt;',
                       'options': [],
                       'title': 'Update Checks'},
 'check_host_freshness': {'doc': 'This option determines whether or not Nagios will periodically check the "freshness" of host checks.  Enabling this option is useful for helping to ensure that <a href="passivechecks.html">passive host checks</a> are received in a timely manner.  More information on freshness checking can be found <a href="freshness.html">here</a>. ',
                          'examples': ['check_host_freshness=0'],
                          'format': 'check_host_freshness=&lt;0/1&gt;',
                          'options': ["0 = Don't check host freshness",
                                      '1 = Check host freshness (default)'],
                          'title': 'Host Freshness Checking Option'},
 'check_result_path': {'doc': 'This options determines which directory Nagios will use to temporarily store host and service check results before they are processed.  This directory should not be used to store any other files, as Nagios will periodically clean this directory of old file (see the <a href="#max_check_result_file_age">max_check_result_file_age</a> option for more information). Note: Make sure that only a single instance of Nagios has access to the check result path.  If multiple instances of Nagios have their check result path set to the same directory, you will run into problems with check results being processed (incorrectly) by the wrong instance of Nagios! ',
                       'examples': ['check_result_path=/var/spool/nagios/checkresults'],
                       'format': 'check_result_path=&lt;path&gt;',
                       'options': [],
                       'title': 'Check Result Path'},
 'check_result_reaper_frequency': {'doc': 'This option allows you to control the frequency <i>in seconds</i> of check result "reaper" events.  "Reaper" events process the results from host and service checks that have finished executing.  These events consitute the core of the monitoring logic in Nagios. ',
                                   'examples': ['check_result_reaper_frequency=5'],
                                   'format': 'check_result_reaper_frequency=&lt;frequency_in_seconds&gt;',
                                   'options': [],
                                   'title': 'Check Result Reaper Frequency'},
 'check_service_freshness': {'doc': 'This option determines whether or not Nagios will periodically check the "freshness" of service checks.  Enabling this option is useful for helping to ensure that <a href="passivechecks.html">passive service checks</a> are received in a timely manner.  More information on freshness checking can be found <a href="freshness.html">here</a>. ',
                             'examples': ['check_service_freshness=0'],
                             'format': 'check_service_freshness=&lt;0/1&gt;',
                             'options': ["0 = Don't check service freshness",
                                         '1 = Check service freshness (default)'],
                             'title': 'Service Freshness Checking Option'},
 'child_processes_fork_twice': {'doc': 'This option determines whether or not Nagios will fork() child processes twice when it executes host and service checks.  By default, Nagios fork()s twice.  However, if the <a href="#use_large_installation_tweaks">use_large_installation_tweaks</a> option is enabled, it will only fork() once.  By defining this option in your configuration file, you are able to override things to get the behavior you want. ',
                                'examples': ['child_processes_fork_twice=0'],
                                'format': 'child_processes_fork_twice=&lt;0/1&gt;',
                                'options': ['0 = Fork() just once',
                                            '1 = Fork() twice'],
                                'title': 'Child Processes Fork Twice'},
 'command_check_interval': {'doc': 'If you specify a number with an "s" appended to it (i.e. 30s), this is the number of <i>seconds</i> to wait between external command checks.  If you leave off the "s", this is the number of "time units" to wait between external command checks. Unless you\'ve changed the <a href="#interval_length">interval_length</a> value (as defined below) from the default value of 60, this number will mean minutes.   Note: By setting this value to <b>-1</b>, Nagios will check for external commands as often as possible.  Each time Nagios checks for external commands it will read and process all commands present in the <a href="#command_file">command file</a> before continuing on with its other duties.  More information on external commands can be found <a href="extcommands.html">here</a>. ',
                            'examples': ['command_check_interval=1'],
                            'format': 'command_check_interval=&lt;xxx&gt;[s]',
                            'options': [],
                            'title': 'External Command Check Interval'},
 'command_file': {'doc': 'This is the file that Nagios will check for external commands to process.  The <a href="cgis.html#cmd_cgi">command CGI</a> writes commands to this file.  The external command file is implemented as a named pipe (FIFO), which is created when Nagios starts and removed when it shuts down.  If the file exists when Nagios starts, the Nagios process will terminate with an error message.  More information on external commands can be found <a href="extcommands.html">here</a>. ',
                  'examples': ['command_file=/usr/local/nagios/var/rw/nagios.cmd'],
                  'format': 'command_file=&lt;file_name&gt;',
                  'options': [],
                  'title': 'External Command File'},
 'date_format': {'doc': 'This option allows you to specify what kind of date/time format Nagios should use in the web interface and date/time <a href="macros.html">macros</a>.  Possible options (along with example output) include: ',
                 'examples': ['date_format=us'],
                 'format': 'date_format=&lt;option&gt;',
                 'options': [],
                 'title': 'Date Format'},
 'debug_file': {'doc': 'This option determines where Nagios should write debugging information.  What (if any) information is written is determined by the <a href="#debug_level">debug_level</a> and <a href="#debug_verbosity">debug_verbosity</a> options.  You can have Nagios automaticaly rotate the debug file when it reaches a certain size by using the <a href="#max_debug_file_size">max_debug_file_size</a> option. ',
                'examples': ['debug_file=/usr/local/nagios/var/nagios.debug'],
                'format': 'debug_file=&lt;file_name&gt;',
                'options': [],
                'title': 'Debug File'},
 'debug_level': {'doc': 'This option determines what type of information Nagios should write to the <a href="#debug_file">debug_file</a>.  This value is a logical OR of the values below. ',
                 'examples': ['debug_level=24'],
                 'format': 'debug_level=&lt;#&gt;',
                 'options': ['-1 = Log everything',
                             '0 = Log nothing (default)',
                             '1 = Function enter/exit information',
                             '2 = Config information',
                             '4 = Process information',
                             '8 = Scheduled event information',
                             '16 = Host/service check information',
                             '32 = Notification information',
                             '64 = Event broker information'],
                 'title': 'Debug Level'},
 'debug_verbosity': {'doc': 'This option determines how much debugging information Nagios should write to the <a href="#debug_file">debug_file</a>. ',
                     'examples': ['debug_verbosity=1'],
                     'format': 'debug_verbosity=&lt;#&gt;',
                     'options': ['0 = Basic information',
                                 '1 = More detailed information (default)',
                                 '2 = Highly detailed information'],
                     'title': 'Debug Verbosity'},
 'enable_embedded_perl': {'doc': 'This setting determines whether or not the embedded Perl interpreter is enabled on a program-wide basis.  Nagios must be compiled with support for embedded Perl for this option to have an effect.  More information on the embedded Perl interpreter can be found <a href="embeddedperl.html">here</a>. ',
                          'examples': ['enable_embedded_perl=1'],
                          'format': 'enable_embedded_perl=&lt;0/1&gt;',
                          'options': [],
                          'title': 'Embedded Perl Interpreter Option'},
 'enable_environment_macros': {'doc': 'This option determines whether or not the Nagios daemon will make all standard <a href="macrolist.html">macros</a> available as environment variables to your check, notification, event hander, etc. commands.  In large Nagios installations this can be problematic because it takes additional memory and (more importantly) CPU to compute the values of all macros and make them available to the environment. ',
                               'examples': ['enable_environment_macros=0'],
                               'format': 'enable_environment_macros=&lt;0/1&gt;',
                               'options': ["0 = Don't make macros available as environment variables",
                                           '1 = Make macros available as environment variables (default)'],
                               'title': 'Environment Macros Option'},
 'enable_event_handlers': {'doc': 'This option determines whether or not Nagios will run <a href="eventhandlers.html">event handlers</a> when it initially (re)starts.  If this option is disabled, Nagios will not run any host or service event handlers.  Note: If you have <a href="#retain_state_information">state retention</a> enabled, Nagios will ignore this setting when it (re)starts and use the last known setting for this option (as stored in the <a href="#state_retention_file">state retention file</a>), <i>unless</i> you disable the <a href="#use_retained_program_state">use_retained_program_state</a> option.  If you want to change this option when state retention is active (and the <a href="#use_retained_program_state">use_retained_program_state</a> is enabled), you\'ll have to use the appropriate <a href="extcommands.html">external command</a> or change it via the web interface.  Values are as follows: ',
                           'examples': ['enable_event_handlers=1'],
                           'format': 'enable_event_handlers=&lt;0/1&gt;',
                           'options': ['0 = Disable event handlers',
                                       '1 = Enable event handlers (default)'],
                           'title': 'Event Handler Option'},
 'enable_flap_detection': {'doc': 'This option determines whether or not Nagios will try and detect hosts and services that are "flapping".  Flapping occurs when a host or service changes between states too frequently, resulting in a barrage of notifications being sent out.  When Nagios detects that a host or service is flapping, it will temporarily suppress notifications for that host/service until it stops flapping.  Flap detection is very experimental at this point, so use this feature with caution!  More information on how flap detection and handling works can be found <a href="flapping.html">here</a>.     Note: If you have <a href="#retain_state_information">state retention</a> enabled, Nagios will ignore this setting when it (re)starts and use the last known setting for this option (as stored in the <a href="#state_retention_file">state retention file</a>), <i>unless</i> you disable the <a href="#use_retained_program_state">use_retained_program_state</a> option.  If you want to change this option when state retention is active (and the <a href="#use_retained_program_state">use_retained_program_state</a> is enabled), you\'ll have to use the appropriate <a href="extcommands.html">external command</a> or change it via the web interface. ',
                           'examples': ['enable_flap_detection=0'],
                           'format': 'enable_flap_detection=&lt;0/1&gt;',
                           'options': ["0 = Don't enable flap detection (default)",
                                       '1 = Enable flap detection'],
                           'title': 'Flap Detection Option'},
 'enable_notifications': {'doc': 'This option determines whether or not Nagios will send out <a href="notifications.html">notifications</a> when it initially (re)starts.  If this option is disabled, Nagios will not send out notifications for any host or service.  Note: If you have <a href="#retain_state_information">state retention</a> enabled, Nagios will ignore this setting when it (re)starts and use the last known setting for this option (as stored in the <a href="#state_retention_file">state retention file</a>), <i>unless</i> you disable the <a href="#use_retained_program_state">use_retained_program_state</a> option.  If you want to change this option when state retention is active (and the <a href="#use_retained_program_state">use_retained_program_state</a> is enabled), you\'ll have to use the appropriate <a href="extcommands.html">external command</a> or change it via the web interface.  Values are as follows: ',
                          'examples': ['enable_notifications=1'],
                          'format': 'enable_notifications=&lt;0/1&gt;',
                          'options': ['0 = Disable notifications',
                                      '1 = Enable notifications (default)'],
                          'title': 'Notifications Option'},
 'enable_predictive_host_dependency_checks': {'doc': 'This option determines whether or not Nagios will execute predictive checks of hosts that are being depended upon (as defined in <a href="objectdefinitions.html#hostdependency">host dependencies</a>) for a particular host when it changes state.  Predictive checks help ensure that the dependency logic is as accurate as possible.  More information on how predictive checks work can be found <a href="dependencychecks.html">here</a>. ',
                                              'examples': ['enable_predictive_host_dependency_checks=1'],
                                              'format': 'enable_predictive_host_dependency_checks=&lt;0/1&gt;',
                                              'options': ['0 = Disable predictive checks',
                                                          '1 = Enable predictive checks (default)'],
                                              'title': 'Predictive Host Dependency Checks Option'},
 'enable_predictive_service_dependency_checks': {'doc': 'This option determines whether or not Nagios will execute predictive checks of services that are being depended upon (as defined in <a href="objectdefinitions.html#servicedependency">service dependencies</a>) for a particular service when it changes state.  Predictive checks help ensure that the dependency logic is as accurate as possible.  More information on how predictive checks work can be found <a href="dependencychecks.html">here</a>. ',
                                                 'examples': ['enable_predictive_service_dependency_checks=1'],
                                                 'format': 'enable_predictive_service_dependency_checks=&lt;0/1&gt;',
                                                 'options': ['0 = Disable predictive checks',
                                                             '1 = Enable predictive checks (default)'],
                                                 'title': 'Predictive Service Dependency Checks Option'},
 'event_broker_options': {'doc': 'This option controls what (if any) data gets sent to the event broker and, in turn, to any loaded event broker modules.   This is an advanced option.  When in doubt, either broker nothing (if not using event broker modules) or broker everything (if using event broker modules). Possible values are shown below. ',
                          'examples': ['event_broker_options=-1'],
                          'format': 'event_broker_options=&lt;#&gt;',
                          'options': ['0 = Broker nothing',
                                      '-1 = Broker everything',
                                      "# = See BROKER_* definitions in source code (include/broker.h) for other values that can be OR'ed together"],
                          'title': 'Event Broker Options'},
 'event_handler_timeout': {'doc': 'This is the maximum number of seconds that Nagios will allow <a href="eventhandlers.html">event handlers</a> to be run.  If an event handler exceeds this time limit it will be killed and a warning will be logged. There is often widespread confusion as to what this option really does.  It is meant to be used as a last ditch mechanism to kill off commands which are misbehaving and not exiting in a timely manner.  It should be set to something high (like 60 seconds or more), so that each event handler command normally finishes executing within this time limit.  If an event handler runs longer than this limit, Nagios will kill it off thinking it is a runaway processes. ',
                           'examples': ['event_handler_timeout=60'],
                           'format': 'event_handler_timeout=&lt;seconds&gt;',
                           'options': [],
                           'title': 'Event Handler Timeout'},
 'execute_host_checks': {'doc': 'This option determines whether or not Nagios will execute on-demand and regularly scheduled host checks when it initially (re)starts.  If this option is disabled, Nagios will not actively execute any host checks, although it can still accept <a href="passivechecks.html">passive host checks</a> unless you\'ve <a href="#accept_passive_host_checks">disabled them</a>).   This option is most often used when configuring backup monitoring servers, as described in the documentation on <a href="redundancy.html">redundancy</a>, or when setting up a <a href="distributed.html">distributed</a> monitoring environment.  Note: If you have <a href="#retain_state_information">state retention</a> enabled, Nagios will ignore this setting when it (re)starts and use the last known setting for this option (as stored in the <a href="#state_retention_file">state retention file</a>), <i>unless</i> you disable the <a href="#use_retained_program_state">use_retained_program_state</a> option.  If you want to change this option when state retention is active (and the <a href="#use_retained_program_state">use_retained_program_state</a> is enabled), you\'ll have to use the appropriate <a href="extcommands.html">external command</a> or change it via the web interface.  Values are as follows: ',
                         'examples': ['execute_host_checks=1'],
                         'format': 'execute_host_checks=&lt;0/1&gt;',
                         'options': ["0 = Don't execute host checks",
                                     '1 = Execute host checks (default)'],
                         'title': 'Host Check Execution Option'},
 'execute_service_checks': {'doc': 'This option determines whether or not Nagios will execute service checks when it initially (re)starts.  If this option is disabled, Nagios will not actively execute any service checks and will remain in a sort of "sleep" mode (it can still accept <a href="passivechecks.html">passive checks</a> unless you\'ve <a href="#accept_passive_service_checks">disabled them</a>).   This option is most often used when configuring backup monitoring servers, as described in the documentation on <a href="redundancy.html">redundancy</a>, or when setting up a <a href="distributed.html">distributed</a> monitoring environment.  Note: If you have <a href="#retain_state_information">state retention</a> enabled, Nagios will ignore this setting when it (re)starts and use the last known setting for this option (as stored in the <a href="#state_retention_file">state retention file</a>), <i>unless</i> you disable the <a href="#use_retained_program_state">use_retained_program_state</a> option.  If you want to change this option when state retention is active (and the <a href="#use_retained_program_state">use_retained_program_state</a> is enabled), you\'ll have to use the appropriate <a href="extcommands.html">external command</a> or change it via the web interface.  Values are as follows: ',
                            'examples': ['execute_service_checks=1'],
                            'format': 'execute_service_checks=&lt;0/1&gt;',
                            'options': ["0 = Don't execute service checks",
                                        '1 = Execute service checks (default)'],
                            'title': 'Service Check Execution Option'},
 'external_command_buffer_slots': {'doc': 'Note: This is an advanced feature. This option determines how many buffer slots Nagios will reserve for caching external commands that have been read from the external command file by a worker thread, but have not yet been processed by the main thread of the Nagios deamon.  Each slot can hold one external command, so this option essentially determines how many commands can be buffered.  For installations where you process a large number of passive checks (e.g. <a href="distributed.html">distributed setups</a>), you may need to increase this number.  You should consider using MRTG to graph Nagios\' usage of external command buffers.  You can read more on how to configure graphing <a href="mrtggraphs.html">here</a>. ',
                                   'examples': ['external_command_buffer_slots=512'],
                                   'format': 'external_command_buffer_slots=&lt;#&gt;',
                                   'options': [],
                                   'title': 'External Command Buffer Slots'},
 'free_child_process_memory': {'doc': 'This option determines whether or not Nagios will free memory in child processes when they are fork()ed off from the main process.  By default, Nagios frees memory.  However, if the <a href="#use_large_installation_tweaks">use_large_installation_tweaks</a> option is enabled, it will not.  By defining this option in your configuration file, you are able to override things to get the behavior you want. ',
                               'examples': ['free_child_process_memory=0'],
                               'format': 'free_child_process_memory=&lt;0/1&gt;',
                               'options': ["0 = Don't free memory",
                                           '1 = Free memory'],
                               'title': 'Child Process Memory Option'},
 'global_host_event_handler': {'doc': 'This option allows you to specify a host event handler command that is to be run for every host state change.  The global event handler is executed immediately prior to the event handler that you have optionally specified in each host definition.  The <i>command</i> argument is the short name of a command that you define in your <a href="configobject.html">object configuration file</a>.  The maximum amount of time that this command can run is controlled by the <a href="#event_handler_timeout">event_handler_timeout</a> option.  More information on event handlers can be found <a href="eventhandlers.html">here</a>. ',
                               'examples': ['global_host_event_handler=log-host-event-to-db'],
                               'format': 'global_host_event_handler=&lt;command&gt;',
                               'options': [],
                               'title': 'Global Host Event Handler Option'},
 'global_service_event_handler': {'doc': 'This option allows you to specify a service event handler command that is to be run for every service state change.  The global event handler is executed immediately prior to the event handler that you have optionally specified in each service definition.  The <i>command</i> argument is the short name of a command that you define in your <a href="configobject.html">object configuration file</a>.  The maximum amount of time that this command can run is controlled by the <a href="#event_handler_timeout">event_handler_timeout</a> option.  More information on event handlers can be found <a href="eventhandlers.html">here</a>. ',
                                  'examples': ['global_service_event_handler=log-service-event-to-db'],
                                  'format': 'global_service_event_handler=&lt;command&gt;',
                                  'options': [],
                                  'title': 'Global Service Event Handler Option'},
 'high_host_flap_threshold': {'doc': 'This option is used to set the high threshold for detection of host flapping.  For more information on how flap detection and handling works (and how this option affects things) read <a href="flapping.html">this</a>. ',
                              'examples': ['high_host_flap_threshold=50.0'],
                              'format': 'high_host_flap_threshold=&lt;percent&gt;',
                              'options': [],
                              'title': 'High Host Flap Threshold'},
 'high_service_flap_threshold': {'doc': 'This option is used to set the high threshold for detection of service flapping.  For more information on how flap detection and handling works (and how this option affects things) read <a href="flapping.html">this</a>. ',
                                 'examples': ['high_service_flap_threshold=50.0'],
                                 'format': 'high_service_flap_threshold=&lt;percent&gt;',
                                 'options': [],
                                 'title': 'High Service Flap Threshold'},
 'host_check_timeout': {'doc': 'This is the maximum number of seconds that Nagios will allow host checks to run.  If checks exceed this limit, they are killed and a CRITICAL state is returned and the host will be assumed to be DOWN.  A timeout error will also be logged. There is often widespread confusion as to what this option really does.  It is meant to be used as a last ditch mechanism to kill off plugins which are misbehaving and not exiting in a timely manner.  It should be set to something high (like 60 seconds or more), so that each host check normally finishes executing within this time limit.  If a host check runs longer than this limit, Nagios will kill it off thinking it is a runaway processes. ',
                        'examples': ['host_check_timeout=60'],
                        'format': 'host_check_timeout=&lt;seconds&gt;',
                        'options': [],
                        'title': 'Host Check Timeout'},
 'host_freshness_check_interval': {'doc': 'This setting determines how often (in seconds) Nagios will periodically check the "freshness" of host check results.  If you have disabled host freshness checking (with the <a href="#check_host_freshness">check_host_freshness</a> option), this option has no effect.  More information on freshness checking can be found <a href="freshness.html">here</a>. ',
                                   'examples': ['host_freshness_check_interval=60'],
                                   'format': 'host_freshness_check_interval=&lt;seconds&gt;',
                                   'options': [],
                                   'title': 'Host Freshness Check Interval'},
 'host_inter_check_delay_method': {'doc': 'This option allows you to control how host checks <i>that are scheduled to be checked on a regular basis</i> are initially "spread out" in the event queue.  Using a "smart" delay calculation (the default) will cause Nagios to calculate an average check interval and spread initial checks of all hosts out over that interval, thereby helping to eliminate CPU load spikes.  Using no delay is generally <i>not</i> recommended.  Using no delay will cause all host checks to be scheduled for execution at the same time.  More information on how to estimate how the inter-check delay affects host check scheduling can be found <a href="checkscheduling.html#host_inter_check_delay">here</a>.Values are as follows: ',
                                   'examples': ['host_inter_check_delay_method=s'],
                                   'format': 'host_inter_check_delay_method=&lt;n/d/s/x.xx&gt;',
                                   'options': ["n = Don't use any delay - schedule all host checks to run immediately (i.e. at the same time!)",
                                               'd = Use a "dumb" delay of 1 second between host checks',
                                               's = Use a "smart" delay calculation to spread host checks out evenly (default)',
                                               'x.xx = Use a user-supplied inter-check delay of x.xx seconds'],
                                   'title': 'Host Inter-Check Delay Method'},
 'host_perfdata_command': {'doc': 'This option allows you to specify a command to be run after <i>every</i> host check to process host <a href="perfdata.html">performance data</a> that may be returned from the check.  The <i>command</i> argument is the short name of a <a href="objectdefinitions.html#command">command definition</a> that you define in your object configuration file.  This command is only executed if the <a href="#process_performance_data">process_performance_data</a> option is enabled globally and if the <i>process_perf_data</i> directive in the <a href="objectdefinitions.html#host">host definition</a> is enabled. ',
                           'examples': ['host_perfdata_command=process-host-perfdata'],
                           'format': 'host_perfdata_command=&lt;command&gt;',
                           'options': [],
                           'title': 'Host Performance Data Processing Command'},
 'host_perfdata_file': {'doc': 'This option allows you to specify a file to which host <a href="perfdata.html">performance data</a> will be written after every host check.  Data will be written to the performance file as specified by the <a href="#host_perfdata_file_template">host_perfdata_file_template</a> option.  Performance data is only written to this file if the <a href="#process_performance_data">process_performance_data</a> option is enabled globally and if the <i>process_perf_data</i> directive in the <a href="objectdefinitions.html#host">host definition</a> is enabled. ',
                        'examples': ['host_perfdata_file=/usr/local/nagios/var/host-perfdata.dat'],
                        'format': 'host_perfdata_file=&lt;file_name&gt;',
                        'options': [],
                        'title': 'Host Performance Data File'},
 'host_perfdata_file_mode': {'doc': 'This option determines how the <a href="#host_perfdata_file">host performance data file</a> is opened.  Unless the file is a named pipe you\'ll probably want to use the default mode of append. ',
                             'examples': ['host_perfdata_file_mode=a'],
                             'format': 'host_perfdata_file_mode=&lt;mode&gt;',
                             'options': ['a = Open file in append mode (default)',
                                         'w = Open file in write mode',
                                         'p = Open in non-blocking read/write mode (useful when writing to pipes)'],
                             'title': 'Host Performance Data File Mode'},
 'host_perfdata_file_processing_command': {'doc': 'This option allows you to specify the command that should be executed to process the <a href="#host_perfdata_file">host performance data file</a>.  The <i>command</i> argument is the short name of a <a href="objectdefinitions.html#command">command definition</a> that you define in your object configuration file.  The interval at which this command is executed is determined by the <a href="#host_perfdata_file_processing_interval">host_perfdata_file_processing_interval</a> directive. ',
                                           'examples': ['host_perfdata_file_processing_command=process-host-perfdata-file'],
                                           'format': 'host_perfdata_file_processing_command=&lt;command&gt;',
                                           'options': [],
                                           'title': 'Host Performance Data File Processing Command'},
 'host_perfdata_file_processing_interval': {'doc': 'This option allows you to specify the interval (in seconds) at which the <a href="#host_perfdata_file">host performance data file</a> is processed using the <a href="#host_perfdata_file_processing_command">host performance data file processing command</a>.  A value of 0 indicates that the performance data file should not be processed at regular intervals. ',
                                            'examples': ['host_perfdata_file_processing_interval=0'],
                                            'format': 'host_perfdata_file_processing_interval=&lt;seconds&gt;',
                                            'options': [],
                                            'title': 'Host Performance Data File Processing Interval'},
 'host_perfdata_file_template': {'doc': 'This option determines what (and how) data is written to the <a href="#host_perfdata_file">host performance data file</a>.  The template may contain <a href="macros.html">macros</a>, special characters (\\t for tab, \\r for carriage return, \\n for newline) and plain text.  A newline is automatically added after each write to the performance data file. ',
                                 'examples': ['host_perfdata_file_template=[HOSTPERFDATA]\\t$TIMET$\\t$HOSTNAME$\\t$HOSTEXECUTIONTIME$\\t$HOSTOUTPUT$\\t$HOSTPERFDATA$'],
                                 'format': 'host_perfdata_file_template=&lt;template&gt;',
                                 'options': [],
                                 'title': 'Host Performance Data File Template'},
 'illegal_macro_output_chars': {'doc': 'This option allows you to specify illegal characters that should be stripped from <a href="macros.html">macros</a> before being used in notifications, event handlers, and other commands.  This DOES NOT affect macros used in service or host check commands.  You can choose to not strip out the characters shown in the example above, but I recommend you do not do this.  Some of these characters are interpreted by the shell (i.e. the backtick) and can lead to security problems.  The following macros are stripped of the characters you specify:  <b>$HOSTOUTPUT$</b>, <b>$HOSTPERFDATA$</b>, <b>$HOSTACKAUTHOR$</b>, <b>$HOSTACKCOMMENT$</b>, <b>$SERVICEOUTPUT$</b>, <b>$SERVICEPERFDATA$</b>, <b>$SERVICEACKAUTHOR$</b>, and <b>$SERVICEACKCOMMENT$</b> ',
                                'examples': ['illegal_macro_output_chars=`~$^&amp;"|\'&lt;&gt;'],
                                'format': 'illegal_macro_output_chars=&lt;chars...&gt;',
                                'options': [],
                                'title': 'Illegal Macro Output Characters'},
 'illegal_object_name_chars': {'doc': 'This option allows you to specify illegal characters that cannot be used in host names, service descriptions, or names of other object types.  Nagios will allow you to use most characters in object definitions, but I recommend not using the characters shown in the example above.  Doing may give you problems in the web interface, notification commands, etc. ',
                               'examples': ['illegal_object_name_chars=`~!$%^&amp;*"|\'&lt;&gt;?,()='],
                               'format': 'illegal_object_name_chars=&lt;chars...&gt;',
                               'options': [],
                               'title': 'Illegal Object Name Characters'},
 'interval_length': {'doc': 'This is the number of seconds per "unit interval" used for timing in the scheduling queue, re-notifications, etc. "Units intervals" are used in the object configuration file to determine how often to run a service check, how often to re-notify a contact, etc. <strong>Important:</strong>  The default value for this is set to 60, which means that a "unit value" of 1 in the object configuration file will mean 60 seconds (1 minute).  I have not really tested other values for this variable, so proceed at your own risk if you decide to do so! ',
                     'examples': ['interval_length=60'],
                     'format': 'interval_length=&lt;seconds&gt;',
                     'options': [],
                     'title': 'Timing Interval Length'},
 'lock_file': {'doc': 'This option specifies the location of the lock file that Nagios should create when it runs as a daemon (when started with the -d command line argument).  This file contains the process id (PID) number of the running Nagios process. ',
               'examples': ['lock_file=/tmp/nagios.lock'],
               'format': 'lock_file=&lt;file_name&gt;',
               'options': [],
               'title': 'Lock File'},
 'log_archive_path': {'doc': 'This is the directory where Nagios should place log files that have been rotated.  This option is ignored if you choose to not use the <a href="#log_rotation_method">log rotation</a> functionality. ',
                      'examples': ['log_archive_path=/usr/local/nagios/var/archives/'],
                      'format': 'log_archive_path=&lt;path&gt;',
                      'options': [],
                      'title': 'Log Archive Path'},
 'log_event_handlers': {'doc': 'This variable determines whether or not service and host <a href="eventhandlers.html">event handlers</a> are logged. Event handlers are optional commands that can be run whenever a service or hosts changes state.  Logging event handlers is most useful when debugging Nagios or first trying out your event handler scripts. ',
                        'examples': ['log_event_handlers=1'],
                        'format': 'log_event_handlers=&lt;0/1&gt;',
                        'options': ["0 = Don't log event handlers",
                                    '1 = Log event handlers'],
                        'title': 'Event Handler Logging Option'},
 'log_external_commands': {'doc': 'This variable determines whether or not Nagios will log <a href="extcommands.html">external commands</a> that it receives from the <a href="#command_file">external command file</a>.  Note: This option does not control whether or not <a href="passivechecks.html">passive service checks</a> (which are a type of external command) get logged.  To enable or disable logging of passive checks, use the <a href="#log_passive_checks">log_passive_checks</a> option. ',
                           'examples': ['log_external_commands=1'],
                           'format': 'log_external_commands=&lt;0/1&gt;',
                           'options': ["0 = Don't log external commands",
                                       '1 = Log external commands (default)'],
                           'title': 'External Command Logging Option'},
 'log_file': {'doc': 'This variable specifies where Nagios should create its main log file.  This should be the first variable that you define in your configuration file, as Nagios will try to write errors that it finds in the rest of your configuration data to this file.  If you have <a href="#log_rotation_method">log rotation</a> enabled, this file will automatically be rotated every hour, day, week, or month. ',
              'examples': ['log_file=/usr/local/nagios/var/nagios.log'],
              'format': 'log_file=&lt;file_name&gt;',
              'options': [],
              'title': 'Log File'},
 'log_host_retries': {'doc': 'This variable determines whether or not host check retries are logged.  Logging host check retries is mostly useful when attempting to debug Nagios or test out host <a href="eventhandlers.html">event handlers</a>. ',
                      'examples': ['log_host_retries=1'],
                      'format': 'log_host_retries=&lt;0/1&gt;',
                      'options': ["0 = Don't log host check retries",
                                  '1 = Log host check retries'],
                      'title': 'Host Check Retry Logging Option'},
 'log_initial_states': {'doc': 'This variable determines whether or not Nagios will force all initial host and service states to be logged, even if they result in an OK state.  Initial service and host states are normally only logged when there is a problem on the first check.  Enabling this option is useful if you are using an application that scans the log file to determine long-term state statistics for services and hosts. ',
                        'examples': ['log_initial_states=1'],
                        'format': 'log_initial_states=&lt;0/1&gt;',
                        'options': ["0 = Don't log initial states (default)",
                                    '1 = Log initial states'],
                        'title': 'Initial States Logging Option'},
 'log_notifications': {'doc': 'This variable determines whether or not notification messages are logged.  If you have a lot of contacts or regular service failures your log file will grow relatively quickly.  Use this option to keep contact notifications from being logged. ',
                       'examples': ['log_notifications=1'],
                       'format': 'log_notifications=&lt;0/1&gt;',
                       'options': ["0 = Don't log notifications",
                                   '1 = Log notifications'],
                       'title': 'Notification Logging Option'},
 'log_passive_checks': {'doc': 'This variable determines whether or not Nagios will log <a href="passivechecks.html">passive host and service checks</a> that it receives from the <a href="#command_file">external command file</a>.  If you are setting up a <a href="distributed.html">distributed monitoring environment</a> or plan on handling a large number of passive checks on a regular basis, you may wish to disable this option so your log file doesn\'t get too large. ',
                        'examples': ['log_passive_checks=1'],
                        'format': 'log_passive_checks=&lt;0/1&gt;',
                        'options': ["0 = Don't log passive checks",
                                    '1 = Log passive checks (default)'],
                        'title': 'Passive Check Logging Option'},
 'log_rotation_method': {'doc': 'This is the rotation method that you would like Nagios to use for your log file.  Values are as follows: ',
                         'examples': ['log_rotation_method=d'],
                         'format': 'log_rotation_method=&lt;n/h/d/w/m&gt;',
                         'options': ["n = None (don't rotate the log - this is the default)",
                                     'h = Hourly (rotate the log at the top of each hour)',
                                     'd = Daily (rotate the log at midnight each day)',
                                     'w = Weekly (rotate the log at midnight on Saturday)',
                                     'm = Monthly (rotate the log at midnight on the last day of the month)'],
                         'title': 'Log Rotation Method'},
 'log_service_retries': {'doc': 'This variable determines whether or not service check retries are logged.  Service check retries occur when a service check results in a non-OK state, but you have configured Nagios to retry the service more than once before responding to the error.  Services in this situation are considered to be in "soft" states.  Logging service check retries is mostly useful when attempting to debug Nagios or test out service <a href="eventhandlers.html">event handlers</a>. ',
                         'examples': ['log_service_retries=1'],
                         'format': 'log_service_retries=&lt;0/1&gt;',
                         'options': ["0 = Don't log service check retries",
                                     '1 = Log service check retries'],
                         'title': 'Service Check Retry Logging Option'},
 'low_host_flap_threshold': {'doc': 'This option is used to set the low threshold for detection of host flapping.  For more information on how flap detection and handling works (and how this option affects things) read <a href="flapping.html">this</a>. ',
                             'examples': ['low_host_flap_threshold=25.0'],
                             'format': 'low_host_flap_threshold=&lt;percent&gt;',
                             'options': [],
                             'title': 'Low Host Flap Threshold'},
 'low_service_flap_threshold': {'doc': 'This option is used to set the low threshold for detection of service flapping.  For more information on how flap detection and handling works (and how this option affects things) read <a href="flapping.html">this</a>. ',
                                'examples': ['low_service_flap_threshold=25.0'],
                                'format': 'low_service_flap_threshold=&lt;percent&gt;',
                                'options': [],
                                'title': 'Low Service Flap Threshold'},
 'max_check_result_file_age': {'doc': 'This options determines the maximum age in seconds that Nagios will consider check result files found in the <a href="#check_result_path">check_result_path</a> directory to be valid.  Check result files that are older that this threshold will be deleted by Nagios and the check results they contain will not be processed.  By using a value of zero (0) with this option, Nagios will process all check result files - even if they\'re older than your hardware :-). ',
                               'examples': ['max_check_result_file_age=3600'],
                               'format': 'max_check_result_file_age=&lt;seconds&gt;',
                               'options': [],
                               'title': 'Max Check Result File Age'},
 'max_check_result_reaper_time': {'doc': 'This option allows you to control the maximum amount of time <i>in seconds</i> that host and service check result "reaper" events are allowed to run.  "Reaper" events process the results from host and service checks that have finished executing.  If there are a lot of results to process, reaper events may take a long time to finish, which might delay timely execution of new host and service checks.  This variable allows you to limit the amount of time that an individual reaper event will run before it hands control back over to Nagios for other portions of the monitoring logic. ',
                                  'examples': ['max_check_result_reaper_time=30'],
                                  'format': 'max_check_result_reaper_time=&lt;seconds&gt;',
                                  'options': [],
                                  'title': 'Maximum Check Result Reaper Time'},
 'max_concurrent_checks': {'doc': 'This option allows you to specify the maximum number of service checks that can be run in parallel at any given time.  Specifying a value of 1 for this variable essentially prevents any service checks from being run in parallel.  Specifying a value of 0 (the default) does not place any restrictions on the number of concurrent checks.  You\'ll have to modify this value based on the system resources you have available on the machine that runs Nagios, as it directly affects the maximum load that will be imposed on the system (processor utilization, memory, etc.).  More information on how to estimate how many concurrent checks you should allow can be found <a href="checkscheduling.html#max_concurrent_checks">here</a>. ',
                           'examples': ['max_concurrent_checks=20'],
                           'format': 'max_concurrent_checks=&lt;max_checks&gt;',
                           'options': [],
                           'title': 'Maximum Concurrent Service Checks'},
 'max_debug_file_size': {'doc': 'This option determines the maximum size (in bytes) of the <a href="#debug_file">debug file</a>.  If the file grows larger than this size, it will be renamed with a .old  extension.  If a file already exists with a .old extension it will automatically be deleted.  This helps ensure your disk space usage doesn\'t get out of control when debugging Nagios. ',
                         'examples': ['max_debug_file_size=1000000'],
                         'format': 'max_debug_file_size=&lt;#&gt;',
                         'options': [],
                         'title': 'Maximum Debug File Size'},
 'max_host_check_spread': {'doc': 'This option determines the maximum number of minutes from when Nagios starts that all hosts (that are scheduled to be regularly checked) are checked.  This option will automatically adjust the <a href="#host_inter_check_delay_method">host inter-check delay method</a> (if necessary) to ensure that the initial checks of all hosts occur within the timeframe you specify.  In general, this option will not have an affect on host check scheduling if scheduling information is being retained using the <a href="#use_retained_scheduling_info">use_retained_scheduling_info</a> option.  Default value is <b>30</b> (minutes). ',
                           'examples': ['max_host_check_spread=30'],
                           'format': 'max_host_check_spread=&lt;minutes&gt;',
                           'options': [],
                           'title': 'Maximum Host Check Spread'},
 'max_service_check_spread': {'doc': 'This option determines the maximum number of minutes from when Nagios starts that all services (that are scheduled to be regularly checked) are checked.  This option will automatically adjust the <a href="#service_inter_check_delay_method">service inter-check delay method</a> (if necessary) to ensure that the initial checks of all services occur within the timeframe you specify.  In general, this option will not have an affect on service check scheduling if scheduling information is being retained using the <a href="#use_retained_scheduling_info">use_retained_scheduling_info</a> option.  Default value is <b>30</b> (minutes). ',
                              'examples': ['max_service_check_spread=30'],
                              'format': 'max_service_check_spread=&lt;minutes&gt;',
                              'options': [],
                              'title': 'Maximum Service Check Spread'},
 'nagios_group': {'doc': 'This is used to set the effective group that the Nagios process should run as.  After initial program startup and before starting to monitor anything, Nagios will drop its effective privileges and run as this group.  You may specify either a groupname or a GID. ',
                  'examples': ['nagios_group=nagios'],
                  'format': 'nagios_group=&lt;groupname/GID&gt;',
                  'options': [],
                  'title': 'Nagios Group'},
 'nagios_user': {'doc': 'This is used to set the effective user that the Nagios process should run as.  After initial program startup and before starting to monitor anything, Nagios will drop its effective privileges and run as this user.  You may specify either a username or a UID. ',
                 'examples': ['nagios_user=nagios'],
                 'format': 'nagios_user=&lt;username/UID&gt;',
                 'options': [],
                 'title': 'Nagios User'},
 'notification_timeout': {'doc': 'This is the maximum number of seconds that Nagios will allow notification commands to be run.  If a notification command exceeds this time limit it will be killed and a warning will be logged. There is often widespread confusion as to what this option really does.  It is meant to be used as a last ditch mechanism to kill off commands which are misbehaving and not exiting in a timely manner.  It should be set to something high (like 60 seconds or more), so that each notification command finishes executing within this time limit.  If a notification command runs longer than this limit, Nagios will kill it off thinking it is a runaway processes. ',
                          'examples': ['notification_timeout=60'],
                          'format': 'notification_timeout=&lt;seconds&gt;',
                          'options': [],
                          'title': 'Notification Timeout'},
 'object_cache_file': {'doc': 'This directive is used to specify a file in which a cached copy of <a href="configobject.html">object definitions</a> should be stored.  The cache file is (re)created every time Nagios is (re)started and is used by the CGIs.   It is intended to speed up config file caching in the CGIs and allow you to edit the source <a href="#cfg_file">object config files</a> while Nagios is running without affecting the output displayed in the CGIs. ',
                       'examples': ['object_cache_file=/usr/local/nagios/var/objects.cache'],
                       'format': 'object_cache_file=&lt;file_name&gt;',
                       'options': [],
                       'title': 'Object Cache File'},
 'obsess_over_hosts': {'doc': 'This value determines whether or not Nagios will "obsess" over host checks results and run the <a href="#ochp_command">obsessive compulsive host processor command</a> you define.  I know - funny name, but it was all I could think of.  This option is useful for performing <a href="distributed.html">distributed monitoring</a>.  If you\'re not doing distributed monitoring, don\'t enable this option. ',
                       'examples': ['obsess_over_hosts=1'],
                       'format': 'obsess_over_hosts=&lt;0/1&gt;',
                       'options': ["0 = Don't obsess over hosts (default)",
                                   '1 = Obsess over hosts'],
                       'title': 'Obsess Over Hosts Option'},
 'obsess_over_services': {'doc': 'This value determines whether or not Nagios will "obsess" over service checks results and run the <a href="#ocsp_command">obsessive compulsive service processor command</a> you define.  I know - funny name, but it was all I could think of.  This option is useful for performing <a href="distributed.html">distributed monitoring</a>.  If you\'re not doing distributed monitoring, don\'t enable this option. ',
                          'examples': ['obsess_over_services=1'],
                          'format': 'obsess_over_services=&lt;0/1&gt;',
                          'options': ["0 = Don't obsess over services (default)",
                                      '1 = Obsess over services'],
                          'title': 'Obsess Over Services Option'},
 'ochp_command': {'doc': 'This option allows you to specify a command to be run after <i>every</i> host check, which can be useful in <a href="distributed.html">distributed monitoring</a>.  This command is executed after any <a href="eventhandlers.html">event handler</a> or <a href="notifications.html">notification</a> commands.  The <i>command</i> argument is the short name of a <a href="objectdefinitions.html#command">command definition</a> that you define in your object configuration file.  The maximum amount of time that this command can run is controlled by the <a href="#ochp_timeout">ochp_timeout</a> option.   More information on distributed monitoring can be found <a href="distributed.html">here</a>.  This command is only executed if the <a href="#obsess_over_hosts">obsess_over_hosts</a> option is enabled globally and if the <i>obsess_over_host</i> directive in the <a href="objectdefinitions.html#host">host definition</a> is enabled. ',
                  'examples': ['ochp_command=obsessive_host_handler'],
                  'format': 'ochp_command=&lt;command&gt;',
                  'options': [],
                  'title': 'Obsessive Compulsive Host Processor Command'},
 'ochp_timeout': {'doc': 'This is the maximum number of seconds that Nagios will allow an <a href="#ochp_command">obsessive compulsive host processor command</a> to be run.  If a command exceeds this time limit it will be killed and a warning will be logged. ',
                  'examples': ['ochp_timeout=5'],
                  'format': 'ochp_timeout=&lt;seconds&gt;',
                  'options': [],
                  'title': 'Obsessive Compulsive Host Processor Timeout'},
 'ocsp_command': {'doc': 'This option allows you to specify a command to be run after <i>every</i> service check, which can be useful in <a href="distributed.html">distributed monitoring</a>.  This command is executed after any <a href="eventhandlers.html">event handler</a> or <a href="notifications.html">notification</a> commands.  The <i>command</i> argument is the short name of a <a href="objectdefinitions.html#command">command definition</a> that you define in your object configuration file.  The maximum amount of time that this command can run is controlled by the <a href="#ocsp_timeout">ocsp_timeout</a> option.   More information on distributed monitoring can be found <a href="distributed.html">here</a>.  This command is only executed if the <a href="#obsess_over_services">obsess_over_services</a> option is enabled globally and if the <i>obsess_over_service</i> directive in the <a href="objectdefinitions.html#service">service definition</a> is enabled. ',
                  'examples': ['ocsp_command=obsessive_service_handler'],
                  'format': 'ocsp_command=&lt;command&gt;',
                  'options': [],
                  'title': 'Obsessive Compulsive Service Processor Command'},
 'ocsp_timeout': {'doc': 'This is the maximum number of seconds that Nagios will allow an <a href="#ocsp_command">obsessive compulsive service processor command</a> to be run.  If a command exceeds this time limit it will be killed and a warning will be logged. ',
                  'examples': ['ocsp_timeout=5'],
                  'format': 'ocsp_timeout=&lt;seconds&gt;',
                  'options': [],
                  'title': 'Obsessive Compulsive Service Processor Timeout'},
 'passive_host_checks_are_soft': {'doc': 'This option determines whether or not Nagios will treat <a href="passivechecks.html">passive host checks</a> as HARD states or SOFT states.  By default, a passive host check result will put a host into a <a href="statetypes.html">HARD state type</a>.  You can change this behavior by enabling this option. ',
                                  'examples': ['passive_host_checks_are_soft=1'],
                                  'format': 'passive_host_checks_are_soft=&lt;0/1&gt;',
                                  'options': ['0 = Passive host checks are HARD (default)',
                                              '1 = Passive host checks are SOFT'],
                                  'title': 'Passive Host Checks Are SOFT Option'},
 'perfdata_timeout': {'doc': 'This is the maximum number of seconds that Nagios will allow a <a href="#host_perfdata_command">host performance data processor command</a> or <a href="#service_perfdata_command">service performance data processor command</a> to be run.  If a command exceeds this time limit it will be killed and a warning will be logged. ',
                      'examples': ['perfdata_timeout=5'],
                      'format': 'perfdata_timeout=&lt;seconds&gt;',
                      'options': [],
                      'title': 'Performance Data Processor Command Timeout'},
 'precached_object_file': {'doc': 'This directive is used to specify a file in which a pre-processed, pre-cached copy of <a href="configobject.html">object definitions</a> should be stored.  This file can be used to drastically improve startup times in large/complex Nagios installations.  Read more information on how to speed up start times <a href="faststartup.html">here</a>. ',
                           'examples': ['precached_object_file=/usr/local/nagios/var/objects.precache'],
                           'format': 'precached_object_file=&lt;file_name&gt;',
                           'options': [],
                           'title': 'Precached Object File'},
 'process_performance_data': {'doc': 'This value determines whether or not Nagios will process host and service check <a href="perfdata.html">performance data</a>. ',
                              'examples': ['process_performance_data=1'],
                              'format': 'process_performance_data=&lt;0/1&gt;',
                              'options': ["0 = Don't process performance data (default)",
                                          '1 = Process performance data'],
                              'title': 'Performance Data Processing Option'},
 'resource_file': {'doc': 'This is used to specify an optional resource file that can contain $USERn$ <a href="macros.html">macro</a> definitions.  $USERn$ macros are useful for storing usernames, passwords, and items commonly used in command definitions (like directory paths).  The CGIs will <i>not</i> attempt to read resource files, so you can set restrictive permissions (600 or 660) on them to protect sensitive information.  You can include multiple resource files by adding multiple resource_file statements to the main config file - Nagios will process them all.  See the sample resource.cfg file in the <i>sample-config/</i> subdirectory of the Nagios distribution for an example of how to define $USERn$ macros. ',
                   'examples': ['resource_file=/usr/local/nagios/etc/resource.cfg'],
                   'format': 'resource_file=&lt;file_name&gt;',
                   'options': [],
                   'title': 'Resource File'},
 'retain_state_information': {'doc': 'This option determines whether or not Nagios will retain state information for hosts and services between program restarts.  If you enable this option, you should supply a value for the <a href="#state_retention_file">state_retention_file</a> variable.  When enabled, Nagios will save all state information for hosts and service before it shuts down (or restarts) and will read in previously saved state information when it starts up again. ',
                              'examples': ['retain_state_information=1'],
                              'format': 'retain_state_information=&lt;0/1&gt;',
                              'options': ["0 = Don't retain state information",
                                          '1 = Retain state information (default)'],
                              'title': 'State Retention Option'},
 'retained_contact_host_attribute_mask': {'doc': '',
                                          'examples': [],
                                          'format': '',
                                          'options': [],
                                          'title': ''},
 'retained_contact_service_attribute_mask': {'doc': 'WARNING: This is an advanced feature.  You\'ll need to read the Nagios source code to use this option effectively. These options determine which contact attributes are NOT retained across program restarts.  There are two masks because there are often separate host and service contact attributes that can be changed.  The values for these options are a bitwise AND of values specified by the "MODATTR_" definitions in the include/common.h source code file.  By default, all process attributes are retained. ',
                                             'examples': ['retained_contact_host_attribute_mask=0',
                                                          'retained_contact_service_attribute_mask=0'],
                                             'format': '',
                                             'options': [],
                                             'title': 'Retained Contact Attribute Masks'},
 'retained_host_attribute_mask': {'doc': '',
                                  'examples': [],
                                  'format': '',
                                  'options': [],
                                  'title': ''},
 'retained_process_host_attribute_mask': {'doc': '',
                                          'examples': [],
                                          'format': '',
                                          'options': [],
                                          'title': ''},
 'retained_process_service_attribute_mask': {'doc': 'WARNING: This is an advanced feature.  You\'ll need to read the Nagios source code to use this option effectively. These options determine which process attributes are NOT retained across program restarts.  There are two masks because there are often separate host and service process attributes that can be changed.  For example, host checks can be disabled at the program level, while service checks are still enabled.  The values for these options are a bitwise AND of values specified by the "MODATTR_" definitions in the include/common.h source code file.  By default, all process attributes are retained. ',
                                             'examples': ['retained_process_host_attribute_mask=0',
                                                          'retained_process_service_attribute_mask=0'],
                                             'format': '',
                                             'options': [],
                                             'title': 'Retained Process Attribute Masks'},
 'retained_service_attribute_mask': {'doc': 'WARNING: This is an advanced feature.  You\'ll need to read the Nagios source code to use this option effectively. These options determine which host or service attributes are NOT retained across program restarts.  The values for these options are a bitwise AND of values specified by the "MODATTR_" definitions in the include/common.h source code file.  By default, all host and service attributes are retained. ',
                                     'examples': ['retained_host_attribute_mask=0',
                                                  'retained_service_attribute_mask=0'],
                                     'format': '',
                                     'options': [],
                                     'title': 'Retained Host and Service Attribute Masks'},
 'retention_update_interval': {'doc': 'This setting determines how often (in minutes) that Nagios will automatically save retention data during normal operation.  If you set this value to 0, Nagios will not save retention data at regular intervals, but it will still save retention data before shutting down or restarting.  If you have disabled state retention (with the <a href="#retain_state_information">retain_state_information</a> option), this option has no effect. ',
                               'examples': ['retention_update_interval=60'],
                               'format': 'retention_update_interval=&lt;minutes&gt;',
                               'options': [],
                               'title': 'Automatic State Retention Update Interval'},
 'service_check_timeout': {'doc': 'This is the maximum number of seconds that Nagios will allow service checks to run.  If checks exceed this limit, they are killed and a CRITICAL state is returned.   A timeout error will also be logged. There is often widespread confusion as to what this option really does.  It is meant to be used as a last ditch mechanism to kill off plugins which are misbehaving and not exiting in a timely manner.  It should be set to something high (like 60 seconds or more), so that each service check normally finishes executing within this time limit.  If a service check runs longer than this limit, Nagios will kill it off thinking it is a runaway processes. ',
                           'examples': ['service_check_timeout=60'],
                           'format': 'service_check_timeout=&lt;seconds&gt;',
                           'options': [],
                           'title': 'Service Check Timeout'},
 'service_freshness_check_interval': {'doc': 'This setting determines how often (in seconds) Nagios will periodically check the "freshness" of service check results.  If you have disabled service freshness checking (with the <a href="#check_service_freshness">check_service_freshness</a> option), this option has no effect.  More information on freshness checking can be found <a href="freshness.html">here</a>. ',
                                      'examples': ['service_freshness_check_interval=60'],
                                      'format': 'service_freshness_check_interval=&lt;seconds&gt;',
                                      'options': [],
                                      'title': 'Service Freshness Check Interval'},
 'service_inter_check_delay_method': {'doc': 'This option allows you to control how service checks are initially "spread out" in the event queue.  Using a "smart" delay calculation (the default) will cause Nagios to calculate an average check interval and spread initial checks of all services out over that interval, thereby helping to eliminate CPU load spikes.  Using no delay is generally <i>not</i> recommended, as it will cause all service checks to be scheduled for execution at the same time.  This means that you will generally have large CPU spikes when the services are all executed in parallel.   More information on how to estimate how the inter-check delay affects service check scheduling can be found <a href="checkscheduling.html#service_inter_check_delay">here</a>.  Values are as follows: ',
                                      'examples': ['service_inter_check_delay_method=s'],
                                      'format': 'service_inter_check_delay_method=&lt;n/d/s/x.xx&gt;',
                                      'options': ["n = Don't use any delay - schedule all service checks to run immediately (i.e. at the same time!)",
                                                  'd = Use a "dumb" delay of 1 second between service checks',
                                                  's = Use a "smart" delay calculation to spread service checks out evenly (default)',
                                                  'x.xx = Use a user-supplied inter-check delay of x.xx seconds'],
                                      'title': 'Service Inter-Check Delay Method'},
 'service_interleave_factor': {'doc': 'This variable determines how service checks are interleaved. Interleaving allows for a more even distribution of service checks, reduced load on remote hosts, and faster overall detection of host problems.  Setting this value to 1 is equivalent to not interleaving the service checks (this is how versions of Nagios previous to 0.0.5 worked).  Set this value to <b>s</b> (smart) for automatic calculation of the interleave factor unless you have a specific reason to change it.  The best way to understand how interleaving works is to watch the <a href="cgis.html#status_cgi">status CGI</a> (detailed view) when Nagios is just starting.  You should see that the service check results are spread out as they begin to appear.  More information on how interleaving works can be found <a href="checkscheduling.html#service_interleaving">here</a>. <ul> <li><i>x</i> = A number greater than or equal to 1 that specifies the interleave factor to use.  An interleave factor of 1 is equivalent to not interleaving the service checks. <li>s = Use a "smart" interleave factor calculation (default) </ul> ',
                               'examples': ['service_interleave_factor=s'],
                               'format': 'service_interleave_factor=&lt;s|<i>x</i>&gt;',
                               'options': ['<i>x</i> = A number greater than or equal to 1 that specifies the interleave factor to use.  An interleave factor of 1 is equivalent to not interleaving the service checks.',
                                           's = Use a "smart" interleave factor calculation (default)'],
                               'title': 'Service Interleave Factor'},
 'service_perfdata_command': {'doc': 'This option allows you to specify a command to be run after <i>every</i> service check to process service <a href="perfdata.html">performance data</a> that may be returned from the check.  The <i>command</i> argument is the short name of a <a href="objectdefinitions.html#command">command definition</a> that you define in your object configuration file.  This command is only executed if the <a href="#process_performance_data">process_performance_data</a> option is enabled globally and if the <i>process_perf_data</i> directive in the <a href="objectdefinitions.html#service">service definition</a> is enabled. ',
                              'examples': ['service_perfdata_command=process-service-perfdata'],
                              'format': 'service_perfdata_command=&lt;command&gt;',
                              'options': [],
                              'title': 'Service Performance Data Processing Command'},
 'service_perfdata_file': {'doc': 'This option allows you to specify a file to which service <a href="perfdata.html">performance data</a> will be written after every service check.  Data will be written to the performance file as specified by the <a href="#service_perfdata_file_template">service_perfdata_file_template</a> option.  Performance data is only written to this file if the <a href="#process_performance_data">process_performance_data</a> option is enabled globally and if the <i>process_perf_data</i> directive in the <a href="objectdefinitions.html#service">service definition</a> is enabled. ',
                           'examples': ['service_perfdata_file=/usr/local/nagios/var/service-perfdata.dat'],
                           'format': 'service_perfdata_file=&lt;file_name&gt;',
                           'options': [],
                           'title': 'Service Performance Data File'},
 'service_perfdata_file_mode': {'doc': 'This option determines how the <a href="#service_perfdata_file">service performance data file</a> is opened.  Unless the file is a named pipe you\'ll probably want to use the default mode of append. ',
                                'examples': ['service_perfdata_file_mode=a'],
                                'format': 'service_perfdata_file_mode=&lt;mode&gt;',
                                'options': ['a = Open file in append mode (default)',
                                            'w = Open file in write mode',
                                            'p = Open in non-blocking read/write mode (useful when writing to pipes)'],
                                'title': 'Service Performance Data File Mode'},
 'service_perfdata_file_processing_command': {'doc': 'This option allows you to specify the command that should be executed to process the <a href="#service_perfdata_file">service performance data file</a>.  The <i>command</i> argument is the short name of a <a href="objectdefinitions.html#command">command definition</a> that you define in your object configuration file.  The interval at which this command is executed is determined by the <a href="#service_perfdata_file_processing_interval">service_perfdata_file_processing_interval</a> directive. ',
                                              'examples': ['service_perfdata_file_processing_command=process-service-perfdata-file'],
                                              'format': 'service_perfdata_file_processing_command=&lt;command&gt;',
                                              'options': [],
                                              'title': 'Service Performance Data File Processing Command'},
 'service_perfdata_file_processing_interval': {'doc': 'This option allows you to specify the interval (in seconds) at which the <a href="#service_perfdata_file">service performance data file</a> is processed using the <a href="#service_perfdata_file_processing_command">service performance data file processing command</a>.  A value of 0 indicates that the performance data file should not be processed at regular intervals. ',
                                               'examples': ['service_perfdata_file_processing_interval=0'],
                                               'format': 'service_perfdata_file_processing_interval=&lt;seconds&gt;',
                                               'options': [],
                                               'title': 'Service Performance Data File Processing Interval'},
 'service_perfdata_file_template': {'doc': 'This option determines what (and how) data is written to the <a href="#service_perfdata_file">service performance data file</a>.  The template may contain <a href="macros.html">macros</a>, special characters (\\t for tab, \\r for carriage return, \\n for newline) and plain text.  A newline is automatically added after each write to the performance data file. ',
                                    'examples': ['service_perfdata_file_template=[SERVICEPERFDATA]\\t$TIMET$\\t$HOSTNAME$\\t$SERVICEDESC$\\t$SERVICEEXECUTIONTIME$\\t$SERVICELATENCY$\\t$SERVICEOUTPUT$\\t$SERVICEPERFDATA$'],
                                    'format': 'service_perfdata_file_template=&lt;template&gt;',
                                    'options': [],
                                    'title': 'Service Performance Data File Template'},
 'sleep_time': {'doc': 'This is the number of seconds that Nagios will sleep before checking to see if the next service or host check in the scheduling queue should be executed.  Note that Nagios will only sleep after it "catches up" with queued service checks that have fallen behind. ',
                'examples': ['sleep_time=1'],
                'format': 'sleep_time=&lt;seconds&gt;',
                'options': [],
                'title': 'Inter-Check Sleep Time'},
 'soft_state_dependencies': {'doc': 'This option determines whether or not Nagios will use soft state information when checking <a href="dependencies.html">host and service dependencies</a>.  Normally Nagios will only use the latest hard host or service state when checking dependencies.  If you want it to use the latest state (regardless of whether its a soft or hard <a href="statetypes.html">state type</a>), enable this option. ',
                             'examples': ['soft_state_dependencies=0'],
                             'format': 'soft_state_dependencies=&lt;0/1&gt;',
                             'options': ["0 = Don't use soft state dependencies (default)",
                                         '1 = Use soft state dependencies'],
                             'title': 'Soft State Dependencies Option'},
 'state_retention_file': {'doc': 'This is the file that Nagios will use for storing status, downtime, and comment information before it shuts down.  When Nagios is restarted it will use the information stored in this file for setting the initial states of services and hosts before it starts monitoring anything.   In order to make Nagios retain state information between program restarts, you must enable the <a href="#retain_state_information">retain_state_information</a> option. ',
                          'examples': ['state_retention_file=/usr/local/nagios/var/retention.dat'],
                          'format': 'state_retention_file=&lt;file_name&gt;',
                          'options': [],
                          'title': 'State Retention File'},
 'status_file': {'doc': '',
                 'examples': [],
                 'format': '',
                 'options': [],
                 'title': ''},
 'status_log': {'doc': 'This is the file that Nagios uses to store the current status, comment, and downtime information.  This file is used by the CGIs so that current monitoring status can be reported via a web interface.  The CGIs must have read access to this file in order to function properly.  This file is deleted every time Nagios stops and recreated when it starts. ',
                'examples': ['status_file=/usr/local/nagios/var/status.dat'],
                'format': 'status_file=&lt;file_name&gt;',
                'options': [],
                'title': 'Status File'},
 'status_update_interval': {'doc': 'This setting determines how often (in seconds) that Nagios will update status data in the <a href="#status_file">status file</a>.  The minimum update interval is 1 second. ',
                            'examples': ['status_update_interval=15'],
                            'format': 'status_update_interval=&lt;seconds&gt;',
                            'options': [],
                            'title': 'Status File Update Interval'},
 'temp_file': {'doc': 'This is a temporary file that Nagios periodically creates to use when updating comment data, status data, etc.  The file is deleted when it is no longer needed. ',
               'examples': ['temp_file=/usr/local/nagios/var/nagios.tmp'],
               'format': 'temp_file=&lt;file_name&gt;',
               'options': [],
               'title': 'Temp File'},
 'temp_path': {'doc': 'This is a directory that Nagios can use as scratch space for creating temporary files used during the monitoring process.  You should run <i>tmpwatch</i>, or a similiar utility, on this directory occassionally to delete files older than 24 hours. ',
               'examples': ['temp_path=/tmp'],
               'format': 'temp_path=&lt;dir_name&gt;',
               'options': [],
               'title': 'Temp Path'},
 'translate_passive_host_checks': {'doc': 'This option determines whether or not Nagios will translate DOWN/UNREACHABLE passive host check results to their "correct" state from the viewpoint of the local Nagios instance.  This can be very useful in distributed and failover monitoring installations.  More information on passive check state translation can be found <a href="passivestatetranslation.html">here</a>. ',
                                   'examples': ['translate_passive_host_checks=1'],
                                   'format': 'translate_passive_host_checks=&lt;0/1&gt;',
                                   'options': ['0 = Disable check translation (default)',
                                               '1 = Enable check translation'],
                                   'title': 'Translate Passive Host Checks Option'},
 'use_aggressive_host_checking': {'doc': 'Nagios tries to be smart about how and when it checks the status of hosts.  In general, disabling this option will allow Nagios to make some smarter decisions and check hosts a bit faster.  Enabling this option will increase the amount of time required to check hosts, but may improve reliability a bit.  Unless you have problems with Nagios not recognizing that a host recovered, I would suggest <b>not</b> enabling this option. ',
                                  'examples': ['use_aggressive_host_checking=0'],
                                  'format': 'use_aggressive_host_checking=&lt;0/1&gt;',
                                  'options': ["0 = Don't use aggressive host checking (default)",
                                              '1 = Use aggressive host checking'],
                                  'title': 'Aggressive Host Checking Option'},
 'use_agressive_host_checking': {'doc': '',
                                 'examples': [],
                                 'format': '',
                                 'options': [],
                                 'title': ''},
 'use_embedded_perl_implicitly': {'doc': 'This setting determines whether or not the embedded Perl interpreter should be used for Perl plugins/scripts that do not explicitly enable/disable it.  Nagios must be compiled with support for embedded Perl for this option to have an effect.  More information on the embedded Perl interpreter and the effect of this setting can be found <a href="embeddedperl.html">here</a>. ',
                                  'examples': ['use_embedded_perl_implicitly=1'],
                                  'format': 'use_embedded_perl_implicitly=&lt;0/1&gt;',
                                  'options': [],
                                  'title': 'Embedded Perl Implicit Use Option'},
 'use_large_installation_tweaks': {'doc': 'This option determines whether or not the Nagios daemon will take several shortcuts to improve performance.  These shortcuts result in the loss of a few features, but larger installations will likely see a lot of benefit from doing so.  More information on what optimizations are taken when you enable this option can be found <a href="largeinstalltweaks.html">here</a>. ',
                                   'examples': ['use_large_installation_tweaks=0'],
                                   'format': 'use_large_installation_tweaks=&lt;0/1&gt;',
                                   'options': ["0 = Don't use tweaks (default)",
                                               '1 = Use tweaks'],
                                   'title': 'Large Installation Tweaks Option'},
 'use_regexp_matching': {'doc': 'This option determines whether or not various directives in your <a href="configobject.html">object definitions</a> will be processed as regular expressions.  More information on how this works can be found <a href="objecttricks.html">here</a>. ',
                         'examples': ['use_regexp_matching=0'],
                         'format': 'use_regexp_matching=&lt;0/1&gt;',
                         'options': ["0 = Don't use regular expression matching (default)",
                                     '1 = Use regular expression matching'],
                         'title': 'Regular Expression Matching Option'},
 'use_retained_program_state': {'doc': 'This setting determines whether or not Nagios will set various program-wide state variables based on the values saved in the retention file.  Some of these program-wide state variables that are normally saved across program restarts if state retention is enabled include the <a href="#enable_notifications">enable_notifications</a>, <a href="#enable_flap_detection">enable_flap_detection</a>, <a href="#enable_event_handlers">enable_event_handlers</a>, <a href="#execute_service_checks">execute_service_checks</a>, and <a href="#accept_passive_service_checks">accept_passive_service_checks</a> options. If you do not have <a href="#retain_state_information">state retention</a> enabled, this option has no effect. ',
                                'examples': ['use_retained_program_state=1'],
                                'format': 'use_retained_program_state=&lt;0/1&gt;',
                                'options': ["0 = Don't use retained program state",
                                            '1 = Use retained program state (default)'],
                                'title': 'Use Retained Program State Option'},
 'use_retained_scheduling_info': {'doc': 'This setting determines whether or not Nagios will retain scheduling info (next check times) for hosts and services when it restarts.  If you are adding a large number (or percentage) of hosts and services, I would recommend disabling this option when you first restart Nagios, as it can adversely skew the spread of initial checks.  Otherwise you will probably want to  leave it enabled. ',
                                  'examples': ['use_retained_scheduling_info=1'],
                                  'format': 'use_retained_scheduling_info=&lt;0/1&gt;',
                                  'options': ["0 = Don't use retained scheduling info",
                                              '1 = Use retained scheduling info (default)'],
                                  'title': 'Use Retained Scheduling Info Option'},
 'use_syslog': {'doc': 'This variable determines whether messages are logged to the syslog facility on your local host.  Values are as follows: ',
                'examples': ['use_syslog=1'],
                'format': 'use_syslog=&lt;0/1&gt;',
                'options': ["0 = Don't use syslog facility",
                            '1 = Use syslog facility'],
                'title': 'Syslog Logging Option'},
 'use_timezone': {'doc': 'This option allows you to override the default timezone that this instance of Nagios runs in.  Useful if you have multiple instances of Nagios that need to run from the same server, but have different local times associated with them.  If not specified, Nagios will use the system configured timezone. <img src="images/note.gif" border="0" align="bottom" alt="Note" title="Note"> Note: If you use this option to specify a custom timezone, you will also need to alter the Apache configuration directives for the CGIs to specify the timezone you want.  Example: ',
                  'examples': ['use_timezone=US/Mountain'],
                  'format': 'use_timezone=&lt;tz&gt;',
                  'options': [],
                  'title': 'Timezone Option'},
 'use_true_regexp_matching': {'doc': 'If you\'ve enabled regular expression matching of various object directives using the <a href="#use_regexp_matching">use_regexp_matching</a> option, this option will determine when object directives are treated as regular expressions.  If this option is disabled (the default), directives will only be treated as regular expressions if they contain <b>*</b>, <b>?</b>, <b>+</b>, or <b>\\.</b>.  If this option is enabled, all appropriate directives will be treated as regular expression - be careful when enabling this!  More information on how this works can be found <a href="objecttricks.html">here</a>. ',
                              'examples': ['use_true_regexp_matching=0'],
                              'format': 'use_true_regexp_matching=&lt;0/1&gt;',
                              'options': ["0 = Don't use true regular expression matching (default)",
                                          '1 = Use true regular expression matching'],
                              'title': 'True Regular Expression Matching Option'}}
