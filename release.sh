#!/bin/sh
# Use this script to release a new version of pynag


# Extract current version information
current_version=$(grep ^Version: pynag.spec | awk '{ print $2 }')
current_release=$(grep "define release" pynag.spec | awk '{ print $3 }')

# Edit CHANGES
echo -n "### Update CHANGES? [yN] "
read update_changes
if [[ $update_changes =~ ^y.* ]]; then
    ${EDITOR} CHANGES
fi

# pypi upload?
echo -n "### Upload to pypi [Yn] "
read pypy_upload
if ! [[ $pypy_upload =~ ^n.* ]]; then
    pypy_upload=1
else
    pypy_upload=0
fi

# git-autopush 
echo -n "### Push to github [Yn] "
read git_autopush
if ! [[ $git_autopush =~ ^n.* ]]; then
    git_autopush=1
else
    git_autopush=0
fi

# debian-version
echo -n "### Update debian version [Yn] "
read debian_version
if ! [[ $debian_version =~ ^n.* ]]; then
    debian_version=1
else
    debian_version=0
fi

# Optionally submit to freecode
echo -n "### Submit release to freecode? [Yn] "
read freecode_submit
if ! [[ $freecode_submit =~ ^n ]]; then
    error=0
    which freecode-submit &> /dev/null || error=1
    grep freecode ~/.netrc &> /dev/null || error=1
    
    if [ $error -gt 0 ]; then
    cat <<EO && exit
freecode-submit missing, please install and update .netrc appropriately

  use yum install freecode-submit or equivilent for your distribution

Next you have to find your API key on freecode.com and put it into ~/.netrc

  echo "machine freecode account <apikey> password none" >> ~/.netrc

Done
EO
        exit 1
    fi
    freecode_submit=1
else
    freecode_submit=0
fi


UPDATE_INFO_FILE=$(mktemp)

cat <<EO > ${UPDATE_INFO_FILE}
Current version is: $current_version
New version number: 
Summary: <one line summary>

<full description>
EO

# Edit the update template file
${EDITOR} ${UPDATE_INFO_FILE}

new_version=$(grep '^New version number:' ${UPDATE_INFO_FILE} | \
	sed 's/^New version number: *//')
short_desc=$(grep '^Summary:' ${UPDATE_INFO_FILE} | \
	sed 's/^Summary: *//')


# Some sanity checking
if [ -z "${new_version}" ]; then
    echo "New version is required"
    exit 1
fi
if [ -z "${short_desc}" ]; then
    echo "Summary is required"
    exit 1
fi

# Create the freecode-submit update file
if [[ $freecode_submit == 1 ]]; then
    freecode_file=$(mktemp)
    cat << EO > ${freecode_file}
Project: pynag
Version: ${new_version}
Hide: N
Website-URL: http://pynag.org/
Tar/GZ-URL: https://pypi.python.org/packages/source/p/pynag/pynag-${new_version}.tar.gz
EO
    grep -A24 '^$' ${UPDATE_INFO_FILE} >> ${freecode_file}
fi

rm -f ${UPDATE_INFO_FILE}

echo "### Updating Makefile"
sed -i "s/^VERSION.*= ${current_version}/VERSION		= ${new_version}/" Makefile
echo "### Updating pynag/__init__.py"
sed -i "s/^__version__ =.*/__version__ = '${new_version}'/" pynag/__init__.py
echo "### Updating pynag.spec"
sed -i "s/^Version: ${current_version}/Version: ${new_version}/" pynag.spec
echo "### Updating rel-eng/packages/pynag"
echo "${new_version}-${current_release} /" > rel-eng/packages/pynag


if [[ $debian_version == 1 ]]; then
    echo "### Updating debian version"
    dch -v "${new_version}" --distribution unstable "New Upstream release"
fi

echo "### commiting and tagging current git repo"
git commit Makefile pynag/__init__.py rel-eng/packages/pynag pynag.spec debian.upstream/changelog -m "Bumped version number to $new_version" > /dev/null
git tag pynag-${new_version}-${current_release} -a -m "Bumped version number to $new_version" 

# The following 2 require access to git repositories and pypi
if [[ $git_autopush == 1 ]]; then
    echo "### Pushing commit to github"
    git push origin master || exit 1
    git push --tags origin master || exit 1
fi

if [[ $pypy_upload == 1 ]]; then
    echo "### Building package and uploading to pypi"
    python setup.py build sdist upload || exit 1
fi

if [[ $freecode_submit == 1 ]]; then
    echo "### Submit version to freecode"
    freecode-submit < ${freecode_file}
    rm -f ${freecode_file}
fi

echo "### DONE ###"

# vim: sts=4 expandtab autoindent
