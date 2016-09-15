# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

import mock

from bisection import commit


class CommitTest(unittest.TestCase):

  def testProperties(self):
    c = commit.Commit('repo', 'git_hash', 'author', 'subject\nmessage')
    self.assertEqual(c.repository, 'repo')
    self.assertEqual(c.git_hash, 'git_hash')
    self.assertEqual(c.author, 'author')
    self.assertEqual(c.subject, 'subject')
    self.assertEqual(c.message, 'subject\nmessage')
    self.assertEqual(c.results, {})
    self.assertEqual(c.run_count, 0)

  @mock.patch('bisection.crrev.CommitPosition')
  def testReprAndCommitPositionWithNoCommitPosition(self, mock_commit_position):
    c = commit.Commit('repository', 'git_hash', 'author', 'message')
    mock_commit_position.side_effect = ValueError()
    with self.assertRaises(ValueError):
      _ = c.commit_position
    self.assertEqual(repr(c), 'git_has')

  @mock.patch('bisection.crrev.CommitPosition')
  def testReprAndCommitPositionWithGoodCommitPosition(self, mock_commit_position):
    c = commit.Commit('repository', 'git_hash', 'author', 'message')
    mock_commit_position.return_value = 123456
    self.assertEqual(c.commit_position, 123456)
    self.assertEqual(repr(c), 'r123456')

  def testRunAndGetResults(self):
    c = commit.Commit('repository', 'git_hash', 'author', 'message')
    step = mock.MagicMock()
    result = mock.MagicMock()
    step.Run.return_value = False, result

    c.Run((step,))

    self.assertEqual(c.results, {step: result})

  def testRunAndCompareResults(self):
    commit1 = commit.Commit('repository', 'git_hash_1', 'author1', 'message1')
    commit2 = commit.Commit('repository', 'git_hash_2', 'author2', 'message2')
    step = mock.MagicMock()
    step.Run.return_value = False, mock.MagicMock()

    commit1.Run((step,))
    commit2.Run((step,))
    self.assertFalse(commit1.DifferingSteps(commit2))

    commit1.Run((step,))
    self.assertTrue(commit1.DifferingSteps(commit2))

  def testRunAndStepWasFatal(self):
    c = commit.Commit('repository', 'git_hash', 'author', 'message')
    step1 = mock.MagicMock()
    step2 = mock.MagicMock()
    step1.Run.return_value = True, mock.MagicMock()
    step2.Run.return_value = False, mock.MagicMock()

    c.Run((step1, step2))
    self.assertFalse(step2.Run.called)

    step1.Run.return_value = False, mock.MagicMock()
    c.Run((step1, step2))
    self.assertTrue(step2.Run.called)


class CommitsTest(unittest.TestCase):

  def setUp(self):
    patcher = mock.patch('bisection.crrev.Repository')
    self.addCleanup(patcher.stop)
    self.mock_repository = patcher.start()
    self.mock_repository.return_value = 'repository'

    patcher = mock.patch('bisection.gitiles.CommitRange')
    self.addCleanup(patcher.stop)
    self.mock_commit_range = patcher.start()
    self.mock_commit_range.return_value = [
        {'author': {'email': 'a3'}, 'commit': 'githash3', 'message': 's3\nm'},
        {'author': {'email': 'a2'}, 'commit': 'githash2', 'message': 's2\nm'},
        {'author': {'email': 'a1'}, 'commit': 'githash1', 'message': 's1\nm'},
    ]

    patcher = mock.patch('bisection.gitiles.CommitInfo')
    self.addCleanup(patcher.stop)
    self.mock_commit_info = patcher.start()
    self.mock_commit_info.return_value = {
        'author': {'email': 'a0'}, 'commit': 'githash0', 'message': 's0\nm'}

  def testCommits(self):
    commits = commit.Commits('first_hash', 'last_hash')
    self.assertEqual(len(commits), 3)
    for index, c in enumerate(commits):
      index += 1
      self.assertEqual(c.repository, 'repository')
      self.assertEqual(c.git_hash, 'githash' + str(index))
      self.assertEqual(c.author, 'a' + str(index))
      self.assertEqual(c.subject, 's' + str(index))
      self.assertEqual(c.message, 's' + str(index) + '\nm')

    # Check call counts to avoid making too many network requests.
    self.assertEqual(self.mock_repository.call_count, 2)
    self.assertEqual(self.mock_commit_range.call_count, 1)
    self.assertFalse(self.mock_commit_info.called)

  def testInclusive(self):
    commits = commit.Commits('first_hash', 'last_hash', True)
    self.assertEqual(len(commits), 4)
    for index, c in enumerate(commits):
      self.assertEqual(c.repository, 'repository')
      self.assertEqual(c.git_hash, 'githash' + str(index))
      self.assertEqual(c.author, 'a' + str(index))
      self.assertEqual(c.subject, 's' + str(index))
      self.assertEqual(c.message, 's' + str(index) + '\nm')

    # Check call counts to avoid making too many network requests.
    self.assertEqual(self.mock_repository.call_count, 2)
    self.assertEqual(self.mock_commit_range.call_count, 1)
    self.assertEqual(self.mock_commit_info.call_count, 1)

  def testCrossRepository(self):
    self.mock_repository.side_effect = ('repo1', 'repo2')
    self.assertRaises(ValueError, commit.Commits, 'first_hash', 'last_hash')

    # Check call counts to avoid making too many network requests.
    self.assertEqual(self.mock_repository.call_count, 2)
    self.assertFalse(self.mock_commit_range.called)
    self.assertFalse(self.mock_commit_info.called)
