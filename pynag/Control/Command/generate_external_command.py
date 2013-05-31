#!/usr/bin/python
#
# This script will autogenerate python functions to communicate with the python command file.
# input to the program is the documentation from nagios

import BeautifulSoup
import sys
import textwrap

for filename in sys.argv[1:]:
    html = open(filename).read()

    soup = BeautifulSoup.BeautifulSoup(html,  convertEntities='html')

    # First get the command format we need:
    tmp = soup.find('td', {'class':'MediumBold'})
    command_format = tmp.findNext().getText()

    # command_format should look something like this:
    # u'ENABLE_SVC_EVENT_HANDLER;&lt;host_name&gt;;&lt;service_description&gt;'

    # there is a bug in the documentation, where one semicolon is missing, lets adjust:
    command_format = command_format.replace('><','>;<')
    command_format = command_format.replace('service_desription','service_description')
    

    command_format = command_format.replace('<', '',).replace('>','')
    command_format = command_format.split(';')
    func = command_format[0]
    # Lets convert function name to lowercase to be polite
    args = command_format[1:]


    # Now we have the command format, lets find the description text
    description = tmp.findParent().findNextSibling().findNextSibling().findNextSibling().findNextSibling().getText()
    
    # Let's PEP8 the description
    wrapper = textwrap.TextWrapper()
    wrapper.subsequent_indent = '    '
    wrapper.width = 68
    description = '\n'.join(['\n'.join(wrapper.wrap(block)) for block in description.splitlines()])


    strFunction = """
def %s(%s,command_file=None,timestamp=0):
    \"\"\"
    %s
    \"\"\"
    return send_command("%s",command_file,timestamp, %s)"""
    strFunction = strFunction % (func.lower(), ','.join(args), description, func, ','.join(args))
    strFunction = strFunction.replace('(,','(')
    print strFunction
