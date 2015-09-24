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

"""A testing DNF plugin."""


from __future__ import absolute_import
from __future__ import print_function

import ConfigParser

import dnf


class Plugin(dnf.Plugin):

    """A testing DNF plugin.

    :ivar base: a DNF base instance
    :type base: dnf.Base

    """

    name = u'dnf-extra-tests'

    def __init__(self, base, cli):
        """Initialize the plugin.

        :param base: a DNF base instance
        :type base: dnf.Base
        :param cli: a DNF CLI instance
        :type cli: dnf.cli.Cli | None

        """
        super(Plugin, self).__init__(base, cli)
        self.base = base

    def config(self):
        """Do what needs to be done after DNF's configuration."""
        print('An output of the dnf-extra-tests plugin: This is unique.')
        parser = self.read_config(self.base.conf, self.name)
        try:
            parser.get('section', 'unique')
        except ConfigParser.NoSectionError:
            return
        print("dnf-extra-tests plugin's option is configured.")
