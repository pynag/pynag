%{!?python_version: %define python_version %(%{__python} -c "from distutils.sysconfig import get_python_version; print get_python_version()")}
%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

%define is_suse %(test -e /etc/SuSE-release && echo 1 || echo 0)

Summary: Python Nagios plug-in and configuration environment
Name: pynag
Version: 0.4.1
Release: 1%{?dist}
Source0: http://pynag.googlecode.com/files/%{name}-%{version}.tar.gz
License: GPLv2
Group: System Environment/Libraries
Requires: python >= 2.3
BuildRequires: python-devel
%if 0%{?suse_version}
BuildRequires: gettext-devel
%else
%if 0%{?fedora} >= 13
BuildRequires: python-setuptools
%else
%if 0%{?fedora} >= 8
BuildRequires: python-setuptools-devel
%else
%if 0%{?rhel} >= 5
BuildRequires: python-setuptools
%endif
%endif
%endif
%endif
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Url: http://code.google.com/p/pynag/

%description
Pynag contains tools for pragmatically handling Nagios configuration
file maintenance and plug-in development.

%package examples
Group: System Environment/Libraries
Summary: Example scripts which manipulate Nagios configuration

%description examples
Example scripts which manipulate Nagios configuration files. Provided
are scripts which list services, do network discovery amongst others.


%prep
%setup -q

%build
%{__python} setup.py build
make manpage

%install
test "x$RPM_BUILD_ROOT" != "x" && rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install --prefix=/usr --root=$RPM_BUILD_ROOT
#mkdir -p $RPM_BUILD_ROOT/usr/share/pynag
install -m 755 -d $RPM_BUILD_ROOT/%{_datadir}/%{name}/examples
install -m 755 -d $RPM_BUILD_ROOT/%{_datadir}/%{name}/examples/Model
install -m 755 -d $RPM_BUILD_ROOT/%{_datadir}/%{name}/examples/Parsers
install -m 755 -d $RPM_BUILD_ROOT/%{_datadir}/%{name}/examples/Plugins
install -m 755 examples/README $RPM_BUILD_ROOT/%{_datadir}/%{name}/examples/
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
%dir %{python_sitelib}/pynag
%dir %{python_sitelib}/pynag/Control
%dir %{python_sitelib}/pynag/Model
%dir %{python_sitelib}/pynag/Model/EventHandlers
%dir %{python_sitelib}/pynag/Parsers
%dir %{python_sitelib}/pynag/Plugins
%{python_sitelib}/pynag/*.py*
%{python_sitelib}/pynag/Control/*.py*
%{python_sitelib}/pynag/Model/*.py*
%{python_sitelib}/pynag/Model/EventHandlers/*.py*
%{python_sitelib}/pynag/Parsers/*.py*
%{python_sitelib}/pynag/Plugins/*.py*
%{_bindir}/pynag-add_host_to_group
%{_bindir}/pynag-safe_restart
%doc AUTHORS README LICENSE CHANGES
%{_mandir}/man1/pynag-add_host_to_group.1.gz
%{_mandir}/man1/pynag-safe_restart.1.gz
%dir %{_datadir}/%{name}

%files examples
%defattr(-, root, root, -)
%dir %{_datadir}/%{name}/examples
%dir %{_datadir}/%{name}/examples/Model
%dir %{_datadir}/%{name}/examples/Parsers
%dir %{_datadir}/%{name}/examples/Plugins
%{_datadir}/%{name}/examples/README
%{_datadir}/%{name}/examples/Model/*
%{_datadir}/%{name}/examples/Parsers/*
%{_datadir}/%{name}/examples/Plugins/*
%doc AUTHORS README LICENSE CHANGES

%changelog
* Tue Mar 13 2012 Pall Sigurdsson <palli@opensource.is> 0.4.1-1
- make manpages added to pynag.spec (palli@opensource.is)
- make manpages added to pynag.spec (palli@opensource.is)

* Tue Mar 13 2012 Pall Sigurdsson <palli@opensource.is> 0.5-1
- new package built with tito

* Mon Jul  4 2011 Pall Sigurdsson <palli@opensource.is> - 0.4.0
- New upstream version
- Config refactoring
- New Model module

* Wed Apr 27 2011 Tomas Edwardsson <tommi@tommi.org> - 0.3-3
- Added examples package and moved example files there

* Fri Jan 26 2011 Tomas Edwardsson <tommi@tommi.org> - 0.3-2
- Fixes for spelling and some issues reported by rpmlint

* Fri Jan 22 2011 Tomas Edwardsson <tommi@tommi.org> - 0.3-1
- Initial RPM Creation, based heavily on the func spec file
