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

Feature: Keep track of previous runs
  In order support some future DNF's decisions, I want it to store the
  necessary information about the previous runs.

  Scenario: Store the information in the guest if the root is different
     When I execute DNF with the following configuration:
       | Option        | Value                |
       | --installroot | /tmp/dnf-extra-tests |
     Then I should have the tracking information stored in the guest