# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import bisection


class FindIsolated(bisection.Step):

  def Run(self, repository, git_hash):
    isolated_hash = '396b8d0569cd75102e910bc837305ecb6c8cace3'
    return False, sample.Sample([0])

  @property
  def metric_name(self):
    return 'Find isolated (exit code)'


class RunTest(bisection.Step):

  def __init__(self, test_suite, test):
    self._test_suite = test_suite
    self._test = test

  def Run(self, isolated_hash):
    name = '%s/%s' % (isolated_hash, self._test_suite)

    bot_id = 'build29-b1'  # TODO

    extra_args = [self._test_suite]
    if self._test:
      extra_args.append('--story-filter=%s' % self._test)
    extra_args += [
        '--browser=reference',
        '--pageset-repeat=5',
        '--isolated-script-test-output=${ISOLATED_OUTDIR}/output.json',
    ]

    result = swarming_service.Put(name, bot_id, isolated_hash, extra_args)
    # TODO: do something with result

    return False, sample.Sample([0])

  @property
  def metric_name(self):
    return self._test_suite + ' (exit code)'


class ReadTestResults(bisection.Step):

  def __init__(self, metric):
    self._metric = metric

  def Run(self, repository, git_hash):
    # TODO: Fill out this method.
    return False, sample.Sample([0])

  @property
  def metric_name(self):
    return self._metric
