# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import unittest

import mock

from bisection import commit
from bisection import diff
from bisection import sample
from bisection import step


class DiffTest(unittest.TestCase):

  def tearDown(self):
    # matplotlib and pyfakefs don't work well together.
    # Instead, delete the generated plot after the test.
    if os.path.exists('test_plot.png'):
      os.remove('test_plot.png')

  def testTooFewCommits(self):
    with self.assertRaises(ValueError):
      diff.Diff()

    with self.assertRaises(ValueError):
      diff.Diff(mock.MagicMock())

  def testDifferingSteps(self):
    commit1 = commit.Commit('repository', 'git_hash', 'author', 'message')
    commit2 = commit.Commit('repository', 'git_hash', 'author', 'message')

    step1 = step.RunTest('metric name')
    step2 = step.RunTest('metric name')

    commit1._results = {
        step1: sample.Sample((0, 0, 0, 0, 0)),
        step2: sample.Sample((0, 0, 0, 0, 0)),
    }
    commit2._results = {
        step1: sample.Sample((1, 1, 1, 1, 1)),
        step2: sample.Sample((0, 0, 0, 0, 0)),
    }

    d = diff.Diff(commit1, commit2)

    self.assertEqual(d._steps, frozenset((step1,)))

  def testNoDifferingSteps(self):
    commit1 = commit.Commit('repository', 'git_hash', 'author', 'message')
    commit2 = commit.Commit('repository', 'git_hash', 'author', 'message')

    step1 = step.RunTest('metric name')
    step2 = step.RunTest('metric name')

    commit1._results = {step1: sample.Sample((0,)),}
    commit2._results = {step2: sample.Sample((1,)),}

    d = diff.Diff(commit1, commit2)

    self.assertEqual(d._steps, frozenset((step1, step2)))

  def testSavePlots(self):
    commit1 = commit.Commit('repository', 'git_hash', 'author', 'message')
    commit2 = commit.Commit('repository', 'git_hash', 'author', 'message')

    step1 = step.RunTest('metric name')
    step2 = step.RunTest('metric name')

    commit1._results = {step1: sample.Sample((0, 0, 0, 0, 0))}
    commit2._results = {step2: sample.Sample((1, 1, 1, 1, 1))}

    diff.Diff(commit1, commit2).SavePlots('test_plot.png')

  def testCommits(self):
    commit1 = commit.Commit('repository', 'git_hash', 'author', 'message')
    commit2 = commit.Commit('repository', 'git_hash', 'author', 'message')
    commits = commit1, commit2
    self.assertEqual(diff.Diff(*commits).commits, commits)
