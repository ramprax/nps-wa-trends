#!/usr/bin/env python

import re
from collections import OrderedDict

def split_time_name(openfilestream):
    date_fmt = 'dd/MM/yyyy'
    datetime_fmt = date_fmt + ' hh:mm:ss aa'
    datematchprog = re.compile('/2014 ([1-9]):')
    replacement = '/2014 0\\1:'
    for line in openfilestream:
        line = line.strip()
        if line:
            line = datematchprog.sub(replacement , line)
            #print line
            if len(line) <= len(datetime_fmt) or ':' != line[len(datetime_fmt)]:
                continue                
            datetime_str = line[:len(datetime_fmt)].strip()
            datestr = datetime_str[:len('dd/MM/yyyy')].strip()
            rest = line[len(datetime_fmt)+1:].strip()
            name_end = rest.find(':')
            if name_end >= 0:
                name = rest[:name_end].strip()
                msg = rest[name_end+1:].strip()
                yield datestr, datetime_str, name, msg

def count_by_date_name(iterable):
    date_name_count = OrderedDict()
    name_list = []
    for datestr, dt_str, name, msg in iterable:
        if not name in name_list:
            name_list.append(name)
        if datestr in date_name_count:
            name_count = date_name_count[datestr]
            if name in name_count:
                count = name_count[name]
                count = count + 1
                name_count[name] = count
            else:
                name_count[name] = 1
        else:
            name_count = {}
            date_name_count[datestr] = name_count
            name_count[name] = 1
    name_list.sort()
    yield ','.join(('Date', ','.join(name_list)))
    totcount = 0
    for datestr in date_name_count:
        name_count = date_name_count[datestr]
        rowarr = []
        rowarr.append(datestr)
        for name in name_list:
            if name in name_count:
                rowarr.append(str(name_count[name]))
                totcount = totcount + name_count[name]
            else:
                rowarr.append('0')
        yield ','.join(rowarr)
    #print totcount

if __name__ == '__main__':
    #for l in split_time_name('nps-wa-29-jul-2014_0928.txt'):
    #    print l
    import sys
    filename = sys.argv[1]
    with open(filename) as fd:
        for line in count_by_date_name(split_time_name(fd)):
            print line
