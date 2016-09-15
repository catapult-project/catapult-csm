# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import itertools
import math

from matplotlib import cm
from matplotlib import pyplot
import numpy


_PLOT_WIDTH_INCHES = 8
_PLOT_HEIGHT_INCHES = 6
_PERCENTILES = (0, 0.05, 0.25, 0.5, 0.75, 0.95, 1)


class Diff(object):
  """Compares and visualizes differences between multiple Commits.

  If the Commits have any differing Steps, only diffs those particular Steps.
  Otherwise, diffs every Step.
  """

  def __init__(self, *commits):
    if len(commits) < 2:
      raise ValueError('Instantiated a Diff with fewer than 2 Commits.')

    self._commits = tuple(commits)

    # Determine which Steps differed between any pair of Commits.
    commit_pairs = itertools.combinations(commits, 2)
    differing_steps = (a.DifferingSteps(b) for a, b in commit_pairs)
    self._steps = frozenset.union(*differing_steps)

    if not self._steps:
      # If no Steps differed, just include all that ran.
      total_steps = (frozenset(commit.results) for commit in commits)
      self._steps = frozenset.union(*total_steps)

  def SavePlots(self, file_path):
    """Saves histograms and empirial distribution plots showing the diff.

    Args:
      file_path: The location to save the plots go.
    """
    figsize = (_PLOT_WIDTH_INCHES * 2, _PLOT_HEIGHT_INCHES * len(self._steps))
    _, axes = pyplot.subplots(nrows=len(self._steps), ncols=2, figsize=figsize)

    # TODO: Impose an ordering for steps.
    for step, (axis0, axis1) in zip(self._steps, numpy.atleast_2d(axes)):
      self._DrawHistogram(axis0, step)
      self._DrawEmpiricalCdf(axis1, step)

    pyplot.savefig(file_path)
    pyplot.close()

  def _DrawHistogram(self, axis, step):
    values_per_commit = tuple(list(commit.results[step].values)
                              for commit in self._commits
                              if step in commit.results)

    # Calculate bounds and bins.
    combined_values = sum(values_per_commit, [])
    lower_bound = min(combined_values)
    upper_bound = max(combined_values)
    if lower_bound == upper_bound:
      lower_bound -= 0.5
      upper_bound += 0.5
    bins = numpy.linspace(lower_bound, upper_bound,
                          math.log(len(combined_values)) * 4)

    # Histograms.
    colors = cm.rainbow(numpy.linspace(  # pylint: disable=no-member
        1, 0, len(self._commits) + 1))
    for commit, color in zip(self._commits, colors):
      if step not in commit.results:
        continue
      values = commit.results[step].values

      axis.hist(values, bins, alpha=0.5, normed=True, histtype='stepfilled',
                label='%s (n=%d)' % (commit, len(values)), color=color)

    # Vertical lines denoting the medians.
    medians = tuple(numpy.percentile(values, 50)
                    for values in values_per_commit)
    axis.set_xticks(medians, minor=True)
    axis.grid(which='minor', axis='x', linestyle='--')

    # Axis labels and legend.
    axis.set_xlabel(step.metric_name)
    axis.set_ylabel('Relative probability')
    axis.legend(loc='upper right')

  def _DrawEmpiricalCdf(self, axis, step):
    colors = cm.rainbow(numpy.linspace(  # pylint: disable=no-member
        1, 0, len(self._commits) + 1))
    for commit, color in zip(self._commits, colors):
      if step not in commit.results:
        continue
      values = commit.results[step].values

      # Empirical distribution function.
      levels = numpy.linspace(0, 1, len(values) + 1)
      axis.step(sorted(values) + [max(values)], levels,
                label='%s (n=%d)' % (commit, len(values)), color=color)

      # Dots denoting the percentiles.
      axis.plot(numpy.percentile(values, tuple(p * 100 for p in _PERCENTILES)),
                _PERCENTILES, '.', color=color)

    axis.set_yticks(_PERCENTILES)

    # Vertical lines denoting the medians.
    values_per_commit = tuple(list(commit.results[step].values)
                              for commit in self._commits
                              if step in commit.results)
    medians = tuple(numpy.percentile(values, 50)
                    for values in values_per_commit)
    axis.set_xticks(medians, minor=True)
    axis.grid(which='minor', axis='x', linestyle='--')

    # Axis labels and legend.
    axis.set_xlabel(step.metric_name)
    axis.set_ylabel('Cumulative probability')
    axis.legend(loc='lower right')

  @property
  def commits(self):
    return self._commits
