# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

import mock
import numpy

from bisection import commit
from bisection import exceptions
from bisection import run
from bisection import sample
from bisection import step


class RunTest(unittest.TestCase):

  @mock.patch('bisection.commit.Commits')
  def testRun(self, mock_commits):
    mock_commits.return_value = [
        commit.Commit('repository', 'git_hash_%d' % i, 'author', 'message')
        for i in xrange(5)
    ]

    diffs = run.Run('git_hash_0', 'git_hash_4', (_StepWithChange,))
    self.assertEqual(len(diffs), 1)

    diff = next(iter(diffs))
    self.assertEqual(len(diff._steps), 1)

    s = next(iter(diff._steps))
    self.assertIsInstance(s, _StepWithChange)

  @mock.patch('bisection.commit.Commits')
  def testBadCommitRange(self, mock_commits):
    mock_commits.return_value = []

    with self.assertRaises(ValueError):
      run.Run('first_git_hash', 'last_git_hash', (_NoopStep,))

  @mock.patch('bisection.run._TIMEOUT', 0)
  @mock.patch('bisection.commit.Commits')
  def testNoChangeBetweenFirstAndLastCommits(self, mock_commits):
    mock_commits.return_value = [
        commit.Commit('repository', 'git_hash_%d' % i, 'author', 'message')
        for i in xrange(5)
    ]

    with self.assertRaises(exceptions.NoChangeError):
      run.Run('first_git_hash', 'last_git_hash', (_NoopStep,))

  @mock.patch('bisection.run._TIMEOUT', 0.01)
  @mock.patch('bisection.commit.Commits')
  def testRunFailureWithStatisticalFluke(self, mock_commits):
    mock_commits.return_value = [
        commit.Commit('repository', 'git_hash_%d' % i, 'author', 'message')
        for i in xrange(3)
    ]

    with self.assertRaises(exceptions.NoChangeError):
      run.Run('git_hash_0', 'git_hash_2', (_StepWithStatisticalFluke,))


class _NoopStep(step.Step):

  def Run(self, repository, git_hash):
    del repository
    del git_hash

    return False, sample.Sample((0,))

  @property
  def metric_name(self):
    return ''


class _StepWithChange(_NoopStep):

  def Run(self, repository, git_hash):
    del repository

    if git_hash > 'git_hash_2':
      r = sample.Sample(numpy.random.normal(loc=1, size=10))
    else:
      r = sample.Sample(numpy.random.normal(size=10))
    return False, r

  @property
  def metric_name(self):
    return ''


class _StepWithStatisticalFluke(_NoopStep):

  def Run(self, repository, git_hash):
    del repository

    if git_hash == 'git_hash_0':
      r = sample.Sample((0, 0, 0, 0, 0, 0))
    elif git_hash == 'git_hash_1':
      r = sample.Sample((0, 1))
    elif git_hash == 'git_hash_2':
      r = sample.Sample((1, 1, 1, 1, 1, 1))
    return False, r
