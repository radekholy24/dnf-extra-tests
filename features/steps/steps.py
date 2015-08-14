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

:var REPOID: name of testing repositories
:type REPOID: unicode

"""


from __future__ import absolute_import
from __future__ import unicode_literals

import errno
import os
import shutil
import subprocess
import tempfile
import urllib
import urlparse

import behave
import createrepo_c
import dnf.rpm


REPOID = 'dnf-extra-tests'


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
        if option == '--installroot':
            context.installroot_option = value
        else:
            raise NotImplementedError('configuration not supported')


# FIXME: https://bitbucket.org/logilab/pylint/issue/535
@behave.then(  # pylint: disable=no-member
    'I should have the $RELEASEVER configuration variable set to the '
    "{target}'s release version")
def _test_releasever(context, target):
    """Test whether the $RELEASEVER is set to the host's version.

    The "dnf" executable and its "repoquery" plugin must be available.

    :param context: the context in which the function is called
    :type context: behave.runner.Context
    :param target: a root which contains a system of the expected
       release version
    :type target: unicode
    :raises dnf.exceptions.DownloadError: if the target cannot be
       configured
    :raises exceptions.OSError: if DNF cannot be configured or if the
       executable cannot be executed
    :raises exceptions.IOError: if DNF cannot be configured
    :raises subprocess.CalledProcessError: if executable or the plugin
       fails

    """
    with dnf.Base() as base:
        releasever = dnf.rpm.detect_releasever(base.conf.installroot)
        reposdn = base.conf.reposdir[0]
        if target == 'guest':
            releasever = b'19'
            # Prepare an the install root.
            base.conf.installroot = context.installroot_option
            base.conf.substitutions['releasever'] = releasever
            base.read_all_repos()
            base.fill_sack(load_system_repo=False)
            base.install('system-release')
            base.resolve()
            base.download_packages(base.transaction.install_set)
            base.do_transaction()
        elif target != 'host':
            raise NotImplementedError('target not supported')
    # Create a repository with a $RELEASEVER in the URL.
    _makedirs(reposdn, exist_ok=True)
    reposrcdn = os.path.join(
        os.path.dirname(__file__), os.path.pardir, b'resources', b'repository')
    repodn = os.path.join(tempfile.mkdtemp(), releasever)
    # We need a slash at the end so that the urljoin below appends to the URL.
    repoparurl = urllib.pathname2url(
        os.path.join(os.path.dirname(repodn), b''))
    # We need urljoin to avoid a quotation of the variable.
    repourl = urlparse.urljoin(
        urlparse.urlunsplit((b'file', b'', repoparurl, b'', b'')),
        b'$RELEASEVER')
    shutil.copytree(reposrcdn, repodn)
    try:
        metadata = createrepo_c.Metadata()
        metadata.locate_and_load_xml(repodn)
        nevras = [metadata.get(key).nevra() for key in metadata.keys()]
        repofile = tempfile.NamedTemporaryFile(
            'wt', suffix='.repo', dir=reposdn)
        with repofile:
            repofile.write(
                b'[{}]\n'
                b'baseurl={}\n'
                b'metadata_expire=never\n'
                .format(REPOID.encode('utf-8'), repourl))
            repofile.flush()
            cmdline = [
                'dnf', '--quiet', 'repoquery', '--repoid', REPOID]
            if context.installroot_option:
                cmdline.insert(
                    1, '--installroot={}'.format(context.installroot_option))
            try:
                output = subprocess.check_output(cmdline)
                assert output.splitlines() == nevras, '$RELEASEVER not correct'
            finally:
                subprocess.call([
                    'dnf', '--quiet', '--disablerepo=*',
                    '--enablerepo={}'.format(REPOID), 'clean', 'metadata'])
    finally:
        shutil.rmtree(os.path.dirname(repodn))
