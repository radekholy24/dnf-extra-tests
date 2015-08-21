# -*- coding: utf-8 -*-
#
# Copyright 2015 dnf-extra-tests Authors. See the AUTHORS file found
# in the top-level directory of this distribution and at
# https://github.com/rholy/dnf-extra-tests/.
#
# Licensed under the GNU General Public License;
# either version 2, or (at your option) any later version. See the
# LICENSE file found in the top-level directory of this distribution
# and at https://github.com/rholy/dnf-extra-tests/. No part of
# dnf-extra-tests, including this file, may be copied, modified,
# propagated, or distributed except according to the terms contained
# in the LICENSE file.

"""This module implements the feature steps.

:var RESOURCESDN: a name of the directory containing testing resources
:type RESOURCESDN: str
:var REPODN: name of a testing repository directory
:type REPODN: str
:var GPGKEYFN: a name of an armored public GPG key which can be used to
   verify the signed package in the testing repository
:type GPGKEYFN: str
:var GPGKEYID: the short ID of the GPG key
:type GPGKEYID: unicode

"""


from __future__ import absolute_import
from __future__ import unicode_literals

import contextlib
import errno
import os
import re
import shutil
import subprocess
import tempfile
import urllib
import urlparse

import behave
import createrepo_c
import dnf.rpm


RESOURCESDN = os.path.join(
    os.path.dirname(__file__), os.path.pardir, b'resources')

REPODN = os.path.join(RESOURCESDN, b'repository')

GPGKEYFN = os.path.join(RESOURCESDN, b'TEST-GPG-KEY')

GPGKEYID = '867B843D'


@contextlib.contextmanager
def _suppress_enoent():
    """Create a context manager which blocks propagation of ENOENTs.

    :returns: the context manager
    :rtype: contextmanager

    """
    try:
        yield
    except OSError as err:
        if err.errno != errno.ENOENT:
            raise


def _makedirs(name, exist_ok=False):
    """Create a directory recusively.

    :param name: name of the directory
    :type name: unicode
    :param exist_ok: don't fail if the directory already exists
    :type exist_ok: bool
    :raises exceptions.OSError: if the directory cannot be created

    """
    try:
        os.makedirs(name)
    except OSError as err:
        if \
                not exist_ok or \
                err.errno != errno.EEXIST or not os.path.isdir(name):
            raise


def _path2url(path):
    """Convert a file path to an URL.

    :param path: the path
    :type path: str
    :returns: the URL
    :rtype: str

    """
    return urlparse.urlunsplit(
        (b'file', b'', urllib.pathname2url(path), b'', b''))


@contextlib.contextmanager
def _temp_repo_config(baseurl, gpgcheck=None):
    """Temporarily configure a repository.

    The "dnf" executable must be available.

    :param baseurl: a base URL of the repository
    :type baseurl: str
    :param gpgcheck: a value of the gpgcheck option
    :type gpgcheck: bool | None
    :returns: a context manager yielding ID of the repository
    :rtype: contextmanager[unicode]
    :raises exceptions.OSError: if the repository cannot be configured
       or if the executable cannot be executed
    :raises exceptions.IOError: if the repository cannot be configured

    """
    repoid = 'dnf-extra-tests'
    with dnf.Base() as base:
        configdn = base.conf.reposdir[0]
    _makedirs(configdn, exist_ok=True)
    conffile = tempfile.NamedTemporaryFile('wt', suffix='.repo', dir=configdn)
    with conffile:
        conffile.write(
            b'[{}]\n'
            b'baseurl={}\n'
            b'metadata_expire=never\n'
            .format(repoid.encode('utf-8'), baseurl))
        if gpgcheck is not None:
            conffile.write(b'gpgcheck={}\n'.format(
                gpgcheck and b'true' or b'false'))
        conffile.flush()
        try:
            yield repoid
        finally:
            subprocess.call([
                'dnf', '--quiet', '--disablerepo=*',
                '--enablerepo={}'.format(repoid), 'clean', 'metadata'])


def _run_rpm(args, root=None, quiet=False):
    """Run RPM from command line.

    The "rpm" executable must be available.

    :param args: additional command line arguments
    :type args: list[unicode]
    :param root: a value of the --root option
    :type root: unicode | None
    :param quiet: set the --quiet option
    :type quiet: bool
    :raises exceptions.OSError: if the executable cannot be executed
    :raises subprocess.CalledProcessError: if executable fails

    """
    cmdline = ['rpm'] + args
    if root:
        cmdline.insert(1, root)
        cmdline.insert(1, '--root')
    if quiet:
        cmdline.insert(1, '--quiet')
    subprocess.check_call(cmdline)


def _run_dnf(args, root=None, releasever=None, quiet=False, assumeyes=False):
    """Run DNF from command line.

    The "dnf" executable must be available.

    :param args: additional command line arguments
    :type args: list[unicode]
    :param assumeyes: set the --assumeyes option
    :type assumeyes: bool
    :param root: a value of the --installroot option
    :type root: unicode | None
    :param releasever: a value of the --releasever option
    :type releasever: unicode | None
    :param quiet: set the --queit option
    :type quiet: bool
    :returns: the output of the command
    :rtype: str
    :raises exceptions.OSError: if the executable cannot be executed
    :raises subprocess.CalledProcessError: if executable fails

    """
    cmdline = ['dnf'] + args
    if releasever:
        cmdline.insert(1, '--releasever={}'.format(releasever))
    if quiet:
        cmdline.insert(1, '--quiet')
    if root:
        cmdline.insert(1, '--installroot={}'.format(root))
    if assumeyes:
        cmdline.insert(1, '--assumeyes')
    return subprocess.check_output(cmdline)


def _run_dnf_install(
        specs, root=None, releasever=None, quiet=False, assumeyes=False):
    """Run DNF's install command from command line.

    The "dnf" executable must be available.

    :param specs: specifications of the packages to be installed
    :type specs: list[unicode]
    :param root: a value of the --installroot option
    :type root: unicode | None
    :param releasever: a value of the --releasever option
    :type releasever: unicode | None
    :param quiet: set the --queit option
    :type quiet: bool
    :param assumeyes: set the --assumeyes option
    :type assumeyes: bool
    :returns: the output of the command
    :rtype: str
    :raises exceptions.OSError: if the executable cannot be executed
    :raises subprocess.CalledProcessError: if executable fails

    """
    return _run_dnf(['install'] + specs, root, releasever, quiet, assumeyes)


def _run_repoquery(repo=None, root=None, releasever=None, quiet=False):
    """Run the DNF's repoquery plugin from command line.

    The "dnf" executable and its "repoquery" plugin must be available.

    :param repo: a value of the --repo option
    :type repo: unicode | None
    :param root: a value of the --installroot option
    :type root: unicode | None
    :param releasever: a value of the --releasever option
    :type releasever: unicode | None
    :param quiet: set the --queit option
    :type quiet: bool
    :returns: the output of the command
    :rtype: str
    :raises exceptions.OSError: if the executable cannot be executed
    :raises subprocess.CalledProcessError: if executable or the plugin
       fails

    """
    args = ['repoquery']
    if repo:
        args.insert(1, repo)
        args.insert(1, '--repoid')
    return _run_dnf(args, root, releasever, quiet)


# FIXME: https://bitbucket.org/logilab/pylint/issue/535
@behave.when(  # pylint: disable=no-member
    'I execute DNF with the default configuration')
# FIXME: https://bitbucket.org/logilab/pylint/issue/535
def _configure_dnf_defaults(context):  # pylint: disable=unused-argument
    """Configure default DNF options that should be used when executed.

    :param context: the context in which the function is called
    :type context: behave.runner.Context

    """
    pass


# FIXME: https://bitbucket.org/logilab/pylint/issue/535
@behave.when(  # pylint: disable=no-member
    'I execute DNF with the following configuration')
# FIXME: https://bitbucket.org/logilab/pylint/issue/535
def _configure_dnf_customs(context):  # pylint: disable=unused-argument
    """Configure custom DNF options that should be used when executed.

    :param context: the context in which the function is called
    :type context: behave.runner.Context
    :raises exceptions.ValueError: if the context has no table

    """
    if not context.table:
        raise ValueError('table not found')
    if context.table.headings != ['Option', 'Value']:
        raise NotImplementedError('configuration format not supported')
    for option, value in context.table:
        if option == '--releasever':
            context.releasever_option = value
        elif option == '--installroot':
            context.installroot_option = value
        else:
            raise NotImplementedError('configuration not supported')


# FIXME: https://bitbucket.org/logilab/pylint/issue/535
@behave.then('I should manage the system root')  # pylint: disable=no-member
def _test_management(context):
    """Test whether the system root is managed.

    The "dnf" executable must be available.

    :param context: the context in which the function is called
    :type context: behave.runner.Context
    :raises exceptions.AssertionError: if the test fails
    :raises exceptions.OSError: if the executable cannot be executed
    :raises subprocess.CalledProcessError: if the executable fails

    """
    pkgfn = os.path.join(REPODN.decode(), 'foo-1-1.noarch.rpm')
    _run_dnf_install(
        [pkgfn], context.installroot_option, context.releasever_option,
        quiet=True, assumeyes=True)
    try:
        with dnf.Base() as base:
            base.fill_sack(load_available_repos=False)
            package = base.add_remote_rpm(pkgfn)
            installed = base.sack.query().installed().filter(
                name=package.name, epoch=int(package.epoch),
                version=package.version, release=package.release,
                arch=package.arch)
            assert installed, 'system root not managed'
    finally:
        _run_dnf(
            ['remove', 'foo'], context.installroot_option,
            context.releasever_option, quiet=True, assumeyes=True)


# FIXME: https://bitbucket.org/logilab/pylint/issue/535
@behave.then(  # pylint: disable=no-member
    'I should have the {packages} packages being verified using the {keys} '
    'keys')
def _test_verification(context, packages, keys):
    """Test whether packages are verified using correct keys.

    The "dnf" and "rpm" executables must be available.

    :param context: the context in which the function is called
    :type context: behave.runner.Context
    :param packages: a description of the root of the system with the
       tested packages
    :type packages: unicode
    :param keys: a description of the root of the system with the tested
       keys
    :type keys: unicode
    :raises exceptions.OSError: if DNF cannot be configured or if the
       executable cannot be executed
    :raises subprocess.CalledProcessError: if executable fails
    :raises exceptions.IOError: if DNF cannot be configured

    """
    if keys != 'host':
        raise NotImplementedError('keys root not supported')
    _run_rpm(['--import', GPGKEYFN.decode()], quiet=True)
    if packages != 'host':
        raise NotImplementedError('packages root not supported')
    try:
        with _temp_repo_config(_path2url(REPODN), gpgcheck=True):
            _run_dnf_install(
                ['signed-foo'], releasever=context.releasever_option,
                quiet=True, assumeyes=True)
    finally:
        _run_rpm(
            ['--erase', 'gpg-pubkey-{}'.format(GPGKEYID.lower())], quiet=True)


# FIXME: https://bitbucket.org/logilab/pylint/issue/535
@behave.then(  # pylint: disable=no-member
    'I should have the tracking information stored {destination}')
def _test_tracking(context, destination):
    """Test whether tracking information is stored in the destination.

    The "dnf" executable must be available.

    :param context: the context in which the function is called
    :type context: behave.runner.Context
    :param destination: the expected destination
    :type destination: unicode
    :raises exceptions.OSError: if DNF cannot be configured
    :raises shutil.Error: if DNF cannot be configured
    :raises subprocess.CalledProcessError: if the executable fails
    :raises exceptions.AssertionError: if the test fails

    """
    with dnf.Base() as base:
        releasever = context.releasever_option or dnf.rpm.detect_releasever(
            base.conf.installroot)
        persistdn = base.conf.persistdir
    guest_destination = 'in the guest'
    if destination not in {'locally', guest_destination}:
        raise NotImplementedError('destination not supported')
    backupdn = tempfile.mkdtemp()
    backuppersistdn = os.path.join(backupdn, 'persist')
    try:
        with _suppress_enoent():
            shutil.copytree(persistdn, backuppersistdn)
        _run_dnf(
            ['group', 'install', 'Books and Guides'],
            context.installroot_option, releasever, quiet=True, assumeyes=True)
        content = []
        with _suppress_enoent():
            content = os.listdir(persistdn)
        if destination == guest_destination:
            assert not content, 'something stored in the host'
        else:
            assert content, 'nothing stored in the host'
    finally:
        with _suppress_enoent():
            shutil.rmtree(persistdn)
        with _suppress_enoent():
            shutil.copytree(backuppersistdn, persistdn)
        shutil.rmtree(backupdn)
    if destination == guest_destination:
        if not context.installroot_option:
            raise ValueError('guest path not set')
        chrooteddn = os.path.join(
            context.installroot_option, persistdn.lstrip(os.path.sep))
        assert os.listdir(chrooteddn), 'nothing stored in the guest'


# FIXME: https://bitbucket.org/logilab/pylint/issue/535
@behave.then(  # pylint: disable=no-member
    'I should have the $RELEASEVER configuration variable set to {expected}')
def _test_releasever(context, expected):
    """Test whether the $RELEASEVER is set to the host's version.

    The "dnf" executable and its "repoquery" plugin must be available.

    :param context: the context in which the function is called
    :type context: behave.runner.Context
    :param expected: a description of the expected release version
    :type expected: unicode
    :raises dnf.exceptions.DownloadError: if a testing root cannot be
       configured
    :raises exceptions.OSError: if DNF cannot be configured or if the
       executable cannot be executed
    :raises exceptions.IOError: if DNF cannot be configured
    :raises subprocess.CalledProcessError: if executable or the plugin
       fails

    """
    guest_releasever = '19'
    with dnf.Base() as base:
        if expected == "the host's release version":
            releasever = dnf.rpm.detect_releasever(base.conf.installroot)
        elif re.match('^“.+?”$', expected):
            releasever = expected[1:-1]
        elif expected == "the guest's release version":
            releasever = guest_releasever
        else:
            raise NotImplementedError('expectation not supported')
        if context.installroot_option:
            # Prepare an the install root.
            base.conf.installroot = context.installroot_option
            base.conf.substitutions['releasever'] = guest_releasever
            base.read_all_repos()
            base.fill_sack(load_system_repo=False)
            base.install('system-release')
            base.resolve()
            base.download_packages(base.transaction.install_set)
            base.do_transaction()
    # Create a repository with a $RELEASEVER in the URL.
    repodn = os.path.join(tempfile.mkdtemp(), releasever)
    # We need a slash at the end so that the urljoin below appends to the URL.
    repoparurl = urllib.pathname2url(
        os.path.join(os.path.dirname(repodn), b''))
    # We need urljoin to avoid a quotation of the variable.
    repourl = urlparse.urljoin(_path2url(repoparurl), b'$RELEASEVER')
    shutil.copytree(REPODN, repodn)
    try:
        metadata = createrepo_c.Metadata()
        metadata.locate_and_load_xml(repodn)
        nevras = [metadata.get(key).nevra() for key in metadata.keys()]
        with _temp_repo_config(repourl) as repoid:
            output = _run_repoquery(
                repoid, context.installroot_option, context.releasever_option,
                quiet=True)
            assert output.splitlines() == nevras, '$RELEASEVER not correct'
    finally:
        shutil.rmtree(os.path.dirname(repodn))
