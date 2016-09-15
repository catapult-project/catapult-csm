# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Narrows down which commit in a range caused a change.

In this package, "change" refers to a statistically significant change,
determined using hypothesis testing. A change can be measured for any build or
test result, including flaky failures.
"""

from bisection.exceptions import NoChangeError
from bisection.run import Run
from bisection.step import Step
