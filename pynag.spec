%if 0%{?rhel} <= 5
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_version: %global python_version %(%{__python} -c "from distutils.sysconfig import get_python_version; print get_python_version()")}
%endif

Summary: Python Modules for Nagios plugins and configuration
Name: pynag
Version: 0.4.2
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
Contains python modules for pragmatically handling Nagios
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
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install --prefix=/usr --root=$RPM_BUILD_ROOT
install -m 755 -d $RPM_BUILD_ROOT/%{_datadir}/%{name}/examples
install -m 755 -d $RPM_BUILD_ROOT/%{_datadir}/%{name}/examples/Model
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

%doc AUTHORS README LICENSE CHANGES
%dir %{_datadir}/%{name}

%files examples
%defattr(-, root, root, -)
%{_datadir}/%{name}/examples
%doc examples/README

%changelog
* Fri Jun 29 2012 Pall Sigurdsson <palli@opensource.is> 0.4.2-1
- pynag script added to spec file. Other scripts removed (palli@opensource.is)
- pynag script added to spec file (palli@opensource.is)
- confirmation prompt added to update subcommand (palli@opensource.is)
- pynag delete now asks for confirmation before deleting (palli@opensource.is)
- delete subcommand added to pynag (palli@opensource.is)
- pynag command line tool created. For easy way to list/update/add objects from
  command-line (palli@opensource.is)
- ObjectDefinition.copy() now returns a copy of the newly created object
  (palli@opensource.is)
- Bugfix where appending cfg_dir to nagios maincfg and pathnames dont match
  exactly what is in config before (for example double slashes would cause a
  duplicate) (palli@opensource.is)
- make sure cache is reloaded if manual edit has been made
  (palli@opensource.is)
- Change cache reload debug to print only when actual reparse happens
  (palli@opensource.is)
- ObjectDefinition.attributes are now defined according to documentation, no
  longer dynamically created in order to ensure consistency
  (palli@opensource.is)
- Feature: run_check_command() available for hosts and services
  (palli@opensource.is)
- no longer reloads cache as often (palli@opensource.is)
- Bugfix: Properly raise ParserError if unexpected '}' is encountered while
  Parsing (palli@opensource.is)
- ParserError class now has cleaner more detailed output (palli@opensource.is)
- get_all_macros() now also returns custom macros (palli@opensource.is)
- New Feature: Working with comma seperated attributevalues now easier
  (palli@opensource.is)
- Fixed key errors where data is not present (tommi@tommi.org)
- Merge branch 'master' of http://code.google.com/p/pynag (palli@opensource.is)
- improvements to reload_cache() to fix memory leak in save()
  (palli@opensource.is)
- invalidate_cache() removed (palli@opensource.is)
- copy() feature added. host/service dependencies added in string_to_class
  (palli@opensource.is)
- .gitignore file added (palli@opensource.is)
- Cleanup of spec, removed unneeded test condition (tommi@tommi.org)
- Merge branch 'master' of http://code.google.com/p/pynag (palli@opensource.is)
- --set attribute added (palli@opensource.is)
- eclipse suggested codefixes, unused variables, etc (palli@opensource.is)
- Updated build and added manpages for new scripts (tommi@tommi.org)
- Updated versioning and some more license cleanups (tommi@tommi.org)
- Updated license information (tommi@tommi.org)
- Cleanup to build process (tommi@tommi.org)
- Added changes from 0.4 (tommi@tommi.org)
- Clarified licensing issues, GPLv2. (tommi@tommi.org)
- Removed main function from library (tommi@tommi.org)
- Simplified spec file, threw out lots of legacy conditionals (tommi@tommi.org)
- Added Makefile to MANIFEST, should be included in the release.
  (tommi@tommi.org)
- Simple build instructions added to README (tommi@tommi.org)
- Added Host and ServiceDependency objects and parser functionality.
  (tommi@tommi.org)
- pynag.spec conditions added for fedora 13+ (palli@opensource.is)
- updated releasers to use tito as username (palli@opensource.is)

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
