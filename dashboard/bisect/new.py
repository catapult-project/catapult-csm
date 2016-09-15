# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from google.appengine.api import taskqueue

from dashboard import request_handler


class NewHandler(request_handler.RequestHandler):

  def get(self):
    pass

  def post(self):
    parameters = {
        'configuration': 'android galaxy s5',
        'first_git_hash': 'a',
        'last_git_hash': 'a',
        'test_suite': 'tab_switching.typical_25',
        'test': 'http://www.airbnb.com/',
        'metric': 'asdf',
    }
    task = taskqueue.add(queue='bisect', url='/run', target='bisect',
                         params=parameters)

    self.response.write('Task %s enqueued' % task.name)
