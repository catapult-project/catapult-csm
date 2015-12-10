# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.


class TracePreparationError(Exception):
  """Raised if something goes wrong while preparing a trace for mapping."""


class TraceHandle(object):
  def __init__(self, source_url):
    self._source_url = source_url

  @property
  def source_url(self):
      return self._source_url

  def AsDict(self):
    return {
        'source_url': self._source_url,
    }

  def _AsDictInto(self, handle_dict):
    raise NotImplementedError()

  def PrepareTraceForMapping(self):
    """Ensure that the URL to the trace will be acessible during mapping.

    This function must do any pre-work to ensure that mappers will be able to
    read from the URL contained in the trace handle.

    Raises:
      TracePreparationError: If something went wrong while preparing the trace.
    """
    raise NotImplementedError()


class FileURLTraceHandle(object):
  def __init__(self, source_url, metadata=None):
    assert source_url.startswith('file://')

    super(LocalFileTraceHandle, self).__init__(source_url)

    if metadata is None:
      self._metadata = {}
    else:
      assert isinstance(metadata, dict)
      self._metadata = metadata

  def _AsDictInto(self, handle_dict):
    handle_dict['metadata'] = metadata
    handle_dict['type'] = 'local_file'

  def PrepareTraceForMapping(self):
    pass
