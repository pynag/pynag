%if 0%{?rhel} <= 5
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_version: %global python_version %(%{__python} -c "from distutils.sysconfig import get_python_version; print get_python_version()")}
%endif

# RHEL6 and newer has unittest2
# All other distributions assume that we have access to unittest2
%define unittest2 0
%if 0%{?rhel} 
%if 0%{?rhel} >= 6
%define unittest2 1
%endif
%else
%define unittest2 1
%endif

%define release 1


Summary: Python modules and utilities for Nagios plugins and configuration
Name: pynag
Version: 0.8.3
Release: %{release}%{?dist}
Source0: http://pynag.googlecode.com/files/%{name}-%{version}.tar.gz
License: GPLv2
Group: System Environment/Libraries
BuildRequires: python-devel
BuildRequires: python-setuptools
BuildRoot: %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
Url: http://pynag.org/
BuildArch: noarch
%if 0%{?unittest2}
BuildRequires: python-unittest2
%endif

%description
Python modules and utilities for pragmatically handling Nagios configuration
file maintenance, status information, log file parsing and plug-in
development.

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

%if 0%{?unittest2}
%{__python} setup.py test
%endif

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
* Wed Aug 30 2013 Pall Sigurdsson <palli@opensource.is> 0.6.1-1
- New upstream version

* Tue Apr 30 2013 Tomas Edwardsson <tommi@tommi.org> 0.4.9-1
- New upstream version

* Wed Dec 12 2012 Pall Sigurdsson <palli@opensource.is> 0.4.8-1
- New upstream version

* Tue Aug 21 2012 Pall Sigurdsson <palli@opensource.is> 0.4.5-1
- New upstream version

* Fri Aug 17 2012 Pall Sigurdsson <palli@opensource.is> 0.4.4-1
- New upstream version

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
