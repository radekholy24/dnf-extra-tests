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

Among other things, the fixture contains the default configuration of
DNF (including the backup of the previous configuration).

The :class:`behave.runner.Context` instance passed to the environmental
controls and to the step implementations is expected to have following
attributes:

:attr:`!configfn` : :data:`types.UnicodeType`
    A name of the DNF configuration file.
:attr:`!backupfn` : :class:`str` | :data:`None`
    A name of the DNF configuration backup file.
:attr:`!installroot_option` : :data:`types.UnicodeType` | :data:`None`
    A name of an install root to be configured.

"""


from __future__ import absolute_import
from __future__ import unicode_literals

import os
import shutil
import tempfile

import dnf


def before_all(context):
    """Do the preparation that can be done at the very beginning.

    :param context: the context as described in the environment file
    :type context: behave.runner.Context
    :raises exceptions.IOError: if DNF cannot be configured

    """
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
    # Build DNF's cache.
    with dnf.Base() as base:
        base.read_all_repos()
        base.fill_sack()


# FIXME: https://bitbucket.org/logilab/pylint/issue/535
def before_scenario(context, scenario):  # pylint: disable=unused-argument
    """Do the preparation that must be done before every scenario.

    :param context: the context as described in the environment file
    :type context: behave.runner.Context
    :param scenario: the next tested scenario
    :type scenario: behave.model.Scenario

    """
    context.installroot_option = None


def after_all(context):
    """Do the cleanup that can be done at the very end.

    :param context: the context as described in the environment file
    :type context: behave.runner.Context
    :raises exceptions.OSError: if the DNF configuration backup cannot
       be removed
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
