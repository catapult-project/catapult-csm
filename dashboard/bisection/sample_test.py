# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import operator
import unittest

from bisection import sample


class SampleTest(unittest.TestCase):

  def testCannotTestEquality(self):
    self.assertRaises(AttributeError, operator.eq,
                      sample.Sample((0,)), sample.Sample((0,)))

  def testAdd(self):
    sample1 = sample.Sample((1, 2))
    sample2 = sample.Sample((3, 4, 5))
    sample1 += sample2
    self.assertEqual(sample1.values, (1, 2, 3, 4, 5))
    self.assertEqual(sample2.values, (3, 4, 5))

  def testLen(self):
    s = sample.Sample((1, 2, 3))
    self.assertEqual(len(s), 3)

  def testNeTrue(self):
    sample1 = sample.Sample((0, 1, 0, 0, 1, 0))
    sample2 = sample.Sample((3, 2, 3, 2, 1, 3))
    self.assertTrue(sample1 != sample2)

  def testNeFalse(self):
    sample1 = sample.Sample((0, 0, 1, 0, 1))
    sample2 = sample.Sample((0, 0, 0, 0, 1))
    self.assertFalse(sample1 != sample2)

  def testNeWithEmptyResult(self):
    sample1 = sample.Sample(tuple())
    sample2 = sample.Sample((3, 4, 5))
    self.assertFalse(sample1 != sample2)

  def testNeWithIdenticalValues(self):
    sample1 = sample.Sample((0, 0, 0))
    sample2 = sample.Sample((0, 0, 0))
    self.assertFalse(sample1 != sample2)

  def testNeWithBools(self):
    sample1 = sample.Sample((False, False, False, False, False))
    sample2 = sample.Sample((True, True, True, True, True))
    self.assertTrue(sample1 != sample2)

  def testNeWithWrongType(self):
    sample1 = sample.Sample((0,))
    sample2 = 'not a sample'
    self.assertRaises(TypeError, operator.ne, sample1, sample2)

  def testRepr(self):
    self.assertEqual(repr(sample.Sample(())), 'Sample(())')
    self.assertEqual(repr(sample.Sample([1, 2, 3])), 'Sample((1, 2, 3))')
    self.assertEqual(repr(sample.Sample((False, True))),
                     'Sample((False, True))')

  def testValues(self):
    s = sample.Sample((1, 2, 3, 4, 5))
    self.assertEqual(s.values, (1, 2, 3, 4, 5))
