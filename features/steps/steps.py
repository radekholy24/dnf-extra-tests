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


def _repo_config(baseurl, gpgcheck=None):
    """Compose a repository configuration.

    The ID of the repository is "dnf-extra-tests".

    :param baseurl: a base URL of the repository
    :type baseurl: str
    :param gpgcheck: a value of the gpgcheck option
    :type gpgcheck: bool | None
    :returns: the configuration as a string
    :rtype: str

    """
    lines = [
        b'[dnf-extra-tests]\n'
        b'baseurl={}\n'
        b'metadata_expire=0\n'.format(baseurl)]
    if gpgcheck is not None:
        lines.append(b'gpgcheck={}\n'.format(gpgcheck and b'true' or b'false'))
    return b''.join(lines)


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
    with dnf.Base() as base:
        configdn = base.conf.reposdir[0]
    _makedirs(configdn, exist_ok=True)
    conffile = tempfile.NamedTemporaryFile('wt', suffix='.repo', dir=configdn)
    with conffile:
        conffile.write(_repo_config(baseurl, gpgcheck))
        conffile.flush()
        try:
            yield 'dnf-extra-tests'
        finally:
            subprocess.call([
                'dnf', '--quiet', '--disablerepo=*',
                '--enablerepo=dnf-extra-tests', 'clean', 'metadata'])


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


def _run_dnf(  # pylint: disable=too-many-arguments
        args, configfn=None, root=None, releasever=None, quiet=False,
        assumeyes=False):
    """Run DNF from command line.

    The "dnf" executable must be available.

    :param args: additional command line arguments
    :type args: list[unicode]
    :param configfn: a name of a configuration file
    :type configfn: unicode | None
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
    if configfn:
        cmdline.insert(1, '--config={}'.format(configfn))
    if assumeyes:
        cmdline.insert(1, '--assumeyes')
    return subprocess.check_output(cmdline)


def _run_dnf_install(  # pylint: disable=too-many-arguments
        specs, configfn=None, root=None, releasever=None, quiet=False,
        assumeyes=False):
    """Run DNF's install command from command line.

    The "dnf" executable must be available.

    :param specs: specifications of the packages to be installed
    :type specs: list[unicode]
    :param configfn: a name of a configuration file
    :type configfn: unicode | None
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
    return _run_dnf(
        ['install'] + specs, configfn, root, releasever, quiet, assumeyes)


def _run_repoquery(
        configfn=None, repo=None, root=None, releasever=None, quiet=False):
    """Run the DNF's repoquery plugin from command line.

    The "dnf" executable and its "repoquery" plugin must be available.

    :param configfn: a name of a configuration file
    :type configfn: unicode | None
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
    return _run_dnf(args, configfn, root, releasever, quiet)


def _prepare_installroot(name, releasever='19'):
    """Prepare an install root.

    :param name: a name of the root directory
    :type name: unicode
    :param releasever: the release version of the guest system
    :type releasever: unicode
    :raises dnf.exceptions.DownloadError: if the root cannot be prepared

    """
    with dnf.Base() as base:
        base.conf.installroot = name
        base.conf.substitutions['releasever'] = releasever
        base.read_all_repos()
        base.fill_sack(load_system_repo=False)
        base.install('system-release')
        base.resolve()
        base.download_packages(base.transaction.install_set)
        base.do_transaction()


def _test_repo_equals_dir(  # pylint: disable=too-many-arguments
        repoid, reporoot, reporelease, dirname, message, dnfconfig=None):
    """Test whether a repository is equal to a directory.

    The "dnf" executable and its "repoquery" plugin must be available.

    :param repoid: the ID of the repository
    :type repoid: unicode
    :param reporoot: a name of the install root of the repository
    :type reporoot: unicode | None
    :param reporelease: a value of the $RELEASEVER
    :type reporelease: unicode | None
    :param dirname: a name of the directory
    :type dirname: str
    :param message: an argument passed to the assertion error
    :type message: unicode
    :param dnfconfig: a name of a configuration file
    :type dnfconfig: unicode | None
    :raises exceptions.OSError: if the executable cannot be executed
    :raises exceptions.ValueError: if the repository or the directory
       cannot be queried
    :raises exceptions.AssertionError: if the test fails

    """
    try:
        output = _run_repoquery(
            dnfconfig, repoid, reporoot, reporelease, quiet=True)
    except subprocess.CalledProcessError:
        raise ValueError('repo query failed')
    metadata = createrepo_c.Metadata()
    # FIXME: https://github.com/rpm-software-management/createrepo_c/issues/29
    try:
        metadata.locate_and_load_xml(dirname)
    except Exception:
        raise ValueError('directory query failed')
    nevras = [metadata.get(key).nevra() for key in metadata.keys()]
    assert output.splitlines() == nevras, message


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
        if option == '--config':
            context.config_option = value
        elif option == '--releasever':
            context.releasever_option = value
        elif option == '--installroot':
            context.installroot_option = value
        else:
            raise NotImplementedError('configuration not supported')


# FIXME: https://bitbucket.org/logilab/pylint/issue/535
@behave.then('I should manage the {root} root')  # pylint: disable=no-member
def _test_management(context, root):
    """Test whether the particular root is managed.

    The "dnf" executable must be available.

    :param context: the context in which the function is called
    :type context: behave.runner.Context
    :param root: a description of the tested root
    :type root: unicode
    :raises dnf.exceptions.DownloadError: if a testing root cannot be
       configured
    :raises exceptions.AssertionError: if the test fails
    :raises exceptions.OSError: if the executable cannot be executed
    :raises subprocess.CalledProcessError: if the executable fails

    """
    pkgfn = os.path.join(REPODN.decode(), 'foo-1-1.noarch.rpm')
    if context.installroot_option:
        _prepare_installroot(
            context.installroot_option, context.releasever_option or '19')
    _run_dnf_install(
        [pkgfn], context.config_option, context.installroot_option,
        context.releasever_option, quiet=True, assumeyes=True)
    try:
        with dnf.Base() as base:
            if root == 'custom install':
                if not context.installroot_option:
                    raise ValueError('root path not set')
                base.conf.installroot = context.installroot_option
            elif root != 'system':
                raise NotImplementedError('root description not supported')
            base.fill_sack(load_available_repos=False)
            package = base.add_remote_rpm(pkgfn)
            installed = base.sack.query().installed().filter(
                name=package.name, epoch=int(package.epoch),
                version=package.version, release=package.release,
                arch=package.arch)
            assert installed, '{} root not managed'.format(root)
    finally:
        _run_dnf(
            ['remove', 'foo'], root=context.installroot_option,
            releasever=context.releasever_option, quiet=True, assumeyes=True)


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
    :raises dnf.exceptions.DownloadError: if a testing root cannot be
       configured
    :raises exceptions.ValueError: if a guest is manipulated but its
       path is not specified
    :raises exceptions.OSError: if DNF cannot be configured or if the
       executable cannot be executed
    :raises subprocess.CalledProcessError: if executable fails
    :raises exceptions.IOError: if DNF cannot be configured

    """
    def translate_root(description):
        """Convert from a root description to a root path.

        :param description: the root description
        :type description: unicode
        :returns: the root path
        :rtype: unicode
        :raises exceptions.ValueError: if a guest is described but its
           path is not specified

        """
        if description == 'host':
            return
        elif description == 'guest':
            if not context.installroot_option:
                raise ValueError('guest path not set')
            return context.installroot_option
        else:
            raise NotImplementedError('root description not supported')
    if context.installroot_option:
        # Prepare the install root.
        _prepare_installroot(context.installroot_option)
    _run_rpm(
        ['--import', GPGKEYFN.decode()], root=translate_root(keys), quiet=True)
    try:
        with _temp_repo_config(_path2url(REPODN), gpgcheck=True):
            _run_dnf_install(
                ['signed-foo'], context.config_option,
                translate_root(packages), context.releasever_option,
                quiet=True, assumeyes=True)
    finally:
        _run_rpm(
            ['--erase', 'gpg-pubkey-{}'.format(GPGKEYID.lower())],
            root=translate_root(keys), quiet=True)


@behave.then(  # pylint: disable=no-member
    'I should have the {expected} configuration file loaded')
def _test_config(context, expected):
    """Test whether the default configuration file is loaded.

    The "dnf" executable and its "repoquery" plugin must be available.

    :param context: the context in which the function is called
    :type context: behave.runner.Context
    :param expected: a description of the expected configuration
    :type expected: unicode
    :raises dnf.exceptions.DownloadError: if a testing root cannot be
       configured
    :raises exceptions.IOError: if DNF cannot be configured
    :raises exceptions.OSError: if the executable cannot be executed
    :raises exceptions.ValueError: if the configuration cannot be tested
    :raises exceptions.AssertionError: if the test fails

    """
    if expected == 'default':
        configfn = context.configfn
    elif expected == "guest's default":
        if not context.installroot_option:
            raise ValueError('guest path not set')
        configfn = os.path.join(
            context.installroot_option, context.configfn.lstrip(os.path.sep))
    else:
        configfn = expected
    if context.installroot_option:
        _prepare_installroot(
            context.installroot_option, context.releasever_option or '19')
    _makedirs(os.path.dirname(os.path.abspath(configfn)), exist_ok=True)
    with open(configfn, 'at') as configfile:
        configfile.write(_repo_config(_path2url(REPODN)))
    _test_repo_equals_dir(
        'dnf-extra-tests', context.installroot_option,
        context.releasever_option, REPODN, 'config not loaded', configfn)


@behave.then(  # pylint: disable=no-member
    'I should have the events logged locally')
def _test_logging(context):
    """Test whether events are logged locally.

    The "dnf" executable must be available.

    :param context: the context in which the function is called
    :type context: behave.runner.Context
    :raises exceptions.OSError: if DNF cannot be configured or if the
       executable cannot be executed
    :raises subprocess.CalledProcessError: if executable fails
    :raises exceptions.AssertionError: if the test fails

    """
    with dnf.Base() as base:
        logdn = base.conf.logdir
    basenames = []
    with _suppress_enoent():
        basenames = os.listdir(logdn)
    for basename in basenames:
        filename = os.path.join(logdn, basename)
        if basename.startswith('dnf') and os.path.isfile(filename):
            os.remove(filename)
    if context.installroot_option:
        raise NotImplementedError('installroot not supported')
    _run_dnf(
        ['makecache'], context.config_option, context.installroot_option,
        context.releasever_option, quiet=True, assumeyes=True)
    basenames = []
    with _suppress_enoent():
        basenames = os.listdir(logdn)
    assert any(name.startswith('dnf') for name in basenames), 'nothing logged'


# FIXME: https://bitbucket.org/logilab/pylint/issue/535
@behave.then(  # pylint: disable=no-member
    'I should have the metadata cached {destination}')
def _test_caching(context, destination):
    """Test whether metadata is cached in the destination.

    The "dnf" executable must be available.

    :param context: the context in which the function is called
    :type context: behave.runner.Context
    :param destination: a description of the expected destination
    :type destination: unicode
    :raises exceptions.OSError: if DNF cannot be configured
    :raises subprocess.CalledProcessError: if the executable fails
    :raises exceptions.AssertionError: if the test fails

    """
    with dnf.Base() as base:
        cachedir = chrooteddn = base.conf.cachedir
    if context.installroot_option:
        chrooteddn = os.path.join(
            context.installroot_option, cachedir.lstrip(os.path.sep))
        _prepare_installroot(
            context.installroot_option, context.releasever_option or '19')
    with _suppress_enoent():
        shutil.rmtree(cachedir)
    with _suppress_enoent():
        shutil.rmtree(chrooteddn)
    _run_dnf(
        ['makecache'], context.config_option, context.installroot_option,
        context.releasever_option, quiet=True, assumeyes=True)
    content = []
    with _suppress_enoent():
        content = os.listdir(cachedir)
    if destination == 'locally':
        assert content, 'nothing cached in the host'
    elif destination == 'in the guest':
        assert os.listdir(chrooteddn), 'nothing cached in the guest'
        assert not content, 'something cached in the host'
    else:
        raise NotImplementedError('destination not supported')


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
        with _suppress_enoent():
            shutil.rmtree(persistdn)
        _run_dnf(
            ['group', 'install', 'Books and Guides'], context.config_option,
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
    :raises exceptions.ValueError: if the $RELEASEVER cannot be tested
    :raises exceptions.AssertionError: if the test fails

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
    # Create a repository with a $RELEASEVER in the URL.
    repodn = os.path.join(tempfile.mkdtemp(), releasever)
    # We need a slash at the end so that the urljoin below appends to the URL.
    repoparurl = urllib.pathname2url(
        os.path.join(os.path.dirname(repodn), b''))
    # We need urljoin to avoid a quotation of the variable.
    repourl = urlparse.urljoin(_path2url(repoparurl), b'$RELEASEVER')
    shutil.copytree(REPODN, repodn)
    if context.installroot_option:
        # Prepare an the install root.
        _prepare_installroot(context.installroot_option, guest_releasever)
    try:
        with _temp_repo_config(repourl) as repoid:
            _test_repo_equals_dir(
                repoid, context.installroot_option, context.releasever_option,
                repodn, '$RELEASEVER not correct', context.config_option)
    finally:
        shutil.rmtree(os.path.dirname(repodn))
