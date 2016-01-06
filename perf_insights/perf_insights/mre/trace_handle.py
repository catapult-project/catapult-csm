# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import contextlib
import tempfile


class TracePreparationError(Exception):
  """Raised if something goes wrong while preparing a trace for mapping."""


class _PreparedTrace(object):
  def __init__(self, canonical_url, url_to_load, metadata):
    self._canonical_url = canonical_url
    self._url_to_load = url_to_load
    self._metadata = metadata

  def AsDict(self):
    handle_dict

class TraceHandle(object):
  def __init__(self, source_url, metadata=None):
    self._source_url = source_url

    if metadata is None:
      self._metadata = {}
    else:
      assert isinstance(metadata, dict)
      self._metadata = metadata

  @property
  def metadata(self):
      return self._metadata

  @property
  def source_url(self):
      return self._source_url

  def AsDict(self):
    handle_dict = {
        'source_url': self._source_url,
        'metadata': self._metadata
    }
    self._AsDictInto(handle_dict)
    return handle_dict

  def _AsDictInto(self, handle_dict):
    raise NotImplementedError()

  @contextlib.contextmanager
  def PrepareTraceForMapping(self):
    """Ensure that the URL to the trace will be acessible during mapping.

    This function must do any pre-work to ensure that mappers will be able to
    read from the URL contained in the trace handle.

    Raises:
      TracePreparationError: If something went wrong while preparing the trace.
    """
    yield self._WillMap()
    self._DidMap()

  def _WillMap(self):
    raise NotImplementedError()

  def _DidMap(self):
    raise NotImplementedError()


class URLTraceHandle(TraceHandle):
  def __init__(self, source_url, working_url, metadata=None):
    super(URLTraceHandle, self).__init__(source_url, metadata)

    self._working_url = working_url

  def _AsDictInto(self, handle_dict):
    handle_dict['working_url'] = self._working_url
    handle_dict['type'] = 'url'

  def _WillMap(self):
    return self

  def _DidMap(self):
    pass


class InMemoryTraceHandle(TraceHandle):
  def __init__(self, source_url, data, metadata=None):
    super(InMemoryTraceHandle, self).__init__(
        source_url, metadata)

    self.data = data
    self._tempfile = None

  def _WillMap(self):
    self._tempfile = tempfile.NamedTemporaryFile()
    self._tempfile.write(self.data)
    self._tempfile.flush()
    self._tempfile.seek(0)

    return URLTraceHandle(self.source_url, 'file://' + self._tempfile.name,
                          self.metadata)

  def _DidMap(self):
    self._tempfile.close()
