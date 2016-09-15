# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

import mock

from bisection import decorators


class RetryTest(unittest.TestCase):
  def setUp(self):
    decorator = decorators.Retry(FooError, 5)
    self.mock_callable = mock.MagicMock()
    self.mock_callable.__name__ = 'CallableMock'
    self.decorated_callable = decorator(self.mock_callable)

  def testSuccessOnRetry(self):
    self.mock_callable.side_effect = (FooError, 42)
    self.assertEqual(self.decorated_callable(), 42)
    self.assertEqual(self.mock_callable.call_count, 2)

  def testUncaughtException(self):
    self.mock_callable.side_effect = (FooError, FooError, UncaughtError)
    self.assertRaises(UncaughtError, self.decorated_callable)
    self.assertEqual(self.mock_callable.call_count, 3)

  def testFail(self):
    self.mock_callable.side_effect = [FooError] * 5
    self.assertRaises(FooError, self.decorated_callable)
    self.assertEqual(self.mock_callable.call_count, 5)

  def testMultipleExceptions(self):
    decorator = decorators.Retry((FooError, BarError), 5)
    mock_callable = mock.MagicMock()
    mock_callable.__name__ = 'CallableMock'
    decorated_callable = decorator(mock_callable)

    mock_callable.side_effect = (FooError, BarError, UncaughtError)
    self.assertRaises(UncaughtError, decorated_callable)
    self.assertEqual(mock_callable.call_count, 3)


class FooError(Exception):
  pass


class BarError(Exception):
  pass


class UncaughtError(Exception):
  pass
