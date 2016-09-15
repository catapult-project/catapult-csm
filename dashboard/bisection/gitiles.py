# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Functions for getting commit information from Gitiles."""

import json
import socket
import urllib2

from bisection import decorators


_BASE_URL = 'https://chromium.googlesource.com'
_PADDING = ")]}'\n"  # Gitiles padding.


def CommitInfo(repository, git_hash):
  """Fetches information about a commit.

  Args:
    git_hash: The git hash of the commit.

  Returns:
    A dictionary containing the author, message, time, file changes, and other
    information. See gitiles_test.py for an example.
  """
  # TODO: Update the docstrings in this file.
  url = '%s/%s/+/%s?format=JSON' % (_BASE_URL, repository, git_hash)
  return _Request(url)


def CommitRange(repository, first_git_hash, last_git_hash):
  """Fetches the commits in between first and last, including the latter.

  Args:
    first_git_hash: The git hash of the earliest commit in the range.
    last_git_hash: The git hash of the latest commit in the range.

  Returns:
    A list of dictionaries, one for each commit after the first commit up to
    and including the last commit. For each commit, its dictionary will
    contain information about the author and the comitter and the commit itself.
    See gitiles_test.py for an example. The list is in ascending order.
  """
  commits = []
  while last_git_hash:
    url = '%s/%s/+log/%s..%s?format=JSON' % (
        _BASE_URL, repository, first_git_hash, last_git_hash)
    response = _Request(url)
    commits += response['log']
    last_git_hash = response.get('next')
  return commits


@decorators.Retry(socket.error, 2)
def _Request(url):
  """Requests a URL and decodes the JSON result into a dict."""
  response = urllib2.urlopen(url).read()
  response = json.loads(response[len(_PADDING):])
  return response
