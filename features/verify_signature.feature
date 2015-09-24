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

Feature: Verify signed package
  In order to be sure that packages are coming from trusted sources, I
  want verify that signed packages were signed using trusted keys.

  Scenario: Verify the host packages with the host keys
     When I execute DNF with the default configuration
     Then I should have the host packages being verified using the host keys

  Scenario: Verify the guest packages with the guest keys if the root is different
     When I execute DNF with the following configuration on command line:
       | Option        | Value                |
       | --installroot | /tmp/dnf-extra-tests |
     Then I should have the guest packages being verified using the guest keys