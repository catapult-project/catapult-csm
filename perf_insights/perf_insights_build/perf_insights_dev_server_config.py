# Copyright (c) 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime
import json
import os
import sys
import tempfile
import time
import urllib
import urllib2

import perf_insights_project

import webapp2
from webapp2 import Route

from perf_insights import cloud_storage
from perf_insights import local_directory_corpus_driver
from perf_insights import corpus_query
from perf_insights import map_runner
from perf_insights.mre import function_handle
from perf_insights.mre import job as job_module
from perf_insights import progress_reporter
from perf_insights.results import json_output_formatter


def _RelPathToUnixPath(p):
  return p.replace(os.sep, '/')

class TestListHandler(webapp2.RequestHandler):
  def get(self, *args, **kwargs): # pylint: disable=unused-argument
    project = perf_insights_project.PerfInsightsProject()
    test_relpaths = ['/' + _RelPathToUnixPath(x)
                     for x in project.FindAllTestModuleRelPaths()]

    tests = {'test_relpaths': test_relpaths}
    tests_as_json = json.dumps(tests)
    self.response.content_type = 'application/json'
    return self.response.write(tests_as_json)


class RunMapFunctionHandler(webapp2.RequestHandler):

  def post(self, *args, **kwargs):  # pylint: disable=unused-argument
    job_dict = json.loads(self.request.body)

    job = job_module.Job.FromDict(job_dict)

    job_with_filenames = job_module.Job(
        job.map_function_handle.ConvertHrefsToAbsFilenames(self.app),
        job.reduce_function_handle.ConvertHrefsToAbsFilenames(self.app))

    corpus_driver = local_directory_corpus_driver.LocalDirectoryCorpusDriver(
        trace_directory = kwargs.pop('_pi_data_dir'),
        url_resolver = self.app.GetURLForAbsFilename)

    # TODO(nduca): pass self.request.params to the map function [maybe].
    query_string = self.request.get('corpus_query', 'True')
    query = corpus_query.CorpusQuery.FromString(query_string)

    trace_handles = corpus_driver.GetTraceHandlesMatchingQuery(query)

    self._RunMapper(trace_handles, job_with_filenames)

  # TODO(eakuefner): Rename this and other things that assume we only have map
  def _RunMapper(self, trace_handles, job):
    self.response.content_type = 'application/json'
    output_formatter = json_output_formatter.JSONOutputFormatter(
        self.response.out)

    runner = map_runner.MapRunner(trace_handles, job,
                                  jobs=map_runner.AUTO_JOB_COUNT,
                                  output_formatters=[output_formatter])
    runner.Run()


class RunCloudMapperHandler(webapp2.RequestHandler):

  def post(self, *args, **kwargs):  # pylint: disable=unused-argument
    job_dict = json.loads(self.request.body)

    job = job_module.Job.FromDict(job_dict)

    job_with_filenames = job_module.Job(
        job.map_function_handle.ConvertHrefsToAbsFilenames(self.app),
        job.reduce_function_handle.ConvertHrefsToAbsFilenames(self.app))

    with open(job_with_filenames.map_function_handle.modules_to_load[0].filename, 'r') as f:
      mapper = f.read()
    with open(job_with_filenames.reduce_function_handle.modules_to_load[0].filename, 'r') as f:
      reducer = f.read()
    mapper_name = job_with_filenames.map_function_handle.function_name
    reducer_name = job_with_filenames.reduce_function_handle.function_name

    query_string = self.request.get('corpus_query', 'True')

    params = urllib.urlencode({
        'query': query_string,
        'mapper': mapper,
        'mapper_function': mapper_name,
        'reducer': reducer,
        'reducer_function': reducer_name,
        'revision': 'HEAD',
        'corpus': 'https://performance-insights.appspot.com',
        })
    cloud_mapper_url = 'http://localhost:8080'
    create_url = '%s/cloud_mapper/create' % cloud_mapper_url
    response = urllib2.urlopen(create_url, data=params)

    # TODO(simonhatch): Use /status endpoint.
    results = json.loads(response.read())
    if results['status']:
      jobid = results['jobid']

      status_url = '%s/cloud_mapper/status?jobid=%s' % (cloud_mapper_url, jobid)
      start_time = datetime.datetime.now()
      while datetime.datetime.now() - start_time < datetime.timedelta(seconds=120):
        time.sleep(1)
        print 'Waiting for results.'
        response = urllib2.urlopen(status_url)
        results = json.loads(response.read())
        if results['status'] == 'COMPLETE':
          print 'Mapping complete. Downloading results.'
          output_handle, output_name = tempfile.mkstemp()

          try:
            cloud_storage.Copy(results['data'], output_name)
          except cloud_storage.CloudStorageError:
            return

          map_results = ''
          with open(output_name, 'r') as f:
            map_results = f.read()
          os.close(output_handle)
          self.response.write(map_results)
          return


class PerfInsightsDevServerConfig(object):
  def __init__(self):
    self.project = perf_insights_project.PerfInsightsProject()

  def GetName(self):
    return 'perf_insights'

  def GetRunUnitTestsUrl(self):
    return '/perf_insights/tests.html'

  def AddOptionstToArgParseGroup(self, g):
    g.add_argument('--pi-data-dir',
                   default=self.project.perf_insights_test_data_path)

  def GetRoutes(self, args):  # pylint: disable=unused-argument
    return [
      Route('/perf_insights/tests', TestListHandler),
      Route('/perf_insights_examples/run_map_function',
            RunMapFunctionHandler,
            defaults={
              '_pi_data_dir':
                  os.path.abspath(os.path.expanduser(args.pi_data_dir))
            }),
      Route('/perf_insights_examples/run_cloud_mapper',
            RunCloudMapperHandler,
            defaults={
              '_pi_data_dir':
                  os.path.abspath(os.path.expanduser(args.pi_data_dir))
            })
    ]

  def GetSourcePaths(self, args):  # pylint: disable=unused-argument
    return list(self.project.source_paths)

  def GetTestDataPaths(self, args):  # pylint: disable=unused-argument
    return [('/perf_insights/test_data/',
             os.path.abspath(os.path.expanduser(args.pi_data_dir)))]
