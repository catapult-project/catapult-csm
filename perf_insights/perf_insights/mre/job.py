# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import uuid

from perf_insights import function_handle

class Job(object):

  def __init__(self, map_function_handle, reduce_function_handle,
               guid=uuid.uuid4()):
    self._map_function_handle = map_function_handle
    self._reduce_function_handle = reduce_function_handle
    self._guid = guid

  @property
  def guid(self):
      return self._guid

  @property
  def map_function_handle(self):
      return self._map_function_handle

  @property
  def reduce_function_handle(self):
      return self._reduce_function_handle

  def AsDict(self):
    values_dict = {
        'map_function_handle': None,
        'reduce_function_handle': None,
        'guid': str(self._guid)
    }
    if self._map_function_handle:
      values_dict['map_function_handle'] = self._map_function_handle.AsDict()
    if self._reduce_function_handle:
      values_dict['reduce_function_handle'] = self._reduce_function_handle.AsDict()
    return values_dict

  @staticmethod
  def FromDict(job_dict):
    return Job(
        function_handle.FunctionHandle.FromDict(
            job_dict['map_function_handle']),
        function_handle.FunctionHandle.FromDict(
            job_dict['reduce_function_handle'])
        )
