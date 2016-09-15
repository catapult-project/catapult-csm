# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Helpful decorators."""

import functools


def Retry(exception_classes, max_attempts):
  """Decorator for retrying failures.

  Args:
    exception_classes: The Exception class(es) to catch and retry. Other
        Exceptions are raised as usual.
    max_attempts: The number of tries to make, including the initial attempt.

  Raises:
    The original exception: The last attempt still failed.
  """
  def RetryDecorator(wrapped_callable):
    @functools.wraps(wrapped_callable)
    def RetryWrapper(*args, **kwargs):
      for _ in range(max_attempts):
        try:
          return wrapped_callable(*args, **kwargs)
        except exception_classes:
          pass
      raise
    return RetryWrapper
  return RetryDecorator
