# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Exceptions used in this package."""


class NoChangeError(Exception):
  """Raised when we expected a significant change but didn't find one.

  This happens when no change is detected between the first and last commits
  within the timeout, or when a change is detected between the first and last
  commits, but no change is detected between the intervening commits within
  the timeout.
  """

  def __init__(self, message, diff):
    super(NoChangeError, self).__init__(message)
    self._diff = diff

  @property
  def diff(self):
    return self._diff
