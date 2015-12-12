# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from perf_insights import local_directory_corpus_driver
from perf_insights import perf_insights_corpus_driver
from perf_insights.mre import runner
from perf_insights.mre import threaded_work_queue


class LocalRunner(runner.Runner):

  def __init__(self, trace_handles, job):
    super(LocalRunner, self).__init__(corpus_query, job)
    self._local_data_dir = local_data_dir

  def Run(self):
    pass
