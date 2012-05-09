%if 0%{?rhel} <= 5
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_version: %global python_version %(%{__python} -c "from distutils.sysconfig import get_python_version; print get_python_version()")}
%endif

Summary: Python Nagios plug-in and configuration environment
Name: pynag
Version: 0.4.1
Release: 5%{?dist}
Source0: http://pynag.googlecode.com/files/%{name}-%{version}.tar.gz
License: GPLv2
Group: System Environment/Libraries
BuildRequires: python-devel
BuildRequires: python-setuptools
BuildRoot: %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
Url: http://code.google.com/p/pynag/
BuildArch: noarch

%description
Pynag contains tools for pragmatically handling Nagios configuration
file maintenance and plug-in development.

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
%{_bindir}/pynag-add_host_to_group
%{_bindir}/pynag-safe_restart
%{_bindir}/pynag-addservice
%{_bindir}/pynag-maincfg
%{_bindir}/pynag-sql

%doc AUTHORS README LICENSE CHANGES
%{_mandir}/man1/pynag-add_host_to_group.1.gz
%{_mandir}/man1/pynag-safe_restart.1.gz
%dir %{_datadir}/%{name}

%files examples
%defattr(-, root, root, -)
%{_datadir}/%{name}/examples
%doc examples/README

%changelog
* Tue Apr 17 2012 Tomas Edwardsson <tommi@tommi.org> 0.4.1-5
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
