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

import environment


REPODN = os.path.join(environment.RESOURCESDN, b'repository')

GPGKEYFN = os.path.join(environment.RESOURCESDN, b'TEST-GPG-KEY')

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


def _path2url(path):
    """Convert a file path to an URL.

    :param path: the path
    :type path: str
    :returns: the URL
    :rtype: str

    """
    return urlparse.urlunsplit(
        (b'file', b'', urllib.pathname2url(path), b'', b''))


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


def _remove_gpg_pubkey(shortid, root=None, quiet=False):
    """Remove a public GPG key.

    The "rpm" executable must be available.

    :param shortid: the short ID of the key
    :type shortid: unicode
    :param root: a value of the --root option passed to rpm
    :type root: unicode | None
    :param quiet: set the --quiet option of rpm
    :type quiet: bool
    :raises exceptions.OSError: if the executable cannot be executed
    :raises subprocess.CalledProcessError: if the executable fails

    """
    _run_rpm(['--erase', 'gpg-pubkey-{}'.format(shortid.lower())], root, quiet)


def _run_dnf_install(  # pylint: disable=too-many-arguments
        specs, configfn=None, root=None, releasever=None, quiet=False,
        assumeyes=False, disablerepo=None, enablerepo=None):
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
    :param disablerepo: a pattern matching the repositories to be
        disabled
    :type disablerepo: unicode | None
    :param enablerepo: a pattern matching the repositories to be
        enabled
    :type enablerepo: unicode | None
    :returns: the output of the command
    :rtype: str
    :raises exceptions.OSError: if the executable cannot be executed
    :raises subprocess.CalledProcessError: if executable fails

    """
    return environment.run_dnf(
        ['install'] + specs, configfn, root, releasever, quiet, assumeyes,
        disablerepo, enablerepo)


def _run_dnf_remove(  # pylint: disable=too-many-arguments
        specs, configfn=None, root=None, releasever=None, quiet=False,
        assumeyes=False, disablerepo=None, enablerepo=None):
    """Run DNF's remove command from command line.

    The "dnf" executable must be available.

    :param specs: specifications of the packages to be removed
    :type specs: list[unicode]
    :param configfn: a name of a configuration file
    :type configfn: unicode | None
    :param root: a value of the --installroot option
    :type root: unicode | None
    :param releasever: a value of the --releasever option
    :type releasever: unicode | None
    :param quiet: set the --quiet option
    :type quiet: bool
    :param assumeyes: set the --assumeyes option
    :type assumeyes: bool
    :param disablerepo: a pattern matching the repositories to be
        disabled
    :type disablerepo: unicode | None
    :param enablerepo: a pattern matching the repositories to be
        enabled
    :type enablerepo: unicode | None
    :returns: the output of the command
    :rtype: str
    :raises exceptions.OSError: if the executable cannot be executed
    :raises subprocess.CalledProcessError: if the executable fails

    """
    return environment.run_dnf(
        ['remove'] + specs, configfn, root, releasever, quiet, assumeyes,
        disablerepo, enablerepo)


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
    return environment.run_dnf(args, configfn, root, releasever, quiet)


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
    'I execute DNF with the following configuration on command line')
# FIXME: https://bitbucket.org/logilab/pylint/issue/535
def _configure_dnf_cli(context):  # pylint: disable=unused-argument
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
@behave.when(  # pylint: disable=no-member
    'I execute DNF with the following configuration in the default config')
def _configure_dnf_config(context):
    """Configure custom DNF options that should be set in a config file.

    :param context: the context in which the function is called
    :type context: behave.runner.Context
    :raises exceptions.ValueError: if the context has no table

    """
    if not context.table:
        raise ValueError('table not found')
    if context.table.headings != ['Option', 'Value']:
        raise NotImplementedError('configuration format not supported')
    with open(context.configfn, 'at') as configfile:
        configfile.write(b'[main]\n')
        for option, value in context.table:
            configfile.write('{}={}\n'.format(option, value).encode('utf-8'))


# FIXME: https://bitbucket.org/logilab/pylint/issue/535
@behave.when(  # pylint: disable=no-member
    'I execute DNF with a repository {repoid} of which {urltype} is {url}')
def _configure_baseurl(context, repoid, urltype, url):
    """Configure a repository with a base URL.

    :param context: the context in which the function is called
    :type context: behave.runner.Context
    :param repoid: the ID of the repository
    :type repoid: unicode
    :param urltype: a description of the type of the repository URL
    :type urltype: unicode
    :param url: the URL of the repository
    :type url: unicode
    :raises exceptions.OSError: if the repository cannot be configured
    :raises exceptions.IOError: if the repository cannot be configured

    """
    if urltype == 'baseurl':
        config = environment.TempRepoConfig(url.encode('utf-8'))
    elif urltype in {'metalink', 'mirrorlist', 'gpgkey'}:
        scheme, netloc, path, params, query, fragment = urlparse.urlparse(url)
        if scheme != 'file' or netloc or params or query or fragment:
            raise NotImplementedError('url not supported')
        if urltype == 'metalink':
            config = environment.TempRepoConfig(metalink=url.encode('utf-8'))
            basename = 'metalink.xml'
        elif urltype == 'mirrorlist':
            config = environment.TempRepoConfig(mirrorlist=url.encode('utf-8'))
            basename = 'mirrorlist.txt'
        elif urltype == 'gpgkey':
            config = environment.TempRepoConfig(
                _path2url(REPODN), gpgcheck=True, gpgkey=url.encode('utf-8'))
            basename = 'TEST-GPG-KEY'
        dirname, basename_ = os.path.split(urllib.url2pathname(path))
        if basename_ != basename:
            raise NotImplementedError('name not supported')
        resource = environment.TempResourceCopy(basename, dirname)
        if context.temp_resource:
            raise NotImplementedError('multiple resources not supported')
        resource.create()
        context.temp_resource = resource
    else:
        raise NotImplementedError('type not supported')
    if repoid != config.REPOID:
        raise NotImplementedError('ID not supported')
    if context.temp_repo:
        raise NotImplementedError('multiple repos not supported')
    config.add()
    context.temp_repo = config


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
        _run_dnf_remove(
            ['foo'], root=context.installroot_option,
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
        with environment.TempRepoConfig(_path2url(REPODN), gpgcheck=True):
            _run_dnf_install(
                ['signed-foo'], context.config_option,
                translate_root(packages), context.releasever_option,
                quiet=True, assumeyes=True)
        _run_dnf_remove(
            ['signed-foo'], root=translate_root(packages),
            releasever=context.releasever_option, quiet=True, assumeyes=True)
    finally:
        _remove_gpg_pubkey(GPGKEYID, translate_root(keys), quiet=True)


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
    environment.makedirs(
        os.path.dirname(os.path.abspath(configfn)), exist_ok=True)
    with open(configfn, 'at') as configfile:
        configfile.write(environment.repo_config(_path2url(REPODN)))
    _test_repo_equals_dir(
        'dnf-extra-tests', context.installroot_option,
        context.releasever_option, REPODN, 'config not loaded',
        context.config_option)


# FIXME: https://bitbucket.org/logilab/pylint/issue/535
@behave.then(  # pylint: disable=no-member
    "I should have the content of the repository {repoid} at host's {path} "
    'being available')
def _test_repository(context, repoid, path):
    """Test whether a local repository is available.

    The "dnf" executable and its "repoquery" plugin must be available.

    :param context: the context in which the function is called
    :type context: behave.runner.Context
    :param repoid: the ID of the repository
    :type repoid: unicode
    :param path: a name of the repository directory
    :type path: unicode
    :raises dnf.exceptions.DownloadError: if a testing root cannot be
       configured
    :raises exceptions.OSError: if DNF cannot be configured or if the
       executable cannot be executed
    :raises shutil.Error: if DNF cannot be configured
    :raises exceptions.ValueError: if the repository or the directory
       cannot be queried
    :raises exceptions.AssertionError: if the test fails

    """
    if context.installroot_option:
        _prepare_installroot(
            context.installroot_option, context.releasever_option or '19')
    with _suppress_enoent():
        shutil.rmtree(path)
    shutil.copytree(REPODN, path)
    try:
        _test_repo_equals_dir(
            repoid, context.installroot_option, context.releasever_option,
            path.encode('utf-8'), 'repo not available', context.config_option)
    finally:
        shutil.rmtree(path)


# FIXME: https://bitbucket.org/logilab/pylint/issue/535
@behave.then(  # pylint: disable=no-member
    'I should have a GPG key {shortid} imported to the {destination} and used '
    'to verify packages')
def _test_import(context, shortid, destination):
    """Test whether a GPG key is imported from a repository to the host.

    The "dnf" and "rpm" executables must be available.

    :param context: the context in which the function is called
    :type context: behave.runner.Context
    :param shortid: the short ID of the key
    :type shortid: unicode
    :param destination: a description of the expected import destination
    :type destination: unicode
    :raises dnf.exceptions.DownloadError: if a testing root cannot be
       configured
    :raises exceptions.OSError: if an executable cannot be executed
    :raises subprocess.CalledProcessError: if an executable fails

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
        _prepare_installroot(
            context.installroot_option, context.releasever_option or '19')
    _run_dnf_install(
        ['signed-foo'], context.config_option, context.installroot_option,
        context.releasever_option, quiet=True, assumeyes=True)
    try:
        _remove_gpg_pubkey(shortid, translate_root(destination), quiet=True)
    finally:
        _run_dnf_remove(
            ['signed-foo'], root=context.installroot_option,
            releasever=context.releasever_option, quiet=True, assumeyes=True)


# FIXME: https://bitbucket.org/logilab/pylint/issue/535
@behave.then(  # pylint: disable=no-member
    "I should have the .repo files loaded from the host's {dirname}")
def _test_reposdir(context, dirname):
    """Test whether .repo files are loaded from a host's directory.

    The "dnf" executable and its "repoquery" plugin must be available.

    :param context: the context in which the function is called
    :type context: behave.runner.Context
    :param dirname: a name of the directory
    :type dirname: unicode
    :raises dnf.exceptions.DownloadError: if a testing root cannot be
       configured
    :raises exceptions.OSError: if DNF cannot be configured or if the
       executable cannot be executed
    :raises exceptions.IOError: if DNF cannot be configured
    :raises exceptions.ValueError: if a repository or the directory
       cannot be queried
    :raises exceptions.AssertionError: if the test fails

    """
    if dirname == 'default directory':
        dirname = None
    if context.installroot_option:
        _prepare_installroot(
            context.installroot_option, context.releasever_option or '19')
    with environment.TempRepoConfig(_path2url(REPODN), dirname=dirname):
        _test_repo_equals_dir(
            'dnf-extra-tests', context.installroot_option,
            context.releasever_option, REPODN, '.repo not loaded',
            context.config_option)


@behave.then(  # pylint: disable=no-member
    'I should have the events logged {destination}')
def _test_logging(context, destination):
    """Test whether events are logged locally.

    The "dnf" executable must be available.

    :param context: the context in which the function is called
    :type context: behave.runner.Context
    :param destination: a description of the expected destination
    :type destination: unicode
    :raises dnf.exceptions.DownloadError: if a testing root cannot be
       configured
    :raises exceptions.OSError: if DNF cannot be configured or if the
       executable cannot be executed
    :raises subprocess.CalledProcessError: if executable fails
    :raises exceptions.AssertionError: if the test fails

    """
    def log_files(dirname):
        """Iter over the DNF log files in a directory.

        :param dirname: a name of the directory
        :type dirname: unicode
        :returns: names of the files
        :rtype: generator[unicode]

        """
        basenames = []
        with _suppress_enoent():
            basenames = os.listdir(dirname)
        for basename in basenames:
            filename = os.path.join(dirname, basename)
            if basename.startswith('dnf') and os.path.isfile(filename):
                yield filename
    with dnf.Base() as base:
        logdn = chrooteddn = base.conf.logdir
    if context.installroot_option:
        chrooteddn = os.path.join(
            context.installroot_option, logdn.lstrip(os.path.sep))
        _prepare_installroot(
            context.installroot_option, context.releasever_option or '19')
    for filename in log_files(logdn):
        os.remove(filename)
    for filename in log_files(chrooteddn):
        os.remove(filename)
    environment.run_dnf_clean_metadata(
        context.config_option, context.installroot_option,
        context.releasever_option, quiet=True, assumeyes=True)
    logged = any(log_files(logdn))
    if destination == 'locally':
        assert logged, 'nothing logged in the host'
    elif destination == 'in the guest':
        assert any(log_files(chrooteddn)), 'nothing logged in the guest'
        assert not logged, 'something logged in the host'
    else:
        raise NotImplementedError('destination not supported')


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
    :raises exceptions.OSError: if DNF cannot be configured or if the
       executable cannot be executed
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
    environment.run_dnf(
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
    :raises exceptions.OSError: if the executable cannot be executed
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
        environment.run_dnf(
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
    :raises subprocess.CalledProcessError: if the executable fails
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
        with environment.TempRepoConfig(repourl):
            _test_repo_equals_dir(
                environment.TempRepoConfig.REPOID, context.installroot_option,
                context.releasever_option, repodn, '$RELEASEVER not correct',
                context.config_option)
    finally:
        shutil.rmtree(os.path.dirname(repodn))


# FIXME: https://bitbucket.org/logilab/pylint/issue/535
@behave.then(  # pylint: disable=no-member
    'I should have the plugins at {path} being loaded')
def _test_plugins(context, path):
    """Test whether particular plugins are being loaded.

    The "dnf" executable must be available.

    :param context: the context in which the function is called
    :type context: behave.runner.Context
    :param path: a name of the plugins directory
    :type path: unicode
    :raises exceptions.OSError: if DNF cannot be configured or if the
       executable cannot be executed
    :raises exceptions.IOError: if DNF cannot be configured
    :raises subprocess.CalledProcessError: if the executable fails
    :raises exceptions.AssertionError: if the test fails

    """
    with dnf.Base() as base:
        plugindn = base.conf.pluginpath[0]
    if path != "the host's default path" and path.startswith("host's "):
        plugindn = path[7:]
    with environment.TempResourceCopy('dnf-extra-tests.py', plugindn):
        expected = b'An output of the dnf-extra-tests plugin: This is unique.'
        output = environment.run_dnf_clean_metadata(
            context.config_option, context.installroot_option,
            context.releasever_option, quiet=True, assumeyes=True)
        assert expected in output, 'plugin not loaded'


# FIXME: https://bitbucket.org/logilab/pylint/issue/535
@behave.then(  # pylint: disable=no-member
    'I should have the plugins configuration path set to {path}')
def _test_plugins_conf(context, path):
    """Test whether the plugins configuration path is set correctly.

    The "dnf" executable must be available.

    :param context: the context in which the function is called
    :type context: behave.runner.Context
    :param path: the expected path
    :type path: unicode
    :raises exceptions.OSError: if DNF cannot be configured or if the
       executable cannot be executed
    :raises exceptions.IOError: if DNF cannot be configured
    :raises subprocess.CalledProcessError: if the executable fails
    :raises exceptions.AssertionError: if the test fails

    """
    with dnf.Base() as base:
        plugindn = base.conf.pluginpath[0]
        confdn = base.conf.pluginconfpath[0]
    if path != "the host's default" and path.startswith("host's "):
        confdn = path[7:]
    with environment.TempResourceCopy('dnf-extra-tests.py', plugindn), \
            environment.TempResourceCopy('dnf-extra-tests.conf', confdn):
        expected = b"dnf-extra-tests plugin's option is configured."
        output = environment.run_dnf_clean_metadata(
            context.config_option, context.installroot_option,
            context.releasever_option, quiet=True, assumeyes=True)
        assert expected in output, 'path not set'
