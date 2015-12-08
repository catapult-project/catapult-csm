# Copyright (c) 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import uuid

class TraceHandle(object):
  # TODO(nduca): Extract metadata from trace instead of passing here.
  def __init__(self, url, display_name=None, metadata=None, guid=uuid.uuid4()):
    self._url = url
    self._display_name = display_name
    if metadata is None:
      self._metadata = {}
    else:
      assert isinstance(metadata, dict)
      self._metadata = metadata
    self._guid = guid

  @property
  def url(self):
      return self._url

  @property
  def display_name(self):
      return self._display_name

  @property
  def metadata(self):
      return self._metadata

  @property
  def guid(self):
      return self._guid

  def AsDict(self):
    return {
        'url': self._url,
        'display_name': self._display_name,
        'metadata': self._metadata
    }

  def Open(self):
    # Returns a with-able object containing a name.
    raise NotImplementedError()
