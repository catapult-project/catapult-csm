# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import bisection
from bisect import step
from dashboard import request_handler


class RunHandler(request_handler.RequestHandler):
  """Handler for the bisect task.

  This is our raison d'etre, folks. The thread that runs the bisect."""

  def post(self):
    """

    This method is idempotent, but not reentrant. That is, it's safe to call it
    multiple times with the same parameters, as long as the calls are sequential
    and not simultaneous.
    """
    configuration = self.request.get('configuration')
    first_git_hash = self.request.get('first_git_hash')
    last_git_hash = self.request.get('last_git_hash')
    test_suite = self.request.get('test_suite')
    test = self.request.get('test')
    metric = self.request.get('metric')

    # Get list of steps.
    steps = [step.FindIsolated()]
    if test_suite:
      steps.append(step.RunTest(test_suite, test))
    if metric:
      if not test_suite:
        raise ValueError("Bisecting on a metric but there's no test_suite to run.")
      steps.append(step.ReadTestResults(metric))

    # Go!
    bisection.Run(first_git_hash, last_git_hash, steps)
