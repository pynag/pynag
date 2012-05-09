## setup.py ###
from distutils.core import setup

NAME = "pynag"
VERSION = '0.4'
SHORT_DESC = "%s - Python Nagios Extension" % NAME
LONG_DESC = """
%s contains tools for pragmatically handling configuration file maintenance a
nd plugin development.
""" % NAME

if __name__ == "__main__":
	manpath		= "share/man/man1/"
	etcpath = "/etc/%s" % NAME
	etcmodpath	= "/etc/%s/modules" % NAME
	initpath	= "/etc/init.d/"
	logpath		= "/var/log/%s/" % NAME
	varpath		= "/var/lib/%s/" % NAME
	rotpath		= "/etc/logrotate.d"
	setup(
		name='%s' % NAME,
		version = VERSION,
		author='Drew Stinnett',
		description = SHORT_DESC,
		long_description = LONG_DESC,
		author_email='drew@drewlink.com',
		url='http://code.google.com/p/pynag/',
		license='GPLv2',
		scripts = [
			'scripts/pynag-add_host_to_group',
			'scripts/pynag-safe_restart',
			'scripts/pynag-addservice',
			'scripts/pynag-maincfg',
			'scripts/pynag-sql'
		],
		packages = [
			'pynag',
			'pynag.Model',
			'pynag.Model.EventHandlers',
			'pynag.Plugins',
			'pynag.Parsers',
			'pynag.Control'
		],
      	data_files = [(manpath, [
			'docs/pynag-add_host_to_group.1',
			'docs/pynag-safe_restart.1',
		]),
		],
	)
