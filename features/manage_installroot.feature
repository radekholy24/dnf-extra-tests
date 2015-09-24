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

Feature: Manage different install roots
  In order to prepare and manage chroots, I want to manipulate the
  packages installed there.

  Scenario: Manage the system root
     When I execute DNF with the default configuration
     Then I should manage the system root

  Scenario: Manage a custom install root
     When I execute DNF with the following configuration on command line:
       | Option        | Value                |
       | --installroot | /tmp/dnf-extra-tests |
     Then I should manage the custom install root