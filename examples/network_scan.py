#!/usr/bin/python
import os
import sys
import logging
import socket
import time
import ConfigParser
from optparse import OptionParser

sys.path.insert(1, '../')
from pynag.Parsers import config

## Create the plugin option
nagios = config('/etc/nagios/nagios.cfg')
nagios.parse()


## User Variables
nagios_etc = "/etc/nagios"					## Nagios Configuration base
nagios_cfg = "%s/nagios.cfg" % nagios_etc	## Nagios CFG Full path

##
## Set up defaults and objects here
##

## This is a list of existing files
nagios_cfg_list = nagios.get_cfg_files()

## this is just the filenames, no paths
existing_file_list = []
for item in nagios_cfg_list:
	existing_file_list.append(os.path.basename(item))

## Start the counts
total_host_count = 0
active_host_count = 0

#set up command-line options
network_raw = None
host_raw = None
network_to_scan = None

## Start with an empty server list
server_list = []

## Setup exclusion lists
def parse_config_file(filename):
	return_list = []
	for item in open("/etc/nagios/nagscan/%s" % filename, 'r').readlines():
		return_list.append(item.strip())

	return return_list

## Scan Config files
exclude_hosts = parse_config_file("exclude_hosts")
exclude_oses = parse_config_file("exclude_oses")
exclude_mounts = parse_config_file("exclude_mounts")
exclude_mounts_partial = parse_config_file("exclude_mounts_partial")
pseudo_oses = parse_config_file("pseudo_oses")



## Config parser
parser = OptionParser()
parser.add_option("-n", "--network", help="Comma seperated list of networks", metavar="NETWORK", dest="network_raw")
parser.add_option("-c", "--host", help="List of Hosts", metavar="HOSTS", dest="host_raw")
parser.add_option("-p", "--preset-network", help="Network defined in networks.ini", metavar="PRESETNETWEORK", dest="presetnetwork")
parser.add_option("-g", "--hostgroup", help="Default Host group for these hosts", metavar="HOSTGROUP", dest="hostgroup")
parser.add_option("-l", "--loglevel", help="Log Level", metavar="LOGLEVEL", dest="log_level")
parser.add_option("-r", "--random", help="Randomize Server Scan ordering", metavar="RANDOM", action="store_true", dest="random")
parser.add_option("-q", "--quit-on-err", help="Quit on Errors", metavar="QUIT", action="store_true", dest="quit_on_err")

#grab options
(options, args) = parser.parse_args()
network_raw = options.network_raw
host_raw = options.host_raw
log_level = options.log_level
quit_on_err = options.quit_on_err
hostgroup = options.hostgroup
presetnetwork = options.presetnetwork
random = options.random

## Setup logging here
logger = logging.getLogger("simple_logger")
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()

if log_level == 'debug':
	ch.setLevel(logging.DEBUG)
elif log_level == 'info':
	ch.setLevel(logging.INFO)
else:
	ch.setLevel(logging.INFO)

formatter = logging.Formatter("%(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)
## End logging configuration


## Networking Subroutines
# Bytes used for local addresses in a class of IP
_netWorkClassDict={'a':3, 'b':2, 'c':1}
def backToDotNotation(val):
	res=[]
	tempVal=val
	for x in range(4):
		res.append(tempVal & 0xff)
		tempVal = tempVal >> 8
	res.reverse()
	return "%d.%d.%d.%d"%tuple(res)

def populate_subnet(network_string):
	net_vals = getValues(network_string)
	start = net_vals['ip']
	stop = net_vals['ip'] + net_vals['hosts']

	current_int = start
	ip_list = []


	while current_int <= stop:
		ip_list.append(backToDotNotation(current_int))
		
		current_int += 1

	return ip_list

def shiftOctents(octents):
	"""
	Convert dot separated IP format to a number
	This might exist in the socket module?
	"""
	octents=octents.split(".")
	octents.reverse()
	v=0
	for x in range(len(octents)):
		v|= int(octents[x]) << (x*8)
	return v

def getValues(input, netWorkClass='b'):
	"""
	Return IP converted to a number
	subnet address size
	host address size
	"""
	netWorkClass=netWorkClass.lower()

	ip, mask = input.split("/")
	mask = shiftOctents(mask)
	hosts = ~mask & 0xffffffffL -1

	val='0x'+'ff'*_netWorkClassDict[netWorkClass]
	netWorkClassMask = int(val, 16)
	subnet=max(0, (netWorkClassMask/(hosts+2)) -1)

	ip= shiftOctents(ip)
	dict = {}
	dict['ip'] = ip
	dict['subnet'] = subnet
	dict['hosts'] = hosts
	return dict

## This is for the network configuration
net_config = ConfigParser.ConfigParser()
net_config.read("/etc/nagios/networks.ini")

if hostgroup:
	if hostgroup not in nagios.get_object_list('hostgroup'):
		logger.error("No hostgroups named %s, quitting\n" % hostgroup)
		sys.exit(2)

if presetnetwork:
	## If one network is specified
	if presetnetwork in net_config.sections():

		hostgroup = net_config.get(presetnetwork, "hostgroup")
		network_raw = "%s/%s" % (net_config.get(presetnetwork, "network"), net_config.get(presetnetwork,"subnet"))

	## if all networks are specified
	elif presetnetwork.lower() == 'all':
		for section in net_config.sections():
			server_list.extend(populate_subnet("%s/%s" % (net_config.get(section, "network"), net_config.get(section,"subnet"))))

	## Error out, bad preset network
	else:
		logger.error("%s is not in the .ini file" % presetnetwork)
		sys.exit(2)

if not network_raw and not host_raw and not presetnetwork:
	logger.error("No networks or hosts specified")

	if quit_on_err:
		sys.exit(2)

if not network_to_scan:
	network_to_scan = network_raw
	


## Networking functions here
def check_mount(mount_label):
	## Skip empty lines
	if mount_label == "":
		return None
	if mount_label in exclude_mounts:
		return None

	for label in exclude_mounts_partial:
		if mount_label[0:len(label)] == label:
			return None

	## Strip out anything after a :
	if mount_label.find(":") != -1:
		mount_label = mount_label.split(":", 1)[0]
	
	## Return success
	return mount_label

def determine_os(os_string):
	if os_string.find("Linux") != -1:
		return "linux"
	elif os_string.find("Windows NT Version 4.0") != -1:
		return "windows_nt4"
	elif os_string.find("Windows") != -1:
		return "windows"
	elif os_string.find("HP-UX") != -1:
		return "hpux"
	elif os_string.find("NetApp") != -1:
		return "netapp"
	elif os_string.find("Fibre") != -1:
		return "fibre_switch"
	else:
		return None

def get_hostname(ip_address):
	try:
		hostname = socket.gethostbyaddr(ip_address)
		return hostname
	except:
		return None

def create_cpu_cfg(hostname, os_name):
	service_file = "%s/autogenerated-services/%s-cpu.cfg" % (nagios_etc, hostname)
	#if not os.path.isfile(service_file):
	if os.path.basename(service_file) in existing_file_list:
		logger.debug("%s already exists, skipping creation" % os.path.basename(service_file))
		return None

	logger.info("%s does not exist, creating it now" % os.path.basename(service_file))

	## Determin how to do the check
	if os_name == "linux":
		## We dont' really want any critical messages for this
		check_command = "check_linux_load!netsl!4,3,3!100,100,100"
	elif os_name == "windows":
		check_command = "check_hp_load!stand!80!99"
	elif os_name == "hpux":
		check_command = "check_hpux_load!2,10,10!3,10,10"
	elif os_name == "netapp":
		check_command = "check_netapp_cpu!95!100"

	content = """

define service {
	use                     %s-service         ; Name of service template to use
	host_name               %s
	name                    %s_PQ
	service_description     Processor Queue
	check_command           %s
}


""" % (os_name, hostname, hostname, check_command)
	f = open(service_file, 'w')
	f.write(content)
	f.close()

	return True

def create_snmp_cfg(hostname):
	service_file = "%s/autogenerated-services/%s-snmp.cfg" % (nagios_etc, hostname)
	#if not os.path.isfile(service_file):
	if os.path.basename(service_file) in existing_file_list:
		logger.debug("%s already exists, skipping creation" % os.path.basename(service_file))
		return None

	logger.info("%s does not exist, creating it now" % os.path.basename(service_file))

	content = """

define service {
	use                     linux-service         ; Name of service template to use
	host_name               %s
	name                    SNMP
	service_description     %s_SNMP
	check_command           check_snmp
	normal_check_interval	120
}


""" % (hostname, hostname)
	f = open(service_file, 'w')
	f.write(content)
	f.close()

	return True

def create_disk_cfg(hostname, disk_label, os_name):
	## Don't do anything for netapp disks
	if os_name == "netapp":
		return True

	disk_file = "%s/autogenerated-services/%s-disk-%s.cfg" % (nagios_etc, hostname, disk_label.replace("/","_"))

	## Make sure the root disk doesn't recurse down and match all disks
	if disk_label[0] == "/":
		disk_check_label = "%s$" % disk_label
	else:
		disk_check_label = disk_label


	## Set up some default values here
	warning_percentage = 90
	critical_percentage = 95
	register = 1

	## 'Memory' Disks should have a higher threshhold
	if disk_label == "Real Memory":
		warning_percentage = 99
		critical_percentage = 100

		## We don't care about linux memory usage, it should pretty much always be at 100
		if os_name == "linux":
			register = 0

	if os_name == 'hpux':
		check_command = """check_snmp_hpux_storage!"^%s"!%i!%i!""" % (disk_check_label, warning_percentage, critical_percentage)
	else:
		check_command = """check_snmp_storage!"^%s"!%i!%i!""" % (disk_check_label, warning_percentage, critical_percentage)

	if os.path.basename(disk_file) in existing_file_list:
		logger.debug("Skipping %s, it already exists" % os.path.basename(disk_file))
		return None

	logger.info("%s does not exist, creating it now" % os.path.basename(disk_file))

	content = """
define service {
	use                     %s-service         ; Name of service template to use
	host_name               %s
	name                    %s_%s_Drive
	service_description     %s Drive
	check_command           %s
	register				%i
}

""" % (os_name, hostname, hostname.capitalize(), disk_label, disk_label, check_command, register)
	f = open(disk_file, 'w')
	f.write(content)
	f.close()

	return True

def create_host_cfg(hostname, ip, os_name, parent=None):
	## Check if the hosts file exists, and create it if it doesn't
	host_file = "%s/autogenerated-hosts/%s.cfg" % (nagios_etc, hostname)
	hostname_short = hostname.split(".")[0]

	if not parent:
		logger.warning("Could not find parent for %s" % hostname)
		parent_string = ""
	else:
		parent_string = "parents        %s" % parent

	if os.path.basename(host_file) in existing_file_list:
		logger.debug("%s already exists, skipping" % host_file)
		return None

	logger.info("%s does not exist, creating it now" % host_file)
	content = """

define host{
        use                     %s-host
        host_name               %s
        alias                   %s
        address                 %s
        %s
        max_check_attempts      3
        notification_interval   120
}

define hostextinfo{
        use             %s-hostext
        host_name       %s
}

""" % (os_name, hostname, hostname, target, parent_string, os_name, hostname)

	f = open(host_file, 'w')
	f.write(content)
	f.close()
	return True

if network_to_scan:
	server_list = populate_subnet(network_to_scan)
		

if host_raw:
	logger.debug("Scanning %s" % host_raw)
	server_list.append(host_raw)

#server_list = ['smsdbinfo.rtp.ppdi.com']


## Start the timer
start_time = int(time.time())

## Sort the server list
server_list.reverse()

if random:
	import random
	random.shuffle(server_list)

#for target in server_list:
while len(server_list) > 0:
	## Make sure the hostname exists in DNS, if it doesn't, we are just going to skip it
	target = server_list.pop()
	hostname = None
	total_host_count += 1
	try:
		hostname = get_hostname(target)[0].split(".")[0]
	except:
		logger.debug("%s does not have a corresponding dns entry, skipping" % target)
		continue

	if hostname in exclude_hosts:
		logger.debug("%s is in the exclusion list, skipping" % hostname)
		continue

	result = os.system('/bin/ping -c 1 %s &>/dev/null' % target)
	if result != 0:
		logger.debug("%s is not responding to pings, skipping" % hostname)
		continue

	result = os.system('/usr/bin/snmpwalk -v 1 -t 1 -c 1CmPq2  %s system &>/dev/null' % target )
	if result != 0:
		logger.debug("skipping %s, it is not responding to snmp requests" % hostname)
		continue

	logger.debug("Successfully scanned %s, continuing" % hostname)
	active_host_count += 1
	try:
		os_string = os.popen("/usr/bin/snmpwalk -v 1 -c 1CmPq2 %s system.sysDescr.0" % target).readlines()[0].split("STRING:")[1]
	except:
		logger.warning("Could not get an os string for %s, skipping" % hostname)
		continue


	## Determin the os
	os_name = determine_os(os_string)
	if not os_name:
		logger.error("Could not determine os for %s on %s" % (os_string.strip(), target))
		if quit_on_err:
			sys.exit(2)

	## Skip certain Oses
	if os_name in exclude_oses:
		logger.debug("Skipping %s, it's in the os exclusion list" % hostname)
		continue

	logger.debug("%s is good (os is %s)" % (hostname, os_name))


	parent = None
	try:
		gateway = os.popen("/usr/bin/snmpget -v 1 -c 1CmPq2 %s ipRouteNextHop.0.0.0.0" % target).readlines()[0].split("IpAddress: ")[1].strip()
	except:
		gateway = None		
		
	if gateway:
		#parent = nagios.get_name_from_address(gateway)
		parent = nagios.get_object('host', gateway, user_key = 'address')['alias']

	if not parent:
		logger.warning("No parent for %s, gw: %s" % (target, gateway))

		if quit_on_err:
			sys.exit(2)

	## If this os has good storage, do the following:
	if os_name not in pseudo_oses:
		output = os.popen("/usr/lib/nagios/plugins/walk_storage.pl -H %s -C 1CmPq2 -w 90 -c 99 -m" % target).readlines()

		## Little hack to fix errored drive queries
		if output[0][0:5] == "ERROR":
			output = os.popen("/usr/lib/nagios/plugins/walk_storage.pl -H %s -C 1CmPq2 -w 90 -c 99 -m ^/" % target).readlines()

		## Hmmm, see if it's an hpux host
		if output[0][0:5] == "ERROR":
			output = os.popen("/usr/lib/nagios/plugins/walk_storage_ux.pl -H %s -C 1CmPq2 -w 90 -c 99 -m ^/" % target).readlines()

		## If we still cant get a valid output, just continue
		if output[0][0:5] == "ERROR":
			logger.warning("Error while retrieving disk on %s (%s), please retry it manually" % (hostname, target))
			continue

		valid_mount_list = []
		for mount_full in output:
			## Strip out any funky characters
			mount_full = mount_full.strip()
	
			## Make sure the mount is valid
			mount_full = check_mount(mount_full)
			if mount_full:
				valid_mount_list.append(mount_full)
		logger.debug("%s contains %s" % (hostname, ", ".join(valid_mount_list)))
		for mount in valid_mount_list:
			create_disk_cfg(hostname, mount, os_name)

	create_host_cfg(hostname, target, os_name, parent)
	## Reparse the configuration
	nagios.parse()

	## Don't create these right now, may readd it back in later
	#create_snmp_cfg(hostname)

	if os_name not in pseudo_oses:
		create_cpu_cfg(hostname, os_name)
		nagios.add_alias_to_hostgroup(hostname, '%s_servers' % os_name)

	if hostgroup:
		nagios.add_alias_to_hostgroup(hostname, hostgroup)

## Stop the timer
stop_time = int(time.time())
total_time = (stop_time - start_time) / 60

## Reload the nagios daemon to apply changes
#nagios.reload_nagios()

## Output statistical information on what the script pulled
logger.info("Minutes to complete:  %s" % total_time)
logger.info("Total Hosts Scanned:  %i" % total_host_count)
logger.info("Active Hosts Scanned:  %i" % active_host_count)
