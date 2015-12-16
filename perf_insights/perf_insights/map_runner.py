# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import Queue as queue
import json
import os
import multiprocessing
import sys
import threading
import time
import tempfile

from perf_insights.mre import job_results
from perf_insights.mre import map_single_trace
from perf_insights.mre import map_results
from perf_insights.mre import reduce_map_results
from perf_insights.mre import threaded_work_queue
from perf_insights.results import gtest_progress_reporter

AUTO_JOB_COUNT = -1

class MapError(Exception):
  def __init__(self, *args):
    super(MapError, self).__init__(*args)
    self.run_info = None

class MapRunner(object):
  def __init__(self, trace_handles, job,
               stop_on_error=False, progress_reporter=None,
               jobs=AUTO_JOB_COUNT,
               output_formatters=None):
    self._job = job
    self._stop_on_error = stop_on_error
    self._failed_run_info_to_dump = None
    if progress_reporter is None:
      self._progress_reporter = gtest_progress_reporter.GTestProgressReporter(
                                    sys.stdout)
    else:
      self._progress_reporter = progress_reporter
    self._output_formatters = output_formatters or []

    self._trace_handles = trace_handles
    self._num_traces_merged_into_results = 0
    self._map_results = None
    self._job_results = None
    self._map_results_file = None

    if jobs == AUTO_JOB_COUNT:
      jobs = multiprocessing.cpu_count()
    self._wq = threaded_work_queue.ThreadedWorkQueue(num_threads=jobs)

  def _ProcessOneTrace(self, trace_handle):
    subresults = map_results.MapResults()
    print 'Will run ' + trace_handle.source_url

    map_single_trace.MapSingleTrace(
        subresults,
        trace_handle,
        self._job)

    print 'Did map'

    had_failure = len(subresults.failures) > 0

    if had_failure:
      print "Failure while mapping " + trace_handle.source_url
      for failure in subresults.failures:
        print failure

    self._wq.PostMainThreadTask(self._MergeResultsToIntoMaster,
                                trace_handle, subresults)

  def _MergeResultsToIntoMaster(self, trace_handle, subresults):
    self._map_results.AddResults(subresults.results)

    had_failure = len(subresults.failures) > 0
    if self._stop_on_error and had_failure:
      err = MapError("Mapping error")
      self._AbortMappingDueStopOnError(err)
      return

    self._num_traces_merged_into_results += 1
    if self._num_traces_merged_into_results == len(self._trace_handles):
      self._wq.PostMainThreadTask(self._AllMappingDone)

  def _AbortMappingDueStopOnError(self, err):
    self._wq.Stop(err)

  def _AllMappingDone(self):
    self._wq.Stop()

  def _Reduce(self, key):
    print 'Will reduce for key %s' % key

    reduce_map_results.ReduceMapResults(self._job_results, key,
                                        self._map_results_file, self._job)

    print 'Did reduce'
    self._wq.Stop()

  def Run(self):
    self._map_results = map_results.MapResults()

    for trace_handle in self._trace_handles:
      self._wq.PostAnyThreadTask(self._ProcessOneTrace, trace_handle)

    err = self._wq.Run()

    self._map_results_file = tempfile.NamedTemporaryFile()
    json.dump(self._map_results.results, self._map_results_file)
    self._map_results_file.flush()

    # Do the reduction
    self._job_results = job_results.JobResults()

    self._wq.Reset()
    for key in self._map_results.results:
      self._wq.PostAnyThreadTask(self._Reduce, key)

    err = self._wq.Run()

    for of in self._output_formatters:
      of.Format(self._job_results)

    # TODO(eakuefner): Implement repr for Failure so this is more specific.
    if err:
      print 'An issue arose.'

    results = self._job_results
    self._job_results = None
    return results
