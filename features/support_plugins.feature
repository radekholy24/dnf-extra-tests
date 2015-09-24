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

Feature: Support plugins
  In order to extend DNF's functionality, I want to write my own
  plugins.

  Scenario: Support default plugins path
     When I execute DNF with the default configuration
     Then I should have the plugins at the host's default path being loaded

  Scenario: Support custom plugins path
     When I execute DNF with the following configuration in the default config:
       | Option     | Value                |
       | pluginpath | /tmp/dnf-extra-tests |
     Then I should have the plugins at host's /tmp/dnf-extra-tests being loaded

  Scenario: Support custom relative plugins path
     When I execute DNF with the following configuration in the default config:
       | Option     | Value           |
       | pluginpath | dnf-extra-tests |
     Then I should have the plugins at host's dnf-extra-tests being loaded

  Scenario: Support default plugins path if the root is different
     When I execute DNF with the following configuration on command line:
       | Option        | Value                |
       | --installroot | /tmp/dnf-extra-tests |
     Then I should have the plugins at the host's default path being loaded

  Scenario: Support custom plugins path if the root is different
     When I execute DNF with the following configuration on command line:
       | Option        | Value                 |
       | --installroot | /tmp/dnf-extra-tests1 |
     When I execute DNF with the following configuration in the default config:
       | Option     | Value                 |
       | pluginpath | /tmp/dnf-extra-tests2 |
     Then I should have the plugins at host's /tmp/dnf-extra-tests2 being loaded

  Scenario: Support custom relative plugins path if the root is different
     When I execute DNF with the following configuration on command line:
       | Option        | Value                 |
       | --installroot | /tmp/dnf-extra-tests1 |
     When I execute DNF with the following configuration in the default config:
       | Option     | Value            |
       | pluginpath | dnf-extra-tests2 |
     Then I should have the plugins at host's dnf-extra-tests2 being loaded

  Scenario: Support default plugin configuration path
     When I execute DNF with the default configuration
     Then I should have the plugins configuration path set to the host's default

  Scenario: Support custom plugin configuration path
     When I execute DNF with the following configuration in the default config:
       | Option         | Value                |
       | pluginconfpath | /tmp/dnf-extra-tests |
     Then I should have the plugins configuration path set to host's /tmp/dnf-extra-tests

  Scenario: Support custom relative plugin configuration path
     When I execute DNF with the following configuration in the default config:
       | Option         | Value           |
       | pluginconfpath | dnf-extra-tests |
     Then I should have the plugins configuration path set to host's dnf-extra-tests

  Scenario: Support default plugin configuration path if the root is different
     When I execute DNF with the following configuration on command line:
       | Option        | Value                 |
       | --installroot | /tmp/dnf-extra-tests1 |
     Then I should have the plugins configuration path set to the host's default

  Scenario: Support custom plugin configuration path if the root is different
     When I execute DNF with the following configuration on command line:
       | Option        | Value                 |
       | --installroot | /tmp/dnf-extra-tests1 |
     When I execute DNF with the following configuration in the default config:
       | Option         | Value                 |
       | pluginconfpath | /tmp/dnf-extra-tests2 |
     Then I should have the plugins configuration path set to host's /tmp/dnf-extra-tests2

  Scenario: Support custom relative plugin configuration path if the root is different
     When I execute DNF with the following configuration on command line:
       | Option        | Value                 |
       | --installroot | /tmp/dnf-extra-tests1 |
     When I execute DNF with the following configuration in the default config:
       | Option         | Value            |
       | pluginconfpath | dnf-extra-tests2 |
     Then I should have the plugins configuration path set to host's dnf-extra-tests2