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

"""This module implements the feature steps."""


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


# FIXME: https://bitbucket.org/logilab/pylint/issue/535
@behave.when(  # pylint: disable=no-member
    'I execute DNF with the default configuration')
# FIXME: https://bitbucket.org/logilab/pylint/issue/535
def _configure_dnf(context):  # pylint: disable=unused-argument
    """Configure DNF options that should be used when executed.

    :param context: the context in which the function is called
    :type context: behave.runner.Context

    """
    pass


# FIXME: https://bitbucket.org/logilab/pylint/issue/535
@behave.then(  # pylint: disable=no-member
    "I should have the $RELEASEVER configuration variable set to the host\'s "
    'release version')
# FIXME: https://bitbucket.org/logilab/pylint/issue/535
def _test_releasever(context):  # pylint: disable=unused-argument
    """Test whether the $RELEASEVER is set to the host's version.

    The "dnf" executable and its "repoquery" plugin must be available.

    :param context: the context in which the function is called
    :type context: behave.runner.Context
    :raises exceptions.OSError: if DNF cannot be configured or if the
       executable cannot be executed
    :raises exceptions.IOError: if DNF cannot be configured
    :raises subprocess.CalledProcessError: if executable or the plugin
       fails

    """
    with dnf.Base() as base:
        releasever = dnf.rpm.detect_releasever(base.conf.installroot)
        reposdn = base.conf.reposdir[0]
    try:
        os.makedirs(reposdn)
    except OSError as err:
        if err.errno != errno.EEXIST or not os.path.isdir(reposdn):
            raise
    reposrcdn = os.path.join(
        os.path.dirname(__file__), os.path.pardir, b'resources', b'repository')
    repodn = os.path.join(tempfile.mkdtemp(), releasever)
    repoid = 'dnf-extra-tests'
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
                .format(repoid.encode('utf-8'), repourl))
            repofile.flush()
            try:
                output = subprocess.check_output([
                    'dnf', '--quiet', 'repoquery', '--repo', repoid])
                assert output.splitlines() == nevras, '$RELEASEVER not correct'
            finally:
                subprocess.call([
                    'dnf', '--quiet', '--disablerepo=*',
                    '--enablerepo={}'.format(repoid), 'clean', 'metadata'])
    finally:
        shutil.rmtree(os.path.dirname(repodn))
