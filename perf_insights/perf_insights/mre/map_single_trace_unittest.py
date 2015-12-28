# Copyright (c) 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import json
import tempfile
import unittest

from perf_insights.mre import function_handle
from perf_insights.mre import trace_handle
from perf_insights.mre import job as job_module
from perf_insights.mre import map_single_trace
from perf_insights.mre import map_results


def _Handle(filename):
  module = function_handle.ModuleToLoad(filename=filename)
  return function_handle.FunctionHandle(modules_to_load=[module],
                                        function_name='MyMapFunction')

class MapSingleTraceTests(unittest.TestCase):

  def testPassingMapScript(self):
    events = [
      {'pid': 1, 'tid': 2, 'ph': 'X', 'name': 'a', 'cat': 'c',
       'ts': 0, 'dur': 10, 'args': {}},
      {'pid': 1, 'tid': 2, 'ph': 'X', 'name': 'b', 'cat': 'c',
       'ts': 3, 'dur': 5, 'args': {}}
    ]
    trace_handle = in_memory_trace_handle.InMemoryTraceHandle(
        'file:///a.json', '/a.json', {'m': 1}, json.dumps(events))

    results = map_results.MapResults()
    with map_single_trace.TemporaryMapScript("""
      pi.mre.FunctionRegistry.register(
          function MyMapFunction(results, traceHandle, model) {
            results.addResult(
                'result', {
                  numProcesses: model.getAllProcesses().length
                });
          });
    """) as map_script:
      job = job_module.Job(_Handle(map_script.filename), None)
      map_single_trace.MapSingleTrace(results, trace_handle, job)

    self.assertFalse(results.failure_values)
    v = results.FindValueNamed('result')
    self.assertEquals(v['numProcesses'], 1)

  def testTraceDidntImport(self):
    run_info = run_info_module.RunInfo('file:///a.json', '/a.json',
                                       metadata={'m': 1})
    trace_string = 'This is intentionally not a trace-formatted string.'
    trace_handle = in_memory_trace_handle.InMemoryTraceHandle(
        run_info, trace_string);


    results = results_module.Results()
    with map_single_trace.TemporaryMapScript("""
      pi.mre.FunctionRegistry.register(
          function MyMapFunction(results, run_info, model) {
          });
    """) as map_script:
      map_single_trace.MapSingleTrace(results, trace_handle,
                                      _Handle(map_script.filename))

    self.assertEquals(len(results.all_values), 1)
    v = results.all_values[0]
    self.assertIsInstance(v, map_single_trace.TraceImportErrorValue);

  def testMapFunctionThatThrows(self):
    run_info = run_info_module.RunInfo('file:///a.json', '/a.json',
                                       metadata={'m': 1})
    events = [
      {'pid': 1, 'tid': 2, 'ph': 'X', 'name': 'a', 'cat': 'c',
       'ts': 0, 'dur': 10, 'args': {}},
      {'pid': 1, 'tid': 2, 'ph': 'X', 'name': 'b', 'cat': 'c',
       'ts': 3, 'dur': 5, 'args': {}}
    ]
    trace_handle = in_memory_trace_handle.InMemoryTraceHandle(
        run_info, json.dumps(events));


    results = results_module.Results()
    with map_single_trace.TemporaryMapScript("""
      pi.mre.FunctionRegistry.register(
          function MyMapFunction(results, run_info, model) {
            throw new Error('Expected error');
          });
    """) as map_script:
      map_single_trace.MapSingleTrace(results, trace_handle,
                                      _Handle(map_script.filename))

    self.assertEquals(len(results.all_values), 1)
    v = results.all_values[0]
    self.assertIsInstance(v, map_single_trace.MapFunctionErrorValue);

  def testMapperWithLoadeError(self):
    run_info = run_info_module.RunInfo('file:///a.json', '/a.json',
                                       metadata={'m': 1})
    events = [
      {'pid': 1, 'tid': 2, 'ph': 'X', 'name': 'a', 'cat': 'c',
       'ts': 0, 'dur': 10, 'args': {}},
      {'pid': 1, 'tid': 2, 'ph': 'X', 'name': 'b', 'cat': 'c',
       'ts': 3, 'dur': 5, 'args': {}}
    ]
    trace_handle = in_memory_trace_handle.InMemoryTraceHandle(
        run_info, json.dumps(events));


    results = results_module.Results()
    with map_single_trace.TemporaryMapScript("""
      throw new Error('Expected load error');
    """) as map_script:
      map_single_trace.MapSingleTrace(results, trace_handle,
                                      _Handle(map_script.filename))

    self.assertEquals(len(results.all_values), 1)
    v = results.all_values[0]
    self.assertIsInstance(v, map_single_trace.FunctionLoadingErrorValue);


  def testNoMapper(self):
    run_info = run_info_module.RunInfo('file:///a.json', '/a.json',
                                       metadata={'m': 1})
    events = [
      {'pid': 1, 'tid': 2, 'ph': 'X', 'name': 'a', 'cat': 'c',
       'ts': 0, 'dur': 10, 'args': {}},
      {'pid': 1, 'tid': 2, 'ph': 'X', 'name': 'b', 'cat': 'c',
       'ts': 3, 'dur': 5, 'args': {}}
    ]
    trace_handle = in_memory_trace_handle.InMemoryTraceHandle(
        run_info, json.dumps(events));


    results = results_module.Results()
    with map_single_trace.TemporaryMapScript("""
    """) as map_script:
      map_single_trace.MapSingleTrace(results, trace_handle,
                                      _Handle(map_script.filename))

    self.assertEquals(len(results.all_values), 1)
    v = results.all_values[0]
    self.assertIsInstance(v, map_single_trace.FunctionNotDefinedErrorValue);


  def testMapperDoesntAddValues(self):
    run_info = run_info_module.RunInfo('file:///a.json', '/a.json',
                                       metadata={'m': 1})
    events = [
      {'pid': 1, 'tid': 2, 'ph': 'X', 'name': 'a', 'cat': 'c',
       'ts': 0, 'dur': 10, 'args': {}},
      {'pid': 1, 'tid': 2, 'ph': 'X', 'name': 'b', 'cat': 'c',
       'ts': 3, 'dur': 5, 'args': {}}
    ]
    trace_handle = in_memory_trace_handle.InMemoryTraceHandle(
        run_info, json.dumps(events));


    results = results_module.Results()
    with map_single_trace.TemporaryMapScript("""
      pi.mre.FunctionRegistry.register(
          function MyMapFunction(results, run_info, model) {
      });
    """) as map_script:
      map_single_trace.MapSingleTrace(results, trace_handle,
                                      _Handle(map_script.filename))

    self.assertEquals(len(results.all_values), 1)
    v = results.all_values[0]
    self.assertIsInstance(v, map_single_trace.NoResultsAddedErrorValue);

  def testMapperSkips(self):
    run_info = run_info_module.RunInfo('file:///a.json', '/a.json',
                                       metadata={'m': 1})
    events = [
      {'pid': 1, 'tid': 2, 'ph': 'X', 'name': 'a', 'cat': 'c',
       'ts': 0, 'dur': 10, 'args': {}},
      {'pid': 1, 'tid': 2, 'ph': 'X', 'name': 'b', 'cat': 'c',
       'ts': 3, 'dur': 5, 'args': {}}
    ]
    trace_handle = in_memory_trace_handle.InMemoryTraceHandle(
        run_info, json.dumps(events));


    results = results_module.Results()
    with map_single_trace.TemporaryMapScript("""
      pi.mre.FunctionRegistry.register(
          function MyMapFunction(results, run_info, model) {
            results.addValue(new pi.v.SkipValue(
                run_info, 'SkippedFieldName',
                {description: 'SkippedReason'}));

      });
    """) as map_script:
      map_single_trace.MapSingleTrace(results, trace_handle,
                                      _Handle(map_script.filename))

    self.assertEquals(len(results.all_values), 1)
    v = results.all_values[0]
    self.assertIsInstance(v, value_module.SkipValue)
    self.assertEquals(v.name, 'SkippedFieldName')
    self.assertEquals(v.description, 'SkippedReason')
