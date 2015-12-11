# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import json
import os
import re
import sys

from perf_insights.mre import job_results
from perf_insights.mre import failure
import perf_insights_project
import vinn

def Reduce(results, map_results_list, job):
  project = perf_insights_project.PerfInsightsProject()

  all_source_paths = list(project.source_paths)

  all_source_paths.append(project.perf_insights_root_path)

  js_args = [
    json.dumps(map_results_list),
    json.dumps(job.AsDict()),
  ]

  res = vinn.RunFile(_REDUCE_CMDLINE_PATH, source_paths=all_source_paths,
                     js_args=js_args)


