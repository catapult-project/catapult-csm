# Copyright (c) 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import json
import os
import re
import sys
import tempfile
import traceback


from perf_insights.mre import map_results
from perf_insights.mre import failure
import perf_insights_project
import vinn


class TemporaryMapScript(object):
  def __init__(self, js):
    self.file = tempfile.NamedTemporaryFile()
    self.file.write("""
<!DOCTYPE html>
<link rel="import" href="/perf_insights/value/value.html">
<script>
%s
</script>
""" % js)
    self.file.flush()
    self.file.seek(0)

  def __enter__(self):
    return self

  def __exit__(self, *args, **kwargs):
    self.file.close()

  @property
  def filename(self):
      return self.file.name


class FunctionLoadingErrorValue(failure.Failure):
  pass

class FunctionNotDefinedErrorValue(failure.Failure):
  pass

class MapFunctionErrorValue(failure.Failure):
  pass

class TraceImportErrorValue(failure.Failure):
  pass

class NoResultsAddedErrorValue(failure.Failure):
  pass

class InternalMapError(Exception):
  pass

_FAILURE_TYPE_NAME_TO_FAILURE_CONSTRUCTOR = {
  'FunctionLoadingError': FunctionLoadingErrorValue,
  'FunctionNotDefinedError': FunctionNotDefinedErrorValue,
  'TraceImportError': TraceImportErrorValue,
  'MapFunctionError': MapFunctionErrorValue,
  'NoResultsAddedError': NoResultsAddedErrorValue
}

def MapSingleTrace(trace_handle, job):
  project = perf_insights_project.PerfInsightsProject()

  all_source_paths = list(project.source_paths)

  pi_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                         '..'))
  all_source_paths.append(pi_path)

  failures = []
  results = []

  map_function_handle = job.map_function
  trace_file = trace_handle.Open()
  if not trace_file:
    failures.append(failure.Failure(
        job, map_function_handle, trace_handle, 'Error',
        'error while opening trace', 'Unknown stack'))
    return

  try:
    js_args = [
      json.dumps(trace_handle.AsDict()),
      json.dumps(map_function_handle.AsDict())
    ]

    res = vinn.RunFile(
      os.path.join(pi_path, 'perf_insights', 'map_single_trace_cmdline.html'),
      source_paths=all_source_paths,
      js_args=js_args)
  finally:
    trace_file.close()

  if res.returncode != 0:
    try:
      sys.stderr.write(res.stdout)
    except Exception:
      pass
    failures.append(failure.Failure(
        job, map_function_handle, trace_handle, 'Error',
        'vinn runtime error while mapping trace.', 'Unknown stack'))
    return


  found_at_least_one_result=False
  for line in res.stdout.split('\n'):
    result_m = re.match('^MAP_(.+): (.+)', line, re.DOTALL)
    if m:
      found_type, found_dict = json.loads(m.group(1, 2))
      if found_type == 'FAILURE':
        cls = _FAILURE_TYPE_NAME_TO_FAILURE_CONSTRUCTOR.get(
            found_dict['failure_type_name'])
        if not cls:
          cls = failure_module.Failure
        failures.append(cls.FromDict(failure_dict, job, job.map_function_handle,
                                     trace_handle))
      elif found_type == 'RESULT':
        results.append(found_dict)
    else:
      if len(line) > 0:
        sys.stderr.write(line)
        sys.stderr.write('\n')

  if len(results) == 0 or len(failures) == 0:
    raise InternalMapError('Internal error: No results were produced!')
