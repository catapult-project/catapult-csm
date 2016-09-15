# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from bisection import crrev
from bisection import gitiles


class Commit(object):
  """Commit details and step results.

  Attributes:
    _results: A dict containing the result for each Step on this commit. It may
        not be complete if a Step fails or doesn't produce results.
  """

  def __init__(self, repository, git_hash, author, message):
    self._repository = repository
    self._git_hash = git_hash
    self._commit_position = None
    self._author = author
    self._message = message

    self._results = {}
    self._run_count = 0

  def Run(self, steps):
    """Runs a series of Steps on this commit.

    If a Step fails, subsequent Steps will not be run.

    Args:
      steps: An iterable of Step objects.
    """
    self._run_count += 1
    logging.debug('Running commit %s, iteration %d.', self, self._run_count)

    step_args = (self._repository, self._git_hash)
    for step in steps:
      step_args, result = step.Run(*step_args)

      if step in self._results:
        self._results[step] += result
      else:
        self._results[step] = result

      if is_fatal:
        break

  def DifferingSteps(self, other):
    """Returns which Steps are statistically different between two Commits."""
    return frozenset(step for step in set(self.results) & set(other.results)
                     if self.results[step] != other.results[step])

  def __repr__(self):
    try:
      return 'r%d' % self.commit_position
    except ValueError:
      return self.git_hash[:7]

  @property
  def repository(self):
    return self._repository

  @property
  def git_hash(self):
    return self._git_hash

  @property
  def commit_position(self):
    if not self._commit_position:
      self._commit_position = crrev.CommitPosition(self._git_hash)
    return self._commit_position

  @property
  def author(self):
    return self._author

  @property
  def subject(self):
    return self._message.splitlines()[0]

  @property
  def message(self):
    return self._message

  @property
  def results(self):
    return self._results

  @property
  def run_count(self):
    return self._run_count


def Commits(first_git_hash, last_git_hash, include_first_commit=False):
  """Returns a list of Commits between two git hashes.

  Args:
    first_git_hash: The git hash of the first commit in the range.
    last_git_hash: The git hash of the last commit in the range.
    include_first_commit: Iff True, includes the Commit given by first_git_hash.
        The Commit given by last_git_hash is always included.

  Returns:
    A list of Commit objects in order from oldest to newest.

  Raises:
    ValueError: The git hashes are invalid, or are in different repositories.
  """
  # Ensure repositories are the same.
  first_repository = crrev.Repository(first_git_hash)
  last_repository = crrev.Repository(last_git_hash)
  if first_repository != last_repository:
    raise ValueError(
        'Bisecting across repositories: %s/%s and %s/%s.' %
        (first_repository, first_git_hash, last_repository, last_git_hash))

  # Get commit info.
  commits = gitiles.CommitRange(first_repository, first_git_hash, last_git_hash)
  if include_first_commit:
    commits.append(gitiles.CommitInfo(first_repository, first_git_hash))
  commits.reverse()

  # Populate Commit objects with commit info.
  return [Commit(first_repository, commit['commit'],
                 commit['author']['email'], commit['message'])
          for commit in commits]
