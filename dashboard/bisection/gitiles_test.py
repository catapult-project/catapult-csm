# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json
import unittest

import mock

from bisection import gitiles


@mock.patch('urllib2.urlopen')
class GitilesTest(unittest.TestCase):

  def testCommitInfo(self, mock_urlopen):
    return_value = {
        'commit': 'commit_hash',
        'tree': 'tree_hash',
        'parents': ['parent_hash'],
        'author': {
            'name': 'username',
            'email': 'email@chromium.org',
            'time': 'Fri Jan 01 00:00:00 2016',
        },
        'committer': {
            'name': 'Commit bot',
            'email': 'commit-bot@chromium.org',
            'time': 'Fri Jan 01 00:01:00 2016',
        },
        'message': 'Subject.\n\nCommit message.',
        'tree_diff': [
            {
                'type': 'modify',
                'old_id': 'old_hash',
                'old_mode': 33188,
                'old_path': 'a/b/c.py',
                'new_id': 'new_hash',
                'new_mode': 33188,
                'new_path': 'a/b/c.py',
            },
        ],
    }
    _SetUrlopenReturnValue(mock_urlopen, ")]}'\n" + json.dumps(return_value))
    self.assertEqual(gitiles.CommitInfo('repository', 'commit_hash'), return_value)

  def testCommitRange(self, mock_urlopen):
    return_value = {
        'log': [
            {
                'commit': 'commit_2_hash',
                'tree': 'tree_2_hash',
                'parents': ['parent_2_hash'],
                'author': {
                    'name': 'username',
                    'email': 'email@chromium.org',
                    'time': 'Sat Jan 02 00:00:00 2016',
                },
                'committer': {
                    'name': 'Commit bot',
                    'email': 'commit-bot@chromium.org',
                    'time': 'Sat Jan 02 00:01:00 2016',
                },
                'message': 'Subject.\n\nCommit message.',
            },
            {
                'commit': 'commit_1_hash',
                'tree': 'tree_1_hash',
                'parents': ['parent_1_hash'],
                'author': {
                    'name': 'username',
                    'email': 'email@chromium.org',
                    'time': 'Fri Jan 01 00:00:00 2016',
                },
                'committer': {
                    'name': 'Commit bot',
                    'email': 'commit-bot@chromium.org',
                    'time': 'Fri Jan 01 00:01:00 2016',
                },
                'message': 'Subject.\n\nCommit message.',
            },
        ],
    }
    _SetUrlopenReturnValue(mock_urlopen, ")]}'\n" + json.dumps(return_value))
    self.assertEqual(
        gitiles.CommitRange('repository', 'commit_0_hash', 'commit_2_hash'),
        return_value['log'])

  def testCommitRangePaginated(self, mock_urlopen):
    return_value_1 = {
        'log': [
            {'commit': 'commit_4_hash'},
            {'commit': 'commit_3_hash'},
        ],
        'next': 'commit_2_hash',
    }
    return_value_2 = {
        'log': [
            {'commit': 'commit_2_hash'},
            {'commit': 'commit_1_hash'},
        ],
    }

    file_like_object_1 = mock.MagicMock()
    file_like_object_1.read = mock.MagicMock(
        return_value=")]}'\n" + json.dumps(return_value_1))
    file_like_object_2 = mock.MagicMock()
    file_like_object_2.read = mock.MagicMock(
        return_value=")]}'\n" + json.dumps(return_value_2))
    mock_urlopen.side_effect = file_like_object_1, file_like_object_2

    self.assertEqual(
        gitiles.CommitRange('repository', 'commit_0_hash', 'commit_4_hash'),
        return_value_1['log'] + return_value_2['log'])


def _SetUrlopenReturnValue(mock_urlopen, return_value):
  file_like_object = mock.MagicMock()
  file_like_object.read = mock.MagicMock(return_value=return_value)
  mock_urlopen.return_value = file_like_object
