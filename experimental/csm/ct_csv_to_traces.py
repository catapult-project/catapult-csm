import csv
import sys

def csv_to_traces(infile, outfile):
  traces = []
  with open(infile) as inf:
    results = csv.DictReader(inf)
    for r in results:
      for t in r['trace'].split(','):
        traces.append(t)

  with open(outfile, 'w') as outf:
    for trace in traces:
      outf.write(trace + '\n')

def main():
  if len(sys.argv) < 3:
    print "Usage: {0} <input-file> <output-file>".format(sys.argv[0])
    return

  input_filename = sys.argv[1]
  output_filename = sys.argv[2]
  csv_to_traces(input_filename, output_filename)

if __name__ == "__main__":
  main()
