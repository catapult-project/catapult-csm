# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import uuid


class Job(object):

  def __init__(self, map_function, reduce_function):
    self._map_function = map_function
    self._reduce_function = reduce_function
    self._id = uuid.uuid4()

  @property
  def map_function(self):
      return self._map_function

  @property
  def reduce_function(self):
      return self._reduce_function
