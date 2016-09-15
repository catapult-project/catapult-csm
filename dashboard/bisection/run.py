# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import operator
import time

from bisection import commit
from bisection import diff
from bisection import exceptions


_TIMEOUT = 60 * 60 * 2


def Run(first_git_hash, last_git_hash, steps):
  """Uses a binary search to determine which commits caused changes.

  If metric is None, it's an exit code bisect. Otherwise, it's a bisect on the
  metric, as well as test failures.

  If there are multiple changes, we only guarantee we'll find one of them, but
  may find more than one.

  Args:
    first_git_hash: The git hash of a commit before the change.
    last_git_hash: The git hash of a commit on or after the change.
    steps: Iterable of Steps to run on each commit.

  Returns:
    A list of Diff objects in order from oldest to newest.

  Raises:
    ValueError: The git hashes aren't valid, or they're out of order, or
        they're in different repositories.
  """
  # Get list of commits.
  commits = commit.Commits(first_git_hash, last_git_hash,
                           include_first_commit=True)
  if len(commits) < 2:
    raise ValueError('Only %d commits between %s and %s.' %
                     (len(commits), first_git_hash, last_git_hash))
  logging.info('Bisecting on %d commits.', len(commits))

  # Ensure there is a change between the first and last commits.
  start_time = time.time()
  while time.time() - start_time < _TIMEOUT:
    commits[0].Run(steps)
    commits[-1].Run(steps)
    if commits[0].DifferingSteps(commits[-1]):
      break
  else:
    raise exceptions.NoChangeError(
        'No change detected between the first and last commits.',
        diff.Diff(commits[0], commits[-1]))

  # Go!
  return _BisectionRecursive(steps, commits)


def _BisectionRecursive(steps, commits):
  """Recursively determines which commits caused changes.

  Args:
    steps: List or tuple of Step objects to run on each commit.
    commits: List or tuple of Commit objects in order from oldest to newest.
        The first and last commits must have previously been determined to be
        statistically different.

  Returns:
    A list of Diff objects in order from oldest to newest.
  """
  first_commit = commits[0]
  last_commit = commits[-1]

  # Base case.
  if len(commits) == 2:
    # TODO: If last_commit is a DEPS roll, bisect into it.
    return [diff.Diff(first_commit, last_commit)]

  # Recursive case.
  midpoint_index = len(commits) / 2
  midpoint_commit = commits[midpoint_index]

  logging.info('Testing %s -- %s -- %s.',
               first_commit, midpoint_commit, last_commit)
  start_time = time.time()
  while time.time() - start_time < _TIMEOUT:
    target_commit = min((first_commit, last_commit, midpoint_commit),
                        key=operator.attrgetter('run_count'))
    target_commit.Run(steps)

    results = []
    if first_commit.DifferingSteps(midpoint_commit):
      results += _BisectionRecursive(steps, commits[:midpoint_index + 1])
    if midpoint_commit.DifferingSteps(last_commit):
      results += _BisectionRecursive(steps, commits[midpoint_index:])
    if results:
      return results

  raise exceptions.NoChangeError(
      '%s and %s are different from each other, '
      'but %s is the same as both %s and %s.' %
      (first_commit, last_commit, midpoint_commit, first_commit, last_commit),
      diff.Diff(first_commit, midpoint_commit, last_commit))
