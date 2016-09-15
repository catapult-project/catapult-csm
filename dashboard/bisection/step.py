# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from bisection import sample


class Step(object):
  """A generic action that can be performed on a Commit.

  A step can be any behavior used to prepare or run a test. For example,
  cleaning up, updating, running hooks, downloading and installing a build,
  and running tests are all steps.
  """

  def Run(self, repository, git_hash):
    """Run a step.

    Running a step must produce a Sample object. The exit code can be inserted
    directly into a Sample object, which can compare them with statistical
    significance. This allows for flaky failure bisects.

    Args:
      repository: The repository git_hash is in.
      git_hash: The git hash of the commit to run on.

    Returns:
      A tuple of (bool, Sample). If the bool is True, the step failed fatally,
      and subsequent steps should not be run. Otherwise, the step passed or
      failed non-fatally.

      Run() may make multiple attempts. The Sample object
      contains the aggregated result of all attempts.
    """
    raise NotImplementedError()

  @property
  def metric_name(self):
    raise NotImplementedError()
