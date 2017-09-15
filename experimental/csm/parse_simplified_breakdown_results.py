"""TODO(dproy): This file is awkwardly coupled with parse_ctp_results.py right
now, and also contains lots of copy pasta. Consider refactoring.
"""

from parse_ctp_results import load_json_results_from_file
import csv
import sys
import traceback

def get_csv_dicts(result_json_list):
  """
  Converts list of trace_data to list of csv_dict, a flat dictionary that will
  be written out to the csv file.

  This function is truly a hallmark of defensive programming.
  """
  x_to_y_csv_dicts = []
  per_second_csv_dicts = []
  samples_without_breakdown = 0
  mapper_failures = 0
  unhandled_errors = 0
  telemetry_info_error = 0

  for results_json in result_json_list:
    pairs = results_json['pairs']
    if 'TelemetryInfo' not in pairs:
      # This result was a probably total failure and it cannot be processed at
      # all. Print the raw json and give up.
      print 'Ignoring result: No TelemetryInfo found'
      print results_json
      telemetry_info_error += 1
      continue
    telemetry_info = pairs['TelemetryInfo']
    if 'stories' not in telemetry_info:
      print 'Ignoring result: stories not in TelemetryInfo'
      telemetry_info_error += 1
      continue

    storyTags = telemetry_info['storyTags']
    cache_temperature_tags = [t for t in storyTags if 'cache_temperature' in t]
    if len(cache_temperature_tags) == 0:
      print 'Ignoring result: cache temperature not in TelemetryInfo'
      telemetry_info_error += 1
      continue

    if len(cache_temperature_tags) > 1:
      print "Internal Error: More than one cache-temperature in story tags"
      unhandled_errors += 1
      continue

    cache_temperature_tag = cache_temperature_tags[0]

    failures = results_json['failures']
    for f in failures:
      print "Result contains failures:"
      # Some results have partial failures. There are lot of edge cases that
      # may not be worth fixing, so print the failures and carry on processing
      # whatever possible.
      print f

    try:
      metadata_dict = {}
      x_to_y_dict = {}
      per_second_dict = {}

      stories = telemetry_info['stories']
      assert len(stories) == 1
      metadata_dict['site'] = stories[0]
      cache_temperature = cache_temperature_tag.split(':')[1]
      metadata_dict['cache_temperature'] = cache_temperature
      mapper_errors = set()

      for key, data in pairs.iteritems():
        # data is of the form
        # {
        #   value: number
        #   breakdown: {
        #     breakdownName: number
        #     ...
        #   }
        # }
        if key == 'TelemetryInfo':
          continue
        if key == 'navToOnLoad':
          # Ignore navToOnLoad. We should remove it from the metric anyways.
          continue

        metric_name = key
        # Choosing which dict to put data in.
        # Hacky but gets the job done.
        if 'sec' in metric_name:
          target_dict = per_second_dict
        else:
          target_dict = x_to_y_dict

        # We have metric_name-total and metric_name-breakdown-$breakdownName
        if 'error' in data:
          mapper_errors.add(data['error'])
          continue

        target_dict[metric_name + '-total'] = data['value']
        if 'breakdown' in data:
          breakdown = data['breakdown']
          for breakdown_type in breakdown:
            columnName = metric_name + '-' + breakdown_type
            target_dict[columnName] = breakdown[breakdown_type]
        else:
          samples_without_breakdown += 1

      if len(mapper_errors) > 0:
        # Do not add the record if there are any mapper errors.
        print "Mapper errors encountered: "
        print "site: ", metadata_dict['site']
        print "cache_temperature: ", metadata_dict['cache_temperature']
        print "mapper errors: ", mapper_errors
        mapper_failures += 1
      else:
        x_to_y_dict.update(metadata_dict)
        per_second_dict.update(metadata_dict)
        x_to_y_csv_dicts.append(x_to_y_dict)
        per_second_csv_dicts.append(per_second_dict)

    except Exception as e:
      # Catching all other errors. Results json files contain all kinds of
      # errors and it's not desirable to halt the entire script because 1 in
      # 15000 entries was malformed.
      print "Error while processing result this results record:"
      print results_json
      print "Error:"
      traceback.print_exc()
      print "Skipping result and moving on"
      unhandled_errors += 1

  success_count = len(x_to_y_csv_dicts)
  print '------------------------------------------------'
  print "Total input data rows: ", len(result_json_list)
  print "Successful data extraction: ", success_count
  print "Mapper failures: ", mapper_failures
  print "Telemetry info error: ", telemetry_info_error
  print "Unhandled errors: ", unhandled_errors
  assert len(result_json_list) == (success_count +
      mapper_failures + telemetry_info_error + unhandled_errors)
  print "Samples without breakdown: ", samples_without_breakdown
  return {
    'x_to_y': x_to_y_csv_dicts,
    'per_second': per_second_csv_dicts
  }

def write_csv(csv_dicts, output_filename):
  # Not all histograms containn all metrics so we need to gather all the
  # possible fieldnames first.
  fieldnames = set()
  for d in csv_dicts:
    fieldnames = fieldnames.union(d.keys())

  with open(output_filename, 'w') as f:
    writer = csv.DictWriter(f, list(fieldnames), extrasaction='ignore')
    writer.writeheader()
    writer.writerows(csv_dicts)
  print "Wrote csv output to " + output_filename

def validate_dicts(input_dict_list):
  negative_values = 0;
  for d in input_dict_list:
    for k, v in d.iteritems():
      try:
        floatv = float(v)
        if floatv < 0:
          print "WARNING: Negative value found: "
          print k, v
          print "Site: ", d['site']
          negative_values += 1
      except:
        pass
  print "Num negative values found: ", negative_values

def main():
  # TODO(dproy): It may eventually make sense to use a real argument parser.
  if len(sys.argv) < 2:
    print "Usage: {0} <ctp-results> [output-filename]".format(sys.argv[0])
    print "<ctp-results> is the results file produced by chrome trace processor."
    print "[output-filename] is the produced csv file. Defaults to out.csv."

  input_filename = sys.argv[1]
  if len(sys.argv) > 2:
    output_filename_prefix = sys.argv[2]
  else:
    output_filename_prefix = "out"

  output_filename = output_filename_prefix + '.csv'

  result_json_list = load_json_results_from_file(input_filename)
  csv_dicts = get_csv_dicts(result_json_list)
  x_to_y_csv_dicts = csv_dicts['x_to_y']
  per_second_csv_dicts = csv_dicts['per_second']
  print "Validating x to y dicts for negative values..."
  validate_dicts(x_to_y_csv_dicts)
  print  "Validating per second dicts for negative values..."
  validate_dicts(per_second_csv_dicts)
  import IPython; IPython.embed()
  write_csv(x_to_y_csv_dicts, output_filename_prefix + '_x-to-y.csv')
  write_csv(per_second_csv_dicts, output_filename_prefix + '_per-sec.csv')

  print "Total results processed:", len(result_json_list)


if __name__ == "__main__":
  main()
