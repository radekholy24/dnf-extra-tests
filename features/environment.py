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

Among other things, the fixture contains a testing RPM repository and
the default configuration of DNF (including the backup of the previous
configuration). The repository contains at least one package.

The :class:`behave.runner.Context` instance passed to the environmental
controls and to the step implementations is expected to have following
attributes:

:attr:`!configfn` : :data:`types.UnicodeType`
    A name of the DNF configuration file.
:attr:`!backupfn` : :class:`str` | :data:`None`
    A name of the DNF configuration backup file.
:attr:`!repoid` : :class:`str`
    An ID of the testing repository.
:attr:`!reponevras` : :class:`list[str]`
    The NEVRAs of all the packages in the testing repository.

"""


from __future__ import absolute_import
from __future__ import unicode_literals

import os
import shutil
import subprocess
import tempfile
import urllib
import urlparse

import createrepo_c
import dnf.rpm


def before_all(context):
    """Do the preparation that can be done at the very beginning.

    :param context: the context as described in the environment file
    :type context: behave.runner.Context
    :raises exceptions.OSError: if the repository cannot be created or
       if DNF cannot be configured
    :raises shutil.Error: if the repository cannot be created
    :raises exceptions.IOError: if DNF cannot be configured

    """
    with dnf.Base() as base:
        releasever = dnf.rpm.detect_releasever(base.conf.installroot)
        context.configfn = base.conf.config_file_path
    repopardn = tempfile.mkdtemp()
    repodn = os.path.join(repopardn, releasever)
    shutil.copytree(
        os.path.join(os.path.dirname(__file__), b'resources', b'repository'),
        repodn)
    configbackup = tempfile.NamedTemporaryFile(
        'wb',
        prefix='{}.bak'.format(os.path.basename(context.configfn)),
        dir=os.path.dirname(context.configfn),
        delete=False)
    with open(context.configfn, 'rb') as configfile, configbackup:
        shutil.copyfileobj(configfile, configbackup)
    context.backupfn = configbackup.name
    context.repoid = b'dnf-extra-texts'
    # We need a slash at the end so that the urljoin below appends to the URL.
    repoparurl = urllib.pathname2url(os.path.join(repopardn, b''))
    # We need urljoin to avoid a quotation of the variable.
    repourl = urlparse.urljoin(
        urlparse.urlunsplit((b'file', b'', repoparurl, b'', b'')),
        b'$RELEASEVER')
    with open(context.configfn, 'wt') as configfile:
        configfile.write(
            b'[{}]\n'
            b'baseurl={}\n'
            b'metadata_expire=600\n'
            .format(context.repoid, repourl))
    metadata = createrepo_c.Metadata()
    metadata.locate_and_load_xml(repodn)
    context.reponevras = [metadata.get(key).nevra() for key in metadata.keys()]
    # Build DNF's cache.
    with dnf.Base() as base:
        base.conf.substitutions['releasever'] = releasever
        base.read_all_repos()
        base.fill_sack()


def after_all(context):
    """Do the cleanup that can be done at the very end.

    The "dnf" executable must be available.

    :param context: the context as described in the environment file
    :type context: behave.runner.Context
    :raises exceptions.OSError: if the executable cannot be executed or
       if the DNF configuration backup cannot be removed
    :raises exceptions.IOError: if the original DNF configuration cannot
       be restored

    """
    subprocess.call([
        b'dnf', b'--quiet', b'--disablerepo=*',
        b'--enablerepo={}'.format(context.repoid),
        b'clean', b'metadata'])
    if context.backupfn:
        try:
            shutil.copyfile(context.backupfn, context.configfn)
        except shutil.Error:
            pass
        os.remove(context.backupfn)
        context.backupfn = None
