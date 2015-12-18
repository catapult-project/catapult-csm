# Copyright (c) 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import json
import logging
import os
import urllib
import uuid
import webapp2

from google.appengine.api import modules
from google.appengine.api import taskqueue
from google.appengine.api import urlfetch
from perf_insights.endpoints.cloud_mapper import job_info
from perf_insights import cloud_config

def _is_devserver():
  return os.environ.get('SERVER_SOFTWARE','').startswith('Development')

_DEFAULT_MAPPER = """
<!DOCTYPE html>
<!--
Copyright (c) 2015 The Chromium Authors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be
found in the LICENSE file.
-->
<link rel="import" href="/tracing/base/units/units.html">
<link rel="import" href="/tracing/base/units/histogram.html">
<link rel="import" href="/perf_insights/mre/function_handle.html">
<link rel="import" href="/perf_insights/mappers/slice_cost.html">
<link rel="import" href="/perf_insights/mappers/thread_grouping.html">
<link rel="import" href="/tracing/base/iteration_helpers.html">
<link rel="import" href="/tracing/extras/chrome/chrome_model_helper.html">
<link rel="import" href="/tracing/extras/rail/rail_interaction_record.html">
<link rel="import" href="/tracing/extras/rail/rail_score.html">
<link rel="import" href="/tracing/model/ir_coverage.html">

<script>
'use strict';

tr.exportTo('pi.m', function() {

  function getWeatherReportFromModel(model) {
    // Organize all RAIL IRs by type and name in a tree. A node of this tree is
    // a dict with keys |overallScore|, |scores| and optionally |subTypes|.
    // |overallScore| and |scores| are mutually exclusive. If |overallScore| is
    // present it contains the overall rail score of all IRs under the tree. If
    // |scores| is present it contains an array with the IR scores of all the
    // IRs under the tree. |subTypes| is a map from a subType (IR type, IR name)
    // to a node.
    var irTree = {
      overallScore: 0
    };
    var allIRs = [];
    function addIRToNode(node, ir, path) {
      if (node.overallScore === undefined) {
        // For a node without overall rail score keep the individual IR scores.
        node.irScores = node.irScores || [];
        node.irScores.push(ir.railScore);
      }
      if (path.length === 0)
        return;
      var subType = path[0];
      node.subTypes = node.subTypes || {};
      node.subTypes[subType] = node.subTypes[subType] || {};
      addIRToNode(node.subTypes[subType], ir, path.slice(1));
    }
    model.interactionRecords.forEach(function(ir) {
      if (!(ir instanceof tr.e.rail.RAILInteractionRecord))
        return;
      allIRs.push(ir);
      var path = [
        tr.e.rail.userFriendlyRailTypeName(ir.railTypeName),
        ir.name || 'Unnamed'
      ];
      addIRToNode(irTree, ir, path);
    });
    irTree.overallScore = (new tr.e.rail.RAILScore(allIRs)).overallScore;

    var railTypeNameByGUID = getRAILTypeNameForEventsByGUID(model, allIRs);
    var threadGrouping = new pi.m.ThreadGrouping();
    threadGrouping.autoInitUsingHelpers(model);

    var wr = {
      irTree: irTree,
      irCoverage: tr.model.getIRCoverageFromModel(model),
      sliceCosts: pi.m.getSliceCostReport(model, threadGrouping,
                                          railTypeNameByGUID),
      sourceURL: model.sourceURLThatCreatedThisTrace
    };
    return wr;
  }

  function getRAILTypeNameForEventsByGUID(model, railIRs) {
    var railTypeNameByGUID = {};
    railIRs.forEach(function applyAssociatedToRTN(ir) {
      ir.associatedEvents.forEach(function applyEventToRTN(event) {
        // Unassociated events have already been assigned to a RTN.
        if (railTypeNameByGUID[event.guid] !== undefined)
          return;
        railTypeNameByGUID[event.guid] = tr.e.rail.userFriendlyRailTypeName(
            ir.railTypeName);
      }, this);
    }, this);

    model.iterateAllEvents(function storeEventToUnassociatedSet(event) {
      if (railTypeNameByGUID[event.guid] !== undefined)
        return;
      railTypeNameByGUID[event.guid] = 'Unknown';
    });
    return railTypeNameByGUID;
  }

  function weatherReportMapFunction(results, model) {
    var wr = pi.m.getWeatherReportFromModel(model);
    results.addResult('wr', wr);
  }
  pi.mre.FunctionRegistry.register(weatherReportMapFunction);

  return {
    getWeatherReportFromModel: getWeatherReportFromModel,
    weatherReportMapFunction: weatherReportMapFunction
  };
});

</script>
"""

_DEFAULT_FUNCTION = 'weatherReportMapFunction'

_FORM_HTML = """
<!DOCTYPE html>
<html>
<body>
<form action="/cloud_mapper/create" method="POST">
Mapper: <br><textarea rows="50" cols="80" name="mapper">{mapper}</textarea>
<br>
FunctionName: <br><input type="text" name="mapper_function"
    value="{mapper_function}"/>
<br>
Query: <br><input type="text" name="query" value="{query}"/>
<br>
Corpus: <br><input type="text" name="corpus" value="{corpus}"/>
<br>
<input type="submit" name="submit" value="Submit"/>
</form>
</body>
</html>
"""

class TestPage(webapp2.RequestHandler):

  def get(self):
    form_html = _FORM_HTML.format(mapper=_DEFAULT_MAPPER,
                                  mapper_function=_DEFAULT_FUNCTION,
                                  query='MAX_TRACE_HANDLES=10',
                                  corpus=cloud_config.Get().default_corpus)
    self.response.out.write(form_html)

app = webapp2.WSGIApplication([('/cloud_mapper/test', TestPage)])
