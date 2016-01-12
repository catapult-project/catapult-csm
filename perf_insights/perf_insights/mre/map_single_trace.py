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


_MAP_SINGLE_TRACE_CMDLINE_PATH = os.path.join(
    perf_insights_project.PerfInsightsProject.perf_insights_src_path,
    'mre', 'map_single_trace_cmdline.html')

class TemporaryMapScript(object):
  def __init__(self, js):
    self.file = tempfile.NamedTemporaryFile()
    self.file.write("""
<!DOCTYPE html>
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

def MapSingleTrace(results, trace_handle, job):
  project = perf_insights_project.PerfInsightsProject()

  all_source_paths = list(project.source_paths)
  all_source_paths.append(project.perf_insights_root_path)

  with trace_handle.PrepareTraceForMapping() as prepared_trace_handle:
    js_args = [
      json.dumps(prepared_trace_handle.AsDict()),
      json.dumps(job.AsDict()),
    ]

    res = vinn.RunFile(
      _MAP_SINGLE_TRACE_CMDLINE_PATH, source_paths=all_source_paths,
      js_args=js_args)

  if res.returncode != 0:
    try:
      sys.stderr.write(res.stdout)
    except Exception:
      pass
    results.addFailure(failure.Failure(
        job, job.map_function_handle, trace_handle, 'Error',
        'vinn runtime error while mapping trace.', 'Unknown stack'))
    return result

  for line in res.stdout.split('\n'):
    m = re.match('^MAP_(RESULTS|FAILURE): (.+)', line, re.DOTALL)
    if m:
      found_type = m.group(1)
      found_dict = json.loads(m.group(2))
      if found_type == 'FAILURE':
        cls = _FAILURE_TYPE_NAME_TO_FAILURE_CONSTRUCTOR.get(
            found_dict['failure_type_name'])
        if not cls:
          cls = failure.Failure
        results.AddFailure(cls.FromDict(
            found_dict, job, job.map_function_handle, trace_handle))
      elif found_type == 'RESULTS':
        results.AddResults(found_dict)
    else:
      if len(line) > 0:
        sys.stderr.write(line)
        sys.stderr.write('\n')

  if len(results.results) == 0 and len(results.failures) == 0:
    raise InternalMapError('Internal error: No results were produced!')
