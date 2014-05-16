# Search for the weekly summary reports from bugs.python.org in the
# python-dev archives and plot the result.
#
# $ issuestats.py collect
#
# Collects statistics from the mailing list and saves to
# issue.stats.json
#
# $ issuestats.py plot
#
# Written by Ezio Melotti.
# Based on the work of Petri Lehtinen (https://gist.github.com/akheron/2723809).
#
# Requires Python 3.
#
# This script is used to generate a JSON file with historical data that can
# be copied in the html/ dir of the bugs.python.org Roundup instance and used
# by the html/issue.stats.html page.  The roundup-summary script can update the
# JSON file weekly.
#


import os
import re
import sys
import json
import gzip
import errno
import argparse
import datetime
import tempfile
import webbrowser
import urllib.parse
import urllib.request

from collections import defaultdict


MONTH_NAMES = [datetime.date(2012, n, 1).strftime('%B') for n in range(1, 13)]
ARCHIVE_URL = 'http://mail.python.org/pipermail/python-dev/%s'

STARTYEAR = 2011
STARTMONTH = 1  # February

NOW = datetime.date.today()
ENDYEAR = NOW.year
ENDMONTH = NOW.month

STATISTICS_FILENAME = 'issue.stats.json'

activity_re = re.compile('ACTIVITY SUMMARY \((\d{4}-\d\d-\d\d) - '
                         '(\d{4}-\d\d-\d\d)\)')
count_re = re.compile('\s+(open|closed|total)\s+(\d+)\s+\(([^)]+)\)')
patches_re = re.compile('Open issues with patches: (\d+)')


def find_statistics(source):
    print(source)
    monthly_data = {}
    with gzip.open(source) as file:
        parsing = False
        for line in file:
            line = line.decode('utf-8')
            if not parsing:
                m = activity_re.match(line)
                if not m:
                    continue
                start_end = m.groups()
                if start_end in monthly_data:
                    continue
                monthly_data[start_end] = weekly_data = {}
                parsing = True
                continue
            m = count_re.match(line)
            if parsing and m:
                type, count, delta = m.groups()
                weekly_data[type] = int(count)
                weekly_data[type + '_delta'] = int(delta)
            m = patches_re.match(line)
            if parsing and m:
                weekly_data['patches'] = int(m.group(1))
                parsing = False
    print('  ', len(monthly_data), 'reports found')
    return monthly_data


def collect_data():
    try:
        os.mkdir('cache')
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise

    statistics = {}

    for year in range(STARTYEAR, ENDYEAR + 1):
        # Assume STARTYEAR != ENDYEAR
        if year == STARTYEAR:
            month_range = range(STARTMONTH, 12)
        elif year == ENDYEAR:
            month_range = range(0, ENDMONTH)
        else:
            month_range = range(12)

        for month in month_range:
            prefix = '%04d-%s' % (year, MONTH_NAMES[month])

            archive = prefix + '.txt.gz'
            archive_path = os.path.join('cache', archive)

            if not os.path.exists(archive_path):
                print('Downloading %s' % archive)
                url = ARCHIVE_URL % urllib.parse.quote(archive)
                urllib.request.urlretrieve(url, archive_path)


            print('Processing %s' % prefix)
            statistics.update(find_statistics(archive_path))


    statistics2 = defaultdict(list)
    for key, val in sorted(statistics.items()):
        statistics2['timespan'].append(key)
        for k2, v2 in val.items():
            statistics2[k2].append(v2)

    with open(STATISTICS_FILENAME, 'w') as fobj:
        json.dump(statistics2, fobj)

    print('Now run "plot".')


HTML = """<!DOCTYPE html>
<html>
<head>
<script type="text/javascript" src="http://cdn.jsdelivr.net/jquery/2.1.1/jquery.min.js"></script>
<script type="text/javascript" src="http://cdn.jsdelivr.net/jqplot/1.0.8/jquery.jqplot.js"></script>
<script type="text/javascript" src="http://cdnjs.cloudflare.com/ajax/libs/jqPlot/1.0.8/plugins/jqplot.dateAxisRenderer.min.js"></script>
<script type="text/javascript">
function make_chart(id, title, dates, values) {
    var data = [];
    for (var k = 0; k < dates.length; k++) {
        data.push([dates[k], values[k]]);
    }
    var plot = $.jqplot(id, [data], {
        title: title,
        series: [{showMarker:false}],
        axes: {xaxis:{renderer:$.jqplot.DateAxisRenderer}},
    });
}
$(document).ready(function(){
    var j = %s;
    var dates = [];
    for (var k = 0; k < j.timespan.length; k++) {
        console.log(j.timespan[k][1]);
        dates.push(j.timespan[k][1]);
    }
    console.log(dates);
    var open = [];
    for (var k = 0; k < dates.length; k++) {
        open.push([dates[k], j.open[k]]);
    }
    console.log(open);
    make_chart('open', 'Open issues', dates, j.open);
    make_chart('open_delta', 'Open issues (deltas)', dates, j.open_delta);
    make_chart('open_week', 'Opened per week', dates, j.wopened);
    make_chart('closed', 'Closed issues', dates, j.closed);
    make_chart('closed_delta', 'Closed issues (deltas)', dates, j.closed_delta);
    make_chart('closed_week', 'Closed per week', dates, j.wclosed);
    make_chart('total', 'Total issues', dates, j.total);
    make_chart('total_delta', 'Total issues (deltas)', dates, j.total_delta);
    make_chart('patches', 'Open issues with patches', dates, j.patches);
});
</script>
<link rel="stylesheet" type="text/css" href="http://cdn.jsdelivr.net/jqplot/1.0.8/jquery.jqplot.css">
<style type="text/css">div { margin-bottom: 1em; }</style>
</head>
<body>
<div id="open"></div>
<div id="open_delta"></div>
<div id="open_week"></div>
<div id="closed"></div>
<div id="closed_delta"></div>
<div id="closed_week"></div>
<div id="total"></div>
<div id="total_delta"></div>
<div id="patches"></div>
</body>
</html>
"""

def plot_statistics():
    try:
        with open(STATISTICS_FILENAME) as j:
            json = j.read()
    except FileNotFoundError:
        sys.exit('You need to run "collect" first.')
    with tempfile.NamedTemporaryFile('w', delete=False) as tf:
        tf.write(HTML % json)
    webbrowser.open(tf.name)



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['collect', 'plot'])

    args = parser.parse_args()

    if args.command == 'collect':
        collect_data()
    elif args.command == 'plot':
        plot_statistics()


if __name__ == '__main__':
    main()
