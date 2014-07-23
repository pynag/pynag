VERSION		= 0.9.0
RELEASE		= 1
DATE		= $(shell date)
NEWRELEASE	= $(shell echo $$(($(RELEASE) + 1)))
PYTHON		= /usr/bin/python

TOPDIR = $(shell pwd)
DIRS	= build docs contrib etc examples pynag scripts debian.upstream
PYDIRS	= pynag scripts examples debian 
EXAMPLEDIR = examples
MANPAGES = pynag

all: rpms

versionfile:
	echo "version:" $(VERSION) > etc/version
	echo "release:" $(RELEASE) >> etc/version
	echo "source build date:" $(DATE) >> etc/version

build: clean
	$(PYTHON) setup.py build -f

clean:
	-rm -f  MANIFEST
	-rm -rf dist/ build/
	-rm -rf *~
	-rm -rf rpm-build/
	-rm -rf deb-build/
	-rm -rf docs/*.1
	-rm -f etc/version

clean_hard:
	-rm -rf $(shell $(PYTHON) -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")/pynag 


clean_hardest: clean_rpms


install: build
	$(PYTHON) setup.py install -f

install_hard: clean_hard install

install_harder: clean_harder install

install_hardest: clean_harder clean_rpms rpms install_rpm 

install_rpm:
	-rpm -Uvh rpm-build/pynag-$(VERSION)-$(NEWRELEASE)$(shell rpm -E "%{?dist}").noarch.rpm


recombuild: install_harder 

clean_rpms:
	-rpm -e pynag

sdist: 
	$(PYTHON) setup.py sdist

pychecker:
	-for d in $(PYDIRS); do ($(MAKE) -C $$d pychecker ); done   
pyflakes:
	-for d in $(PYDIRS); do ($(MAKE) -C $$d pyflakes ); done	

money: clean
	-sloccount --addlang "makefile" $(TOPDIR) $(PYDIRS) $(EXAMPLEDIR) 

testit: clean
	-cd test; sh test-it.sh

unittest:
	-nosetests -v -w test/unittest

rpms: build sdist
	mkdir -p rpm-build
	cp dist/*.gz rpm-build/
	rpmbuild --define "_topdir %(pwd)/rpm-build" \
	--define "_builddir %{_topdir}" \
	--define "_rpmdir %{_topdir}" \
	--define "_srcrpmdir %{_topdir}" \
	--define '_rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm' \
	--define "_specdir %{_topdir}" \
	--define "_sourcedir  %{_topdir}" \
	-ba pynag.spec
debs: build sdist
	mkdir -p deb-build
	cp dist/*gz deb-build/pynag_${VERSION}.orig.tar.gz
	cd deb-build/ ; \
	  tar -zxvf pynag_${VERSION}.orig.tar.gz ; \
	  cd pynag-${VERSION} ;\
	  cp -r debian.upstream debian ;\
	  debuild
