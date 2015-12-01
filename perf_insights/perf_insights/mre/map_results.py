# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from perf_insights.mre import failure as failure_module


class MapResults(object):

  def __init__(self, failures=None, results=None):
    if failures is None:
      failures = []
    if results is None:
      results = []
    self._failures = failures
    self._results = results

  @property
  def failures(self):
      return self._failures

  @property
  def results(self):
      return self._results

  def AsDict(self):
    return {
        'failures': [failure.AsDict() for failure in self._failures],
        'results': self.results
    }

  @staticmethod
  def FromDict(map_results_dict):
    failures = map(failure_module.Failure.FromDict,
                   map_results_dict['failures'])
    results = map_results_dict['results']

    return MapResults(failures, results)
