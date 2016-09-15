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

  def Run(self, *args):
    """Run a step.

    Running a step must produce a Sample object. The exit code can be inserted
    directly into a Sample object, which can compare them with statistical
    significance. This allows for flaky failure bisects.

    Args:
      args: Any arguments passed from the previous Step.

    Returns:
      A tuple of (tuple, Sample). The inner tuple contains arguments that are
      passed to the subsequent Step's Run() method.
    """
    raise NotImplementedError()

  @property
  def metric_name(self):
    raise NotImplementedError()
