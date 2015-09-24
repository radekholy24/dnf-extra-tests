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

Feature: Configure repositories
  In order to control the DNF's package sources, I want to configure
  which repositories should be used.

  Scenario: Configure local base URL
     When I execute DNF with a repository dnf-extra-tests of which baseurl is file:///tmp/dnf-extra-tests
     Then I should have the content of the repository dnf-extra-tests at host's /tmp/dnf-extra-tests being available

  Scenario: Configure local base URL if the root is different
     When I execute DNF with a repository dnf-extra-tests of which baseurl is file:///tmp/dnf-extra-tests2
     When I execute DNF with the following configuration on command line:
       | Option        | Value                 |
       | --installroot | /tmp/dnf-extra-tests1 |
     Then I should have the content of the repository dnf-extra-tests at host's /tmp/dnf-extra-tests2 being available

  Scenario: Configure local metalink URL
     When I execute DNF with a repository dnf-extra-tests of which metalink is file:///tmp/metalink.xml
     Then I should have the content of the repository dnf-extra-tests at host's /tmp/dnf-extra-tests1 being available

  Scenario: Configure local metalink URL if the root is different
     When I execute DNF with a repository dnf-extra-tests of which metalink is file:///tmp/metalink.xml
     When I execute DNF with the following configuration on command line:
       | Option        | Value                 |
       | --installroot | /tmp/dnf-extra-tests2 |
     Then I should have the content of the repository dnf-extra-tests at host's /tmp/dnf-extra-tests1 being available

  Scenario: Configure local mirrorlist URL
     When I execute DNF with a repository dnf-extra-tests of which mirrorlist is file:///tmp/mirrorlist.txt
     Then I should have the content of the repository dnf-extra-tests at host's /tmp/dnf-extra-tests1 being available

  Scenario: Configure local mirrorlist URL if the root is different
     When I execute DNF with a repository dnf-extra-tests of which mirrorlist is file:///tmp/mirrorlist.txt
     When I execute DNF with the following configuration on command line:
       | Option        | Value                 |
       | --installroot | /tmp/dnf-extra-tests2 |
     Then I should have the content of the repository dnf-extra-tests at host's /tmp/dnf-extra-tests1 being available

  Scenario: Configure local GPG key URL
     When I execute DNF with a repository dnf-extra-tests of which gpgkey is file:///tmp/TEST-GPG-KEY
     Then I should have a GPG key 867B843D imported to the host and used to verify packages

  Scenario: Configure local GPG key URL if the root is different
     When I execute DNF with a repository dnf-extra-tests of which gpgkey is file:///tmp/TEST-GPG-KEY
     When I execute DNF with the following configuration on command line:
       | Option        | Value                |
       | --installroot | /tmp/dnf-extra-tests |
     Then I should have a GPG key 867B843D imported to the guest and used to verify packages

  Scenario: Load from default .repo files directory
     When I execute DNF with the default configuration
     Then I should have the .repo files loaded from the host's default directory

  Scenario: Load from custom .repo files directory
     When I execute DNF with the following configuration in the default config:
       | Option   | Value                |
       | reposdir | /tmp/dnf-extra-tests |
     Then I should have the .repo files loaded from the host's /tmp/dnf-extra-tests

  Scenario: Load from custom relative .repo files directory
     When I execute DNF with the following configuration in the default config:
       | Option   | Value           |
       | reposdir | dnf-extra-tests |
     Then I should have the .repo files loaded from the host's dnf-extra-tests

  Scenario: Load from default .repo files directory if the root is different
     When I execute DNF with the following configuration on command line:
       | Option        | Value                |
       | --installroot | /tmp/dnf-extra-tests |
     Then I should have the .repo files loaded from the host's default directory

  Scenario: Load from custom .repo files directory if the root is different
     When I execute DNF with the following configuration on command line:
       | Option        | Value                 |
       | --installroot | /tmp/dnf-extra-tests1 |
     When I execute DNF with the following configuration in the default config:
       | Option   | Value                 |
       | reposdir | /tmp/dnf-extra-tests2 |
     Then I should have the .repo files loaded from the host's /tmp/dnf-extra-tests2

  Scenario: Load from custom relative .repo files directory if the root is different
     When I execute DNF with the following configuration on command line:
       | Option        | Value                 |
       | --installroot | /tmp/dnf-extra-tests1 |
     When I execute DNF with the following configuration in the default config:
       | Option   | Value            |
       | reposdir | dnf-extra-tests2 |
     Then I should have the .repo files loaded from the host's dnf-extra-tests2