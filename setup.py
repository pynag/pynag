## setup.py ###
from distutils.core import setup

setup (name='PyNag',
      version='0.2',
      description='Python-Nagios Extension',
      author='Drew Stinnett',
      author_email='drew@drewlink.com',
      url='http://code.google.com/p/pynag/',
      license='GPL',
	  
      packages=['pynag','pynag.NObject','pynag.Plugins','pynag.Parsers','pynag.Control'],
	scripts = ['scripts/pynag-add_host_to_group.py', 'scripts/pynag-safe_restart.py'],

)
