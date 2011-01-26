%{!?python_version: %define python_version %(%{__python} -c "from distutils.sysconfig import get_python_version; print get_python_version()")}
%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

%define is_suse %(test -e /etc/SuSE-release && echo 1 || echo 0)

Summary: Python Nagios plug-in and configuration environment
Name: pynag
Version: 0.3
Release: 2%{?dist}
Source0: http://pynag.googlecode.com/files/%{name}-%{version}.tar.gz
License: GPLv2
Group: System Environment/Libraries
Requires: python >= 2.3
BuildRequires: python-devel
%if %is_suse
BuildRequires: gettext-devel
%else
%if 0%{?fedora} >= 8
BuildRequires: python-setuptools-devel
%else
%if 0%{?rhel} >= 5
BuildRequires: python-setuptools
%endif
%endif
%endif
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildArch: noarch
Url: http://code.google.com/p/pynag/

%description
Pynag contains tools for pragmatically handling Nagios configuration
file maintenance and plug-in development.

%prep
%setup -q

%build
%{__python} setup.py build

%install
test "x$RPM_BUILD_ROOT" != "x" && rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install --prefix=/usr --root=$RPM_BUILD_ROOT

%clean
rm -fr $RPM_BUILD_ROOT

%files
%defattr(-, root, root, -)
%if "%{python_version}" >= "2.5"
%{python_sitelib}/pynag*.egg-info
%endif
%dir %{python_sitelib}/pynag
%dir %{python_sitelib}/pynag/Control
%dir %{python_sitelib}/pynag/NObject
%dir %{python_sitelib}/pynag/Parsers
%dir %{python_sitelib}/pynag/Plugins
%{python_sitelib}/pynag/*.py*
%{python_sitelib}/pynag/Control/*.py*
%{python_sitelib}/pynag/NObject/*.py*
%{python_sitelib}/pynag/Parsers/*.py*
%{python_sitelib}/pynag/Plugins/*.py*
%{_bindir}/pynag-add_host_to_group
%{_bindir}/pynag-safe_restart
%doc AUTHORS README LICENSE CHANGES examples
%{_mandir}/man1/pynag-add_host_to_group.1.gz
%{_mandir}/man1/pynag-safe_restart.1.gz

%changelog
* Fri Jan 26 2011 Tomas Edwardsson <tommi@tommi.org> - 0.3-2
- Fixes for spelling and some issues reported by rpmlint

* Fri Jan 22 2011 Tomas Edwardsson <tommi@tommi.org> - 0.3-1
- Initial RPM Creation, based heavily on the func spec file
