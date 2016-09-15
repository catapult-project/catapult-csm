# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from bisection import exceptions


class ExceptionsTest(unittest.TestCase):

  def testNoChangeError(self):
    exception = exceptions.NoChangeError('message', 'diff')
    self.assertEqual(exception.message, 'message')
    self.assertEqual(exception.diff, 'diff')
