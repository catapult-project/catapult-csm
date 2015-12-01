# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

class Runner(object):
  def __init__(self, corpus_query, job):
    self._corpus_query = corpus_query
    self._job = job

  def Run(self):
    raise NotImplementedError()
