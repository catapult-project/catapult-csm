# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from scipy import stats


# In testing, a significance level of 0.05 was too high - there was a high rate
# of incorrect bisects. Even at 0.01 there may be a lot of incorrect bisects.
# Using some napkin math: if each bisect compares about 6 commits, and we expect
# a false positive in 1% of null sample comparisons, then 6% of bisects are
# incorrect.
_SIGNIFICANCE_LEVEL = 0.01


class Sample(object):
  """A statistical sample, taken from one population.

  Has methods for merging and comparing Samples.
  """

  def __init__(self, values):
    self._values = tuple(values)

  def __eq__(self, other):
    raise AttributeError("Can't compare equality of two Sample objects.")

  def __add__(self, other):
    """Add two Samples together.

    It is incorrect to add Samples that came from different populations.
    """
    return Sample(self.values + other.values)

  def __len__(self):
    return len(self.values)

  def __ne__(self, other):
    """Returns True if the Samples likely came from different populations.

    Performs a non-parametric test for the null hypothesis that the two samples
    came from the same distribution. Returns False if there is not enough
    confidence to reject the null hypothesis.
    """
    if not isinstance(other, Sample):
      raise TypeError()

    if not self.values or not other.values:
      return False

    if len(set(self.values + other.values)) <= 1:
      # All the values are the same.
      return False

    p_value = stats.mannwhitneyu(self.values, other.values).pvalue
    logging.debug('n1: %d,  n2: %d,  p-value: %f',
                  len(self), len(other), p_value)
    return p_value <= _SIGNIFICANCE_LEVEL

  def __repr__(self):
    return 'Sample(%s)' % repr(self.values)

  @property
  def values(self):
    return self._values
