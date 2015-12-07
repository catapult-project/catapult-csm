# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import uuid


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
