# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import socket
import unittest
import urllib2

import mock

from bisection import crrev


@mock.patch('urllib2.urlopen')
class CommitPositionTest(unittest.TestCase):

  def testHasCommitPosition(self, mock_urlopen):
    _SetUrlopenReturnValue(mock_urlopen, '{"number": 1234}')
    self.assertEqual(crrev.CommitPosition('git_hash'), 1234)
    mock_urlopen.assert_called_once_with(
        'https://cr-rev.appspot.com/_ah/api/crrev/v1/commit/git_hash')

  def testNoCommitPosition(self, mock_urlopen):
    _SetUrlopenReturnValue(mock_urlopen, '{"repo": "catapult"}')
    self.assertRaises(ValueError, crrev.CommitPosition, 'git_hash')


@mock.patch('urllib2.urlopen')
class RepositoryTest(unittest.TestCase):

  def testRepository(self, mock_urlopen):
    _SetUrlopenReturnValue(mock_urlopen, '{"repo": "repo_name"}')
    self.assertEqual(crrev.Repository('git_hash'), 'repo_name')
    mock_urlopen.assert_called_once_with(
        'https://cr-rev.appspot.com/_ah/api/crrev/v1/commit/git_hash')


@mock.patch('urllib2.urlopen')
class CommitInfoTest(unittest.TestCase):

  def testCommitInfo(self, mock_urlopen):
    _SetUrlopenReturnValue(mock_urlopen, '{}')
    self.assertEqual(crrev.CommitInfo('git_hash'), {})
    mock_urlopen.assert_called_once_with(
        'https://cr-rev.appspot.com/_ah/api/crrev/v1/commit/git_hash')

  def testRetry(self, mock_urlopen):
    file_like_object = mock.MagicMock()
    file_like_object.read = mock.MagicMock(return_value='{}')
    mock_urlopen.side_effect = (socket.error, file_like_object)
    self.assertEqual(crrev.CommitInfo('git_hash'), {})
    self.assertEqual(mock_urlopen.call_count, 2)

  def testFailsAfterRetries(self, mock_urlopen):
    mock_urlopen.side_effect = (socket.error, socket.error, socket.error)
    self.assertRaises(socket.error, crrev.CommitInfo, 'git_hash')
    self.assertEqual(mock_urlopen.call_count, 2)

  def testHTTPError404(self, mock_urlopen):
    mock_urlopen.side_effect = urllib2.HTTPError(
        'url', 404, 'message', {}, mock.MagicMock())
    self.assertRaises(ValueError, crrev.CommitInfo, 'git_hash')

  def testHTTPErrorButNot404(self, mock_urlopen):
    mock_urlopen.side_effect = urllib2.HTTPError(
        'url', 500, 'message', {}, mock.MagicMock())
    self.assertRaises(urllib2.HTTPError, crrev.CommitInfo, 'git_hash')


def _SetUrlopenReturnValue(mock_urlopen, return_value):
  file_like_object = mock.MagicMock()
  file_like_object.read = mock.MagicMock(return_value=return_value)
  mock_urlopen.return_value = file_like_object
