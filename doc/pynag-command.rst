
====
NAME
====

SYNOPSIS
--------
pynag <sub-command> [options] [arguments]

DESCRIPTION
-----------
pynag is a command-line utility that can be used to view or change current
nagios configuration.

sub-commands
------------

*list*
   
   print to screen nagios configuration objects as specified by a WHERE
   clause
   
      | pynag list [attribute1] [attribute2] [WHERE ...]

*update*
   
   modify specific attributes of nagios objects as specified by a WHERE
   and SET clause
    
      | pynag update set attr1=value WHERE attr=value and attr=value

*delete*
   
   Delete objects from nagios configuration as specified by a WHERE clause

      | pynag delete delete <WHERE ...>

*add*

   Add a new object definition

      | pynag add <object_type> <attr1=value1> [attr2=value2]

*copy*

   Copy objects, specifiying which attributes to change

      | pynag copy <WHERE ...> <SET attr1=value1 [attr2=value2] ...>

*execute*

   Executes the currently configured check command for a host or a service

      | pynag execute <host_name> [service_description]

*config*

   modify values in main nagios configuration file (nagios.cfg)

      | pynag config [--set <attribute=value>] [--old_value=attribute]
      | pynag config [--append <attribute=value>] [--old_value=attribute]
      | pynag config [--remove <attribute>] [--old_value=attribute]
      | pynag config [--get <attribute>]

WHERE statements
----------------
Some Subcommands use WHERE statements to filter which objects to work
with.  Where has certain similarity with SQL syntax.

Syntax:
   | WHERE <attr=value> [AND attr=value] [OR attr=value] \
   |   [another where statement]

   where "attr" is any nagios attribute (i.e. host_name or 
   service_description).

Example:
   | pynag list WHERE host_name=localhost and object_type=service
   | pynag list WHERE object_type=host or object_type=service

Any search attributes have the same syntax as the pynag filter. For example
these work just fine:

   | pynag list WHERE host_name__contains=production
   | pynag list WHERE host_name__startswith=prod
   | pynag list WHERE host_name__notcontains=test
   | pynag list host_name address WHERE address__exists=True
   | pynag list host_name WHERE register__isnot=0

The pynag filter supports few parameters that are not just attributes.

Example:

* filename                 -- The filename which the object belongs
* id                       -- pynag unique identifier for the object
* effective_command_line   -- command which nagios will execute

Of course these can be combined with the pynag filter syntax:

   | pynag list where filename__startswith=/etc/nagios/conf.d/
   | pynag list host_name service_description effective_command_line

For detailed description of the filter see pydoc for
pynag.Model.ObjectDefintion.filter()

SET statements
--------------
Subcommands that use SET statements (like update or copy) use them a list of
attributes change for a specific object.

Syntax:
   | SET <attr1=value1> [attr2=value2] [...]

Example:
   | pynag update SET address=127.0.0.1 WHERE host_name=localhost and object_type=host

EXAMPLES
--------
List all services that have "myhost" as a host_name
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
| pynag list host_name service_description WHERE host_name=myhost and object_type=service

Set check_period to 24x7 on all services that belong to host "myhost"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
| pynag update set check_period=24x7 WHERE host_name=myhost

list examples
^^^^^^^^^^^^^
| pynag list host_name address WHERE object_type=host
| pynag list host_name service_description WHERE host_name=examplehost and object_type=service


update examples
^^^^^^^^^^^^^^^
| pynag update SET host_name=newhostname WHERE host_name=oldhostname
| pynag update SET address=127.0.0.1 WHERE host_name='examplehost.example.com' and object_type=host

copy examples
^^^^^^^^^^^^^
| pynag copy SET host_name=newhostname WHERE  host_name=oldhostname
| pynag copy SET address=127.0.0.1 WHERE host_name='examplehost.example.com' and object_type=host

add examples
^^^^^^^^^^^^
| pynag add host host_name=examplehost use=generic-host address=127.0.0.1
| pynag add service service_description="Test Service" use="check_nrpe" host_name="localhost"

delete examples
^^^^^^^^^^^^^^^
| pynag delete where object_type=service and host_name='mydeprecated_host'
| pynag delete where filename__startswith='/etc/nagios/myoldhosts'

execute examples
^^^^^^^^^^^^^^^^
| pynag execute localhost
| pynag execute localhost "Disk Space


Additional Resources
--------------------
See http://github.com/pynag/pynag.git for more information.


