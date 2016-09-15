# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from bisection import step


class StepTest(unittest.TestCase):

  def testRunIsAbstract(self):
    with self.assertRaises(NotImplementedError):
      step.Step().Run('repository', 'git_hash')

  def testMetricNameIsAbstract(self):
    with self.assertRaises(NotImplementedError):
      _ = step.Step().metric_name
