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

Feature: Parametrize repositories by system release version
  In order to have a single repository file for multiple system
  release specific repositories, I want to parametrize the file
  using a variable.

  Scenario: Assign the host's version to $RELEASEVER by default
     When I execute DNF with the default configuration
     Then I should have the $RELEASEVER configuration variable set to the host's release version

  Scenario: Assign the guest's version to $RELEASEVER if the root is different
     When I execute DNF with the following configuration:
       | Option        | Value                |
       | --installroot | /tmp/dnf-extra-tests |
     Then I should have the $RELEASEVER configuration variable set to the guest's release version