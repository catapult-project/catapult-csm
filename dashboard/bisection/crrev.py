# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Functions for getting commit information from crrev.com."""

import json
import socket
import urllib2

from bisection import decorators


_BASE_URL = 'https://cr-rev.appspot.com/_ah/api/crrev/v1/commit'


def CommitPosition(git_hash):
  """Converts a git hash to a commit position.

  Only works for repositories that have commit positions (e.g. chromium/src).

  Args:
    git_hash: A string with the full git hash.

  Returns:
    An int representing the commit position.

  Raises:
    ValueError: git_hash doesn't map to a commit, or the repository doesn't
        have commit positions.
  """
  commit = CommitInfo(git_hash)
  if 'number' not in commit:
    raise ValueError("%s is in %s, which doesn't have commit positions." %
                     (git_hash, commit['repo']))
  return int(commit['number'])


def Repository(git_hash):
  """Returns the repository containing a git hash.

  Args:
    git_hash: A string with the full git hash.

  Returns:
    A string with the full repository name, excluding ".git".

  Raises:
    ValueError: git_hash doesn't map to a commit.
  """
  return CommitInfo(git_hash)['repo']


@decorators.Retry(socket.error, 2)
def CommitInfo(git_hash):
  """Returns information about a commit.

  Args:
    git_hash: A string with the full git hash.

  Returns:
    A dict with information about the commit. For example:
    {
      'git_sha': '0d30216f14e3f5620de722412d76cbdb7759ec42',
      'repo': 'chromium/src',
      'numberings': [
        {
          'number': '347565',
          'numbering_type': 'COMMIT_POSITION',
          'numbering_identifier': 'refs/heads/master'
        }
      ],
      'number': '347565',
      'project': 'chromium',
      'redirect_url': 'https://chromium.googlesource.com/chromium/src/+/0d30..',
      'kind': 'crrev#commitItem',
      'etag': '"kuKkspxlsT40mYsjSiqyueMe20E/QU1czZbwY_HKY12vV6JRLFPh2lI"'
    }

  Raises:
    ValueError: git_hash doesn't map to a commit.
  """
  try:
    return json.load(urllib2.urlopen('%s/%s' % (_BASE_URL, git_hash)))
  except urllib2.HTTPError as e:
    if e.code == 404:
      raise ValueError("There's no commit with git hash %s." % git_hash)
    raise
