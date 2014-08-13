#!/usr/bin/env python

import datetime
import re
from collections import OrderedDict

def split_time_name(openfilestream):
    date_fmt = 'dd/MM/yyyy'
    datetime_fmt = date_fmt + ' hh:mm:ss aa'
    date_repl_prog = re.compile('^([1-9])/([0-9][0-9])/([1-9][0-9][0-9][0-9])')
    date_repl = '0\\1/\\2/\\3'
    time_repl_prog = re.compile('^([0-9][0-9])/([0-9][0-9])/([1-9][0-9][0-9][0-9]) ([1-9]):')
    time_repl = '\\1/\\2/\\3 0\\4:'
    for line in openfilestream.split('\n'):
        line = line.strip()
        #print len(line)
        #print '''### Raw line = '%s' ''' % line
        if line:
            line = date_repl_prog.sub(date_repl, line)
            line = time_repl_prog.sub(time_repl, line)
            #print '#### date subst line = ', line
            datestr = None
            datetime_str = None
            name = None
            msg = ''+line.strip() # Assume whole line is a message
            valid_datetime = True
            if len(line) >= len(datetime_fmt):
                #print line
                datetime_str = line[:len(datetime_fmt)].strip()
                try:
                    dtdt = datetime.datetime.strptime(datetime_str, '%d/%m/%Y %I:%M:%S %p')
                    valid_date_time = True
                except:
                    valid_date_time = False

                if valid_date_time:
                    datestr = datetime_str[:len('dd/MM/yyyy')].strip()
                    if len(line) > len(datetime_fmt):
                        rest = line[len(datetime_fmt)+1:].strip()
                    else:
                        rest = ''
                       
                    msg = ''+rest.strip() # Assume everything after date is message
                    name_end = rest.find(':')
                    if name_end >= 0:
                        name = rest[:name_end].strip()
                        name = ' '.join(name.split()) # Get rid of double spaces in names
                        msg = ''+rest[name_end+1:].strip() # Everything after name is msg

            yield datestr, datetime_str, (name.lower() if name else name), msg.lower()

def count_by_date_name(iterable, end_date):
    date_name_count = OrderedDict()
    name_list = []
    end_date_reached = False
    today_text = ''
    all_time_text = ''
    
    for datestr, datetime_str, name, msg in iterable:
        if not datestr:
            all_time_text = ' '.join((all_time_text, msg))
            if end_date_reached:
                today_text = ' '.join((today_text, msg))
            continue
        elif datestr == end_date:
            end_date_reached = True
            all_time_text = ' '.join((all_time_text, msg))
            today_text = ' '.join((today_text, msg))
        elif end_date_reached:
            break
        else:
            all_time_text = ' '.join((all_time_text, msg))
      

        if not name:
            continue
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
    
    print 'Date keys: ', date_name_count.keys()
    
    tot_count_by_name = [0] * len(name_list)
    for datestr in date_name_count:
        name_count = date_name_count[datestr]
        rowarr = []
        rowarr.append(datestr)
        for i, name in enumerate(name_list):
            if name in name_count:
                rowarr.append(str(name_count[name]))
                tot_count_by_name[i] = tot_count_by_name[i] + name_count[name]
            else:
                rowarr.append('0')
        yield ','.join(rowarr)
    yield ','.join(('Totals', ','.join( (str(x) for x in tot_count_by_name) )))
    
    yield (today_text, all_time_text)
    
    print '##### Finished'

def get_summary_data(instream, datestr):
    summary_data = {}
    #print '#### datestr = ', datestr
    totalsLineReached = False
    lastDateReached = False
    csv_content_arr = []
    datestr_arr = []
    date_msg_totals = []
    today_msgs_by_name = ''
    all_time_msgs_by_name = ''
    
    stat_iter = count_by_date_name(split_time_name(instream), datestr)
    
    for line in stat_iter:
        #print '#### line = ', line
        if not line:
            continue
        if line.startswith('Date'):
            names_line = line
            csv_content_arr.append(line)
            continue
        if line.startswith('Totals'):
            totalsLineReached = True

        if line.startswith(datestr):
            today_msgs_by_name = line
            lastDateReached = True
        elif lastDateReached and not totalsLineReached:
            continue

        csv_content_arr.append(line)
        if totalsLineReached:
            all_time_msgs_by_name = line
            break

        line_cols = line.split(',')
        # Extract & append date
        datestr_arr.append(line_cols[0]) # append date
        # Get sum for each date
        date_msg_totals.append(sum([ int(x) for x in line_cols[1:] ]))
        
    csv_content = '\n'.join(csv_content_arr)
    #print type(csv_content), len(csv_content)
    #print datestr_arr
    #print date_msg_totals
    today_msgs_by_name = [ (int(x) if x else 0) for x in today_msgs_by_name.split(',')[1:] ]
    all_time_msgs_by_name = [ (int(x) if x else 0) for x in all_time_msgs_by_name.split(',')[1:] ]
    names_line = names_line.split(',')[1:]
    
    summary_data['CSV'] = csv_content
    summary_data['DATES'] = datestr_arr
    summary_data['TOTAL_MSGS_BY_DATE'] = date_msg_totals
    summary_data['NAMES'] = names_line
    summary_data['TODAY_MSGS_BY_NAME'] = today_msgs_by_name
    summary_data['ALL_TIME_MSGS_BY_NAME'] = all_time_msgs_by_name
    
    today_words, all_time_words = next(stat_iter)
    print 'today len', len(today_words)
    print 'alltime len', len(all_time_words)
    summary_data['TODAY_WORDS'] = today_words
    summary_data['ALL_TIME_WORDS'] = all_time_words
    
    return summary_data


if __name__ == '__main__':
    #for l in split_time_name('nps-wa-29-jul-2014_0928.txt'):
    #    print l
    import sys
    filename = sys.argv[1]
    enddatestr = sys.argv[2]
    #with open(filename) as fd:
    #    for line in count_by_date_name(split_time_name(fd.read()), enddatestr):
    #        print 'csv line: ', line

    with open(filename) as fd:
        summary = get_summary_data(fd.read(), enddatestr)
        #print 'summary: ', summary

