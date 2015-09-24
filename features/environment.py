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

"""This module provides the test fixture common to all the features.

Among other things, the fixture contains the default (empty) config. of
DNF (including the backup of the previous configuration), a plugin
(which prints "An output of the dnf-extra-tests plugin: This is unique."
to the standard output) and a plugin configuration file (the plugin
prints "dnf-extra-tests plugin's option is configured." if the file is
found).

The :class:`behave.runner.Context` instance passed to the environmental
controls and to the step implementations is expected to have following
attributes:

:attr:`!configfn` : :data:`types.UnicodeType`
    A name of the DNF configuration file.
:attr:`!backupfn` : :class:`str` | :data:`None`
    A name of the DNF configuration backup file.
:attr:`!temp_resource` : :class:`.TempResourceCopy` | :data:`None`
    A temporary resource copy.
:attr:`!temp_repo` : :class:`.TempRepoConfig` | :data:`None`
    A temporary repository configuration.
:attr:`!config_option` : :data:`types.UnicodeType` | :data:`None`
    A release version to be configured.
:attr:`!releasever_option` : :data:`types.UnicodeType` | :data:`None`
    A release version to be configured.
:attr:`!installroot_option` : :data:`types.UnicodeType` | :data:`None`
    A name of an install root to be configured.
:attr:`!pluginpath_option` : :data:`types.UnicodeType` | :data:`None`
    A name of a plugins directory to be configured.

:var RESOURCESDN: a name of the directory containing testing resources
:type RESOURCESDN: str

"""


from __future__ import absolute_import
from __future__ import unicode_literals

import errno
import os
import shutil
import subprocess
import tempfile

import dnf


RESOURCESDN = os.path.join(os.path.dirname(__file__), b'resources')


def makedirs(name, exist_ok=False):
    """Create a directory recursively.

    :param name: the name of the directory
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


def repo_config(
        baseurl=None, metalink=None, mirrorlist=None, gpgcheck=None,
        gpgkey=None):
    """Compose a repository configuration.

    The ID of the repository is "dnf-extra-tests".

    :param baseurl: a base URL of the repository
    :type baseurl: str | None
    :param metalink: a metalink URL of the repository
    :type metalink: str | None
    :param mirrorlist: a mirrorlist URL of the repository
    :type mirrorlist: str | None
    :param gpgcheck: a value of the gpgcheck option
    :type gpgcheck: bool | None
    :param gpgkey: a GPG key URL of the repository
    :type gpgkey: str | None
    :returns: the configuration as a string
    :rtype: str

    """
    lines = [
        b'[dnf-extra-tests]\n'
        b'metadata_expire=0\n']
    if baseurl:
        lines.append(b'baseurl={}\n'.format(baseurl))
    if metalink:
        lines.append(b'metalink={}\n'.format(metalink))
    if mirrorlist:
        lines.append(b'mirrorlist={}\n'.format(mirrorlist))
    if gpgcheck is not None:
        lines.append(b'gpgcheck={}\n'.format(gpgcheck and b'true' or b'false'))
    if gpgkey:
        lines.append(b'gpgkey={}\n'.format(gpgkey))
    return b''.join(lines)


def run_dnf(  # pylint: disable=too-many-arguments
        args, configfn=None, root=None, releasever=None, quiet=False,
        assumeyes=False, disablerepo=None, enablerepo=None):
    """Run DNF from command line.

    The "dnf" executable must be available.

    :param args: additional command line arguments
    :type args: list[unicode]
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
    :raises subprocess.CalledProcessError: if the executable fails

    """
    cmdline = ['dnf'] + args
    if releasever:
        cmdline.insert(1, '--releasever={}'.format(releasever))
    if quiet:
        cmdline.insert(1, '--quiet')
    if root:
        cmdline.insert(1, '--installroot={}'.format(root))
    if enablerepo:
        cmdline.insert(1, '--enablerepo={}'.format(enablerepo))
    if disablerepo:
        cmdline.insert(1, '--disablerepo={}'.format(disablerepo))
    if configfn:
        cmdline.insert(1, '--config={}'.format(configfn))
    if assumeyes:
        cmdline.insert(1, '--assumeyes')
    return subprocess.check_output(cmdline)


def run_dnf_clean_metadata(  # pylint: disable=too-many-arguments
        configfn=None, root=None, releasever=None, quiet=False,
        assumeyes=False, disablerepo=None, enablerepo=None):
    """Run DNF's clean metadata command from command line.

    The "dnf" executable must be available.

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
    return run_dnf(
        ['clean', 'metadata'], configfn, root, releasever, quiet, assumeyes,
        disablerepo, enablerepo)


# FIXME: https://bitbucket.org/logilab/pylint/issue/535
def before_scenario(context, scenario):  # pylint: disable=unused-argument
    """Do the preparation that must be done before every scenario.

    :param context: the context as described in the environment file
    :type context: behave.runner.Context
    :param scenario: the next tested scenario
    :type scenario: behave.model.Scenario
    :raises exceptions.IOError: if DNF cannot be configured

    """
    context.temp_resource = None
    context.temp_repo = None
    context.config_option = None
    context.releasever_option = None
    context.installroot_option = None
    with dnf.Base() as base:
        context.configfn = base.conf.config_file_path
    configbackup = tempfile.NamedTemporaryFile(
        'wb',
        prefix='{}.bak'.format(os.path.basename(context.configfn)),
        dir=os.path.dirname(context.configfn),
        delete=False)
    with open(context.configfn, 'rb') as configfile, configbackup:
        shutil.copyfileobj(configfile, configbackup)
    context.backupfn = configbackup.name
    open(context.configfn, 'wt').close()


# FIXME: https://bitbucket.org/logilab/pylint/issue/535
def after_scenario(context, scenario):  # pylint: disable=unused-argument
    """Do the cleanup that must be done after every scenario.

    :param context: the context as described in the environment file
    :type context: behave.runner.Context
    :param scenario: the next tested scenario
    :type scenario: behave.model.Scenario
    :raises exceptions.OSError: if the DNF configuration backup or the
       configured install root cannot be removed or if the original DNF
       configuration cannot be restored
    :raises exceptions.IOError: if the original DNF configuration cannot
       be restored

    """
    if context.backupfn:
        try:
            shutil.copyfile(context.backupfn, context.configfn)
        except shutil.Error:
            pass
        os.remove(context.backupfn)
        context.backupfn = None
    if context.temp_resource:
        context.temp_resource.remove()
    if context.temp_repo:
        context.temp_repo.remove()
    if context.installroot_option:
        shutil.rmtree(context.installroot_option)


class TempResourceCopy(object):

    """A temporary copy of a resource.

    Its instance can be used as a context manager.

    :ivar basename: a base name of the resource
    :type basename: unicode
    :ivar dirname: a name of the destination directory
    :type dirname: unicode
    :ivar _filename: a name of the copy
    :type _filename: unicode | None

    """

    def __init__(self, basename, dirname):
        """Initialize the copy.

        :param basename: a base name of the resource
        :type basename: unicode
        :param dirname: a name of the destination directory
        :type dirname: unicode

        """
        super(TempResourceCopy, self).__init__()
        self.basename = basename
        self.dirname = dirname
        self._filename = None

    def create(self):
        """Create the copy in the destination directory.

        The destination directory will be created if needed.

        :raises exceptions.OSError: if the directory cannot be created
        :raises exceptions.IOError: if the file cannot be copied

        """
        makedirs(self.dirname, exist_ok=True)
        filename = os.path.join(self.dirname, self.basename)
        shutil.copy2(
            os.path.join(RESOURCESDN, self.basename.encode('utf-8')), filename)
        self._filename = filename

    def remove(self):
        """Remove the copy.

        :raises exceptions.ValueError: if the copy is not present

        """
        if not self._filename:
            raise ValueError('copy not created')
        os.remove(self._filename)

    def __enter__(self):
        """Enter the runtime context related to this object.

        The copy (and the destination directory if needed) is created.

        :raises exceptions.OSError: if the copy cannot be created
        :raises exceptions.IOError: if the copy cannot be created

        """
        return self.create()

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the runtime context related to this object.

        The copy is removed.

        :param exc_type: the type of the exception that caused the
           context to be exited
        :type exc_type: type
        :param exc_value: the instance of the exception
        :type exc_value: exceptions.BaseException
        :param traceback: the traceback that encapsulates the call stack
           at the point where the exception originally occurred
        :type traceback: types.TracebackType
        :returns: suppress the exception that caused the context to be
           exited
        :rtype: bool
        :raises exceptions.ValueError: if the copy is not present

        """
        self.remove()
        return False


class TempRepoConfig(object):

    """A temporary repository configuration.

    Its instance can be used as a context manager.

    :cvar REPOID: the ID of the repository
    :type REPOID: unicode
    :ivar baseurl: a base URL of the repository
    :type baseurl: str | None
    :ivar metalink: a metalink URL of the repository
    :type metalink: str | None
    :ivar mirrorlist: a mirrorlist URL of the repository
    :type mirrorlist: str | None
    :ivar gpgcheck: a value of the gpgcheck option
    :type gpgcheck: bool | None
    :ivar gpgkey: a GPG key URL of the repository
    :type gpgkey: str | None
    :ivar dirname: a name of the destination directory
    :type dirname: unicode | None
    :ivar _filename: a name of the configuration file
    :type _filename: str | None

    """

    REPOID = 'dnf-extra-tests'

    def __init__(  # pylint: disable=too-many-arguments
            self, baseurl=None, metalink=None, mirrorlist=None, gpgcheck=None,
            gpgkey=None, dirname=None):
        """Initialize the repository.

        :param baseurl: a base URL of the repository
        :type baseurl: str | None
        :param metalink: a metalink URL of the repository
        :type metalink: str | None
        :param mirrorlist: a mirrorlist URL of the repository
        :type mirrorlist: str | None
        :param gpgcheck: a value of the gpgcheck option
        :type gpgcheck: bool | None
        :param gpgkey: a GPG key URL of the repository
        :type gpgkey: str | None
        :param dirname: a name of the destination directory
        :type dirname: unicode | None

        """
        super(TempRepoConfig, self).__init__()
        self.baseurl = baseurl
        self.metalink = metalink
        self.mirrorlist = mirrorlist
        self.gpgcheck = gpgcheck
        self.gpgkey = gpgkey
        self.dirname = dirname
        self._filename = None

    def add(self):
        """Add the repository to DNF.

        :raises exceptions.OSError: if the repository cannot be added
        :raises exceptions.IOError: if the repository cannot be added

        """
        with dnf.Base() as base:
            configdn = self.dirname or base.conf.reposdir[0]
        makedirs(configdn, exist_ok=True)
        conffile = tempfile.NamedTemporaryFile(
            'wt', suffix='.repo', dir=configdn, delete=False)
        with conffile:
            conffile.write(repo_config(
                self.baseurl, self.metalink, self.mirrorlist, self.gpgcheck,
                self.gpgkey))
        self._filename = conffile.name

    def remove(self):
        """Remove the repository from DNF.

        The "dnf" executable must be available.

        :raises exceptions.ValueError: if the repository is not present
        :raises exceptions.OSError: if the executable cannot be executed
        :raises subprocess.CalledProcessError: if the executable fails

        """
        if not self._filename:
            raise ValueError('repository not present')
        try:
            run_dnf_clean_metadata(
                quiet=True, disablerepo='*', enablerepo=self.REPOID)
        finally:
            os.remove(self._filename)
            self._filename = None

    def __enter__(self):
        """Enter the runtime context related to this object.

        The repository is added to DNF.

        :raises exceptions.OSError: if the repository cannot be added
        :raises exceptions.IOError: if the repository cannot be added

        """
        return self.add()

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the runtime context related to this object.

        The repository is removed from DNF. The "dnf" executable must be
        available.

        :param exc_type: the type of the exception that caused the
           context to be exited
        :type exc_type: type
        :param exc_value: the instance of the exception
        :type exc_value: exceptions.BaseException
        :param traceback: the traceback that encapsulates the call stack
           at the point where the exception originally occurred
        :type traceback: types.TracebackType
        :returns: suppress the exception that caused the context to be
           exited
        :rtype: bool
        :raises exceptions.ValueError: if the repository is not present
        :raises exceptions.OSError: if the executable cannot be executed
        :raises subprocess.CalledProcessError: if the executable fails

        """
        self.remove()
        return False
