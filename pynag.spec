%if 0%{?rhel} <= 5
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_version: %global python_version %(%{__python} -c "from distutils.sysconfig import get_python_version; print get_python_version()")}
%endif

Summary: Python modules and utilities for Nagios plugins and configuration
Name: pynag
Version: 0.4.5
Release: 1%{?dist}
Source0: http://pynag.googlecode.com/files/%{name}-%{version}.tar.gz
License: GPLv2
Group: System Environment/Libraries
BuildRequires: python-devel
BuildRequires: python-setuptools
BuildRoot: %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
Url: http://code.google.com/p/pynag/
BuildArch: noarch

%description
Contains python modules and utilities for pragmatically handling Nagios
configuration file maintenance and plug-in development.

%package examples
Group: System Environment/Libraries
Summary: Example scripts which manipulate Nagios configuration
Requires: pynag

%description examples
Example scripts which manipulate Nagios configuration files. Provided
are scripts which list services, do network discovery among other tasks.

%prep
%setup -q

%build
%{__python} setup.py build

%install
test "x$RPM_BUILD_ROOT" != "x" && rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install --prefix=/usr --root=$RPM_BUILD_ROOT
install -m 755 -d $RPM_BUILD_ROOT/%{_datadir}/%{name}/examples
install -m 755 -d $RPM_BUILD_ROOT/%{_datadir}/%{name}/examples/Model
install -m 755 -d $RPM_BUILD_ROOT/%{_datadir}/%{name}/examples/Utils
install -m 755 -d $RPM_BUILD_ROOT/%{_datadir}/%{name}/examples/Parsers
install -m 755 -d $RPM_BUILD_ROOT/%{_datadir}/%{name}/examples/Plugins
install -m 755 examples/Model/* $RPM_BUILD_ROOT/%{_datadir}/%{name}/examples/Model/
install -m 755 examples/Parsers/* $RPM_BUILD_ROOT/%{_datadir}/%{name}/examples/Parsers/
install -m 755 examples/Plugins/* $RPM_BUILD_ROOT/%{_datadir}/%{name}/examples/Plugins/


%clean
rm -fr $RPM_BUILD_ROOT

%files
%defattr(-, root, root, -)
%if "%{python_version}" >= "2.5"
%{python_sitelib}/pynag*.egg-info
%endif
%{python_sitelib}/pynag/
%{_bindir}/pynag
%{_mandir}/man1/pynag.1.gz

%doc AUTHORS README.md LICENSE CHANGES
%dir %{_datadir}/%{name}

%files examples
%defattr(-, root, root, -)
%{_datadir}/%{name}/examples
%doc examples/README

%changelog
* Tue Aug 21 2012 Pall Sigurdsson <palli@opensource.is> 0.4.5-1
- Changelog updated (palli@opensource.is)
- debian subdir renamed to debian.upstream (palli@opensource.is)
- Version number bumped to 0.4.5 (palli@opensource.is)
- Merge branch 'master' of github.com:pynag/pynag (palli@opensource.is)
- popen2 import moved to send_nsca() to hide deprecationwarning
  (palli@opensource.is)
- pynag.Model no longer depends on defaultdict to work (palli@opensource.is)
- Updates to pynag.Parsers.status (palli@opensource.is)

* Fri Aug 17 2012 Pall Sigurdsson <palli@opensource.is> 0.4.4-1
- Fix unhandled exception  in Parsers.need_reparse() (palli@opensource.is)
- Fix issues with giteventhandler and objectrelations (palli@opensource.is)
- Improved errorhandling on giteventhandler. author is updated before any git
  add is called (palli@opensource.is)
- get_all_macros returns empty hash map on non-existant check_command
  (palli@opensource.is)
- EventHandler improvements. (palli@opensource.is)
- get_effective_check_command() function added. pynag script now supports
  execute subcommand (palli@opensource.is)
- defaultdict added back. error handling in get_macro (palli@opensource.is)
- Temporary re-implementation of defaultdict (palli@opensource.is)
- Added reference to changed README(.md) filename (tommi@tommi.org)
- GitEventhandler escaping for commit message fixed (palli@opensource.is)
- improved error handling in giteventhandler. better default pynag write
  directory (palli@opensource.is)
- GitEventHandler updated to use subprocess instead of dulwich
  (palli@opensource.is)
- ObjectDefinition.get_id() changed from md5sum to built-in __hash__()
  (palli@opensource.is)
- Host.copy() now recursively copies services (palli@opensource.is)
- Fixes to get_effective_command_line() where macro within another macro was
  not properly solved. (palli@opensource.is)
- Added comment on attribute generation (tommi@tommi.org)
- Added parser for configmain.html for all_attributes (tommi@tommi.org)
- Merge branch 'master' of github.com:pynag/pynag (tommi@tommi.org)
- Added maincfg fields to all_attributes (tommi@tommi.org)
- README syntax fix (palli@opensource.is)
- README syntax fix (palli@opensource.is)
- README syntax fix (palli@opensource.is)
- README moved to markdown format (palli@opensource.is)
- README Updated (palli@opensource.is)
- Bugfix, when Objectdefinition.filter was called with None passed to a
  *__contains argument (palli@opensource.is)
- giteventhandler changed to use dulwich module instead of gitpython
  (palli@opensource.is)
- Merge github.com:pynag/pynag (palli@opensource.is)
- Big improvements to Parsers.status; minor refactoring in Parsers.config
  (palli@opensource.is)
- Merge branch 'master' of https://code.google.com/p/pynag (tommi@tommi.org)
- fixes #3 status[] variable was reset per line (tommi@tommi.org)
- Remove trailing slash from pynag_dir. get_suggested_filename() now produces
  correct pathnames. (er.abhinav.upadhyay@gmail.com)
- print statements removed from parsers library functions (palli@opensource.is)
- Moved to parse instead of extended_parse (tommi@tommi.org)
- Removed static arguments to get_service (tommi@tommi.org)
- Removed import os and fixed find_orphans (tommi@tommi.org)
- Removed unused module os by Abhinav Upadhyay. (tommi@tommi.org)
- Timeperiod hack +permission fix for resource.cfg (palli@opensource.is)
- check_thresholds() added (Issue 22) (palli@opensource.is)
- check_range() rewritten and stuffed outside simple module (Fixes issue 22)
  (palli@opensource.is)
- Missing Objectrelations between servicegroup_services added
  (palli@opensource.is)
- fixed which causes traceback on parsererror (palli@opensource.is)
- All Tabs converted to spaces. Started to enforce PEP8 line spacing
  (palli@opensource.is)
- /usr/local/nagios/etc/ added to paths where nagios.cfg might be found (Thanks
  Abhinav Upadhyay) (palli@opensource.is)
- More optimizations from pycharm inspections (palli@opensource.is)
- filter() now supports __exists suffix for as a search condition
  (palli@opensource.is)
- pycharm code inspection cleanup (palli@opensource.is)
- Major rework og object relations and object cache (palli@opensource.is)

* Mon Jul 23 2012 Tomas Edwardsson <tommi@tommi.org> 0.4.3-1
- New upstream version

* Fri Jun 29 2012 Pall Sigurdsson <palli@opensource.is> 0.4.2-1
- pynag script added to spec file. Other scripts removed (palli@opensource.is)

* Tue May  9 2012 Tomas Edwardsson <tommi@tommi.org> 0.4.1-6
- Simplified spec file, threw out lots of legacy conditionals
- Added Requires parent for pynag-examples

* Mon Jul  4 2011 Pall Sigurdsson <palli@opensource.is> - 0.4-1
- New upstream version
- Config refactoring
- New Model module

* Wed Apr 27 2011 Tomas Edwardsson <tommi@tommi.org> - 0.3-3
- Added examples package and moved example files there

* Fri Jan 26 2011 Tomas Edwardsson <tommi@tommi.org> - 0.3-2
- Fixes for spelling and some issues reported by rpmlint

* Fri Jan 22 2011 Tomas Edwardsson <tommi@tommi.org> - 0.3-1
- Initial RPM Creation, based heavily on the func spec file
