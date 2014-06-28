#!/usr/bin/python
#
# This script will autogenerate python functions to communicate with the python command file.
# input to the program is the documentation from nagios

import BeautifulSoup
import sys
import textwrap

for filename in sys.argv[1:]:
    html = open(filename).read()

    soup = BeautifulSoup.BeautifulSoup(html, convertEntities='html')

    # First get the command format we need:
    tmp = soup.find('td', {'class': 'MediumBold'})
    command_format = tmp.findNext().getText()

    # command_format should look something like this:
    # u'ENABLE_SVC_EVENT_HANDLER;&lt;host_name&gt;;&lt;service_description&gt;'

    # there is a bug in the documentation, where one semicolon is missing, lets adjust:
    command_format = command_format.replace('><', '>;<')
    command_format = command_format.replace('service_desription', 'service_description')

    command_format = command_format.replace('<', '',).replace('>', '')
    command_format = command_format.split(';')
    func = command_format[0]
    # Lets convert function name to lowercase to be polite
    args = command_format[1:]

    # Now we have the command format, lets find the description text
    description = tmp.findParent().findNextSibling().findNextSibling().findNextSibling().findNextSibling().getText()

    # Let's PEP8 the description
    wrapper = textwrap.TextWrapper()
    wrapper.initial_indent = '    '
    wrapper.subsequent_indent = '    '
    wrapper.width = 68
    description = '\n'.join(['\n'.join(wrapper.wrap(block)) for block in description.splitlines()])

    strFunction = """

def {function_name_lower}(
    {arguments}
):
    \"\"\"
{description}
    \"\"\"
    return send_command("{function_name}",
                        command_file,
                        timestamp,
                        {function_arguments_linebroken})"""
    args.extend(['command_file=None', 'timestamp=0'])
    defSpaces = ' ' * (5 + len(func))
    returnSpaces = ' ' * 24
    argSplitter = ',\n    '
    strFunction = strFunction.format(
        function_name_lower=func.lower(),
        arguments=argSplitter.join(args),
        description=description,
        function_name=func,
        function_arguments_linebroken=',\n                        '.join(args[0:-2])
    )
    strFunction = strFunction.replace('(, ', '(')
    print strFunction
