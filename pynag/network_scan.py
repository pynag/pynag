#!/usr/bin/python
import subprocess
import socket
import sys
sys.path.insert(0,'/opt/pynag')
from pynag import Model

class ScannedHost:
	"Simple datastructure for a recently portscanned host"
	def __init__(self, ipaddress=None, hostname=None):
		self.ipaddress = ipaddress
		self.hostname = hostname
	
def runCommand(command):
	proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE,)
	stdout, stderr = proc.communicate('through stdin to stdout')
	returncode = proc.returncode
	return returncode,stdout,stderr


def get_ip_address_list():
	'returns a list of every ip address of every host in nagios'
	hosts = Model.Host.objects.all
	result = []
	for host in hosts:
		a = host['address']
		if a != None and a not in result:
			result.append(a)
	return result

def check_nrpe(host):
	command = "check_nrpe -H '%s'" % (host)
	
	
def pingscan(network='192.168.1.0/24'):
	'scans a specific network, returns a list of all ip that respond'
	r,stdout,stderr = runCommand("fping -a -g %s" % network)
	if r > 1:
		raise Exception("Error running fping: %s" % stderr)
	ip_list = []
	for i in stdout.split('\n'):
		try: socket.inet_aton(i)
		except: continue
		ip_list.append(i)
	return ip_list

if __name__ == '__main__':
	scanned_ips = pingscan(network='127.0.0.1/32')
	registered_ips = get_ip_address_list()
	for i in scanned_ips:
		if i not in registered_ips:
			print i, "not monitored by nagios"
