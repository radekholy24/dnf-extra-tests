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

import subprocess

import behave


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
def _test_releasever(context):
    """Test whether the $RELEASEVER is set to the host's version.

    The "dnf" executable and its "repoquery" plugin must be available.

    :param context: the context in which the function is called
    :type context: behave.runner.Context
    :raises exceptions.OSError: if the executable cannot be executed
    :raises subprocess.CalledProcessError: if the plugin fails

    """
    output = subprocess.check_output([
        'dnf', '--quiet', 'repoquery', '--repo', context.repoid])
    assert output.splitlines() == context.reponevras, '$RELEASEVER not correct'
