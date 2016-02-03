# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from perf_insights.mre import function_handle as function_handle_module
from perf_insights.mre import job as job_module
from perf_insights.mre import trace_handle as trace_handle_module

class Failure(object):

  def __init__(self, job, function_handle, trace_handle,
               failure_type_name, description, stack):
    assert isinstance(job, job_module.Job)
    assert isinstance(function_handle, function_handle_module.FunctionHandle)
    assert trace_handle is None or (
        isinstance(trace_handle, trace_handle_module.TraceHandle))

    self.job = job
    self.function_handle = function_handle
    self.trace_handle = trace_handle
    self.failure_type_name = failure_type_name
    self.description = description
    self.stack = stack

  def __str__(self):
    return (
      'Failure for job %s with function handle %s and trace handle %s:\n'
      'of type %s wtih description %s. Stack:\n\n%s' % (
        self.job.guid, self.function_handle.guid, self.trace_handle.source_url,
        self.failure_type_name, self.description, self.stack))

  def AsDict(self):
    return {
        'job_guid': self.job.guid,
        'function_handle_guid': self.function_handle.guid,
        'trace_handle_guid': self.trace_handle.guid,
        'failure_type_name': self.failure_type_name,
        'description': self.description,
        'stack': self.stack
    }

  # TODO(eakuefner): extend this to take some dicts instead?
  @staticmethod
  def FromDict(failure_dict, job, function_handle, trace_handle):
    return Failure(job, function_handle, trace_handle,
                   failure_dict['failure_type_name'],
                   failure_dict['description'], failure_dict['stack'])
