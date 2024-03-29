<!-- Copyright 2016 The Chromium Authors. All rights reserved.
     Use of this source code is governed by a BSD-style license that can be
     found in the LICENSE file.
-->

# HistogramSet JSON Format

This document assumes familiarity with the concepts introduced in
[how-to-write-metrics](/docs/how-to-write-metrics.md).

HistogramSet JSON contains an unordered array of dictionaries, where each
dictionary represents either a Histogram or a Diagnostic.

```javascript
[
  {
    "name": "my amazing metric",
    "guid": "123e4567-e89b-12d3-a456-426655440000",
    "unit": "ms",
    "binBoundaries": [0, [0, 100, 10]],
    "shortName": "my metric",
    "description": "this is my awesome amazing metric",
    "diagnostics": {
      "telemetry": "923e4567-e89b-12d3-a456-426655440000",
    },
    "sampleValues": [0, 1, 42, -999999999.99999, null],
    "maxNumSampleValues": 1000,
    "numNans": 1,
    "nanDiagnostics": [
      {
        "events": {
          "type": "RelatedEventSet",
          "events": [
            {
              "stableId": "a.b.c", "title": "Title", "start": 0, "duration": 1
            }
          ]
        }
      }
    ],
    "running": [5, 42, 0, -1, -999, -900, 100],
    "allBins": {
      "0": [1],
      "1": [1],
    },
    "summaryOptions": {
      "nans": true,
      "percentile": [0.5, 0.95, 0.99],
    },
  },
  {
    "guid": "923e4567-e89b-12d3-a456-426655440000",
    "type": "TelemetryInfo",
    "benchmarkName": "memory",
    "benchmarkStartMs": 1234567890,
    "label": "abc",
    "storyDisplayName": "my story",
    "storyGroupingKeys": {"state": "pre"},
    "storysetRepeatCounter": 0,
  },
]
```

## Histograms

### Required fields

 * `name`: any string
 * `guid`: string UUID, allows Histograms to reference other Histograms via
   RelatedHistogram Diagnostics
 * `unit`: underscore-separated string of 1 or 2 parts:
    * The required unit base name must be one of
       * ms
       * tsMs
       * n%
       * sizeInBytes
       * J
       * W
       * unitless
       * count
       * sigma
    * Optional improvement direction must be one of
       * biggerIsBetter
       * smallerIsBetter

### Optional fields

 * `shortName`: any string, allows metrics to make results more user-friendly
 * `description`: any string, allows metrics to explain results in more depth
 * `binBoundaries`: an array that describes how to build bin boundaries
   The first element must be a number that specifies the boundary between the
   underflow bin and the first central bin. Subsequent elements can be either
    * numbers specifying bin boundaries, or
    * arrays of 3 numbers that specify how to build sequences of bin boundaries:
       * The first of which is an enum:
          * 0 (LINEAR)
          * 1 (EXPONENTIAL)
       * The second number is the maximum bin boundary of the sequence.
       * The third and final number is the number of bin boundaries in the
         sequence.
   If `binBoundaries` is undefined, then the Histogram contains single bin whose
   range spans `-Number.MAX_VALUE` to `Number.MAX_VALUE`
 * `diagnostics`: a DiagnosticMap that pertains to the entire Histogram, allows
   metrics to help users diagnose regressions and other problems.
   This can reference shared Diagnostics by `guid`.
 * `sampleValues`: array of sample values to support Mann-Whitney U hypothesis
   testing to determine the significance of the difference between two
   Histograms.
 * `maxNumSampleValues`: maximum number of sample values
   If undefined, defaults to allBins.length * 10.
 * `numNans`: number of non-numeric samples added to the Histogram
 * `nanDiagnostics`: an array of DiagnosticMaps for non-numeric samples
 * `running`: running statistics, an array of 7 numbers: count, max, meanlogs,
   mean, min, sum, variance
 * `allBins`: either an array of Bins or a dictionary mapping from index to Bin:
   A Bin is an array containing either 1 or 2 elements:
    * Required number bin count,
    * Optional array of sample DiagnosticMaps
 * `summaryOptions`: dictionary mapping from option names `avg, geometricMean,
   std, count, sum, min, max, nans` to boolean flags. The special option
   `percentile` is an array of numbers between 0 and 1. This allows metrics to
   specify which summary statistics are interesting and should be displayed.

DiagnosticMap is a dictionary mapping strings to Diagnostic dictionaries.

## Diagnostics

The only field that is required for all Diagnostics, `type`, must be one of
 * `GenericSet`
 * `RelatedEventSet`
 * `Breakdown`
 * `RelatedHistogramSet`
 * `RelatedHistogramMap`
 * `RelatedHistogramBreakdown`
 * `TelemetryInfo`
 * `BuildbotInfo`
 * `Scalar`

If a Diagnostic is in the root array of the JSON, then it is shared, so it may be
referenced by multiple Histograms. Shared Diagnostics must contain a string
field `guid` containing a UUID.

If a Diagnostic is contained in a Histogram, then it must not have a `guid`
field.

The other fields of Diagnostic dictionaries depend on `type`.

### TelemetryInfo

This tracks telemetry parameters when the Histogram was produced to allow users
to compare or merge results across similar telemetry story runs.

 * `benchmarkName`: string
 * `benchmarkStartMs`: number of ms since unix epoch
 * `label`: string
 * `legacyTIRLabel`: string
 * `storyDisplayName`: string
 * `storyGroupingKeys`: dictionary mapping from strings to strings
 * `storysetRepeatCounter`: number

### BuildbotInfo

This tracks buildbot parameters when the Histogram was produced to allow users
to compare or merge results across similar bots.

 * `displayMasterName`: string
 * `displayBotName`: string
 * `buildbotMasterName`: string
 * `buildbotName`: string
 * `buildNumber`: number
 * `logUri`: string

### GenericSet

This allows metrics to store arbitrary untyped data in Histograms.

 * `values`: array of any JSON data.

### Scalar

Metrics should not use Scalar diagnostics since they cannot be safely merged.

 * `value`: a dictionary containing a string `unit` and a number `value`

### Breakdown

This allows metrics to explain the magnitude of a sample as composed of various
categories.

 * `values`: required dictionary mapping from a string category name to number values
 * `colorScheme`: optional string specifying how the bar chart should be colored

### RelatedHistogramSet

This allows metrics to annotate which Histograms are related to other
Histograms.

 * `guids`: list of guids of related Histograms

### RelatedHistogramMap

This allows metrics to annotate which Histograms are related to other
Histograms, and annotate the nature of the relationship with a custom string
name.

 * `values`: dictionary mapping from custom string name to the related
   Histogram's string guid

### RelatedHistogramBreakdown

This allows metrics to explain the magnitudes of the samples in a Histogram
collectively as composed of various categories.

 * `values`: dictionary mapping from custom string name to the related
   Histogram's string guid

### RelatedEventSet

This allows metrics to explain the magnitude of a sample as a parameter of a
specific event or set of events in a trace.

 * `events`: array of dictionaries containing `stableId`, `title`, `start`,
   `duration` fields of Events

### DateRange

This is a Range of Dates.

 * `min`: Unix timestamp in ms
 * `max`: optional Unix timestamp in ms
