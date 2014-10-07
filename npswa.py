#!/usr/bin/env python

import datetime
import re
from collections import OrderedDict

DATEFMT_MAP = {
    'DD/MM/YYYY':'%d/%m/%Y',
    'MM/DD/YYYY':'%m/%d/%Y'
}

TIMEFMT_MAP = {
    'hh:mm:ss aa':'%I:%M:%S %p',
    'HH:mm:ss':'%H:%M:%S',
    'HH:mm':'%H:%M'
}

def split_time_name(openfilestream, datefmt_str, timefmt_str):
    date_fmt = datefmt_str
    datetime_fmt = datefmt_str + ' ' + timefmt_str

    cdate_fmt = DATEFMT_MAP[date_fmt]
    cdatetime_fmt = cdate_fmt + ' ' + TIMEFMT_MAP[timefmt_str]

    date_repl_prog = re.compile('^([1-9])/([0-9][0-9])/([1-9][0-9][0-9][0-9])')
    date_repl = '0\\1/\\2/\\3'
    time_repl_prog = re.compile('^([0-9][0-9])/([0-9][0-9])/([1-9][0-9][0-9][0-9]) ([1-9]):')
    time_repl = '\\1/\\2/\\3 0\\4:'
    lineno = 0
    for line in openfilestream.split('\n'):
        lineno = lineno + 1
        #print 'Line # ', lineno
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
            dtdt = None
            valid_datetime = True
            if len(line) >= len(datetime_fmt):
                #print line
                datetime_str = line[:len(datetime_fmt)].strip()
                try:
                    dtdt = datetime.datetime.strptime(datetime_str, cdatetime_fmt)
                    valid_date_time = True
                except:
                    valid_date_time = False

                if valid_date_time:
                    datestr = datetime_str[:len(date_fmt)].strip()
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
            if '<media omitted>' == msg:
                msg = ' '
            yield datestr, datetime_str, dtdt, (name.lower() if name else name), msg.lower()

def count_by_date_name(iterable, end_date):
    date_name_count = OrderedDict()
    name_list = []
    end_date_reached = False
    today_text = ''
    all_time_text = ''
    
    msg_count_by_minute_of_day = [0] * (24 * 60)
    
    for datestr, datetime_str, msg_datetime, name, msg in iterable:
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
            name_count = OrderedDict()
            date_name_count[datestr] = name_count
            name_count[name] = 1
        
        msg_minute_of_day = msg_datetime.hour * 60 + msg_datetime.minute
        msg_count_by_minute_of_day[msg_minute_of_day] = (
            msg_count_by_minute_of_day[msg_minute_of_day] + 1
        )

    return {
        'NAMES': sorted(name_list),
        'DATE_NAME_COUNT': date_name_count,
        'TODAY_WORDS':today_text,
        'ALL_TIME_WORDS':all_time_text,
        'MSGS_BY_MINUTE_OF_DAY':msg_count_by_minute_of_day
    }
    
def get_summary_data(instream, today_datestr, datefmt_str, timefmt_str):
    summary_data = {}
    #print '#### datestr = ', datestr
    totalsLineReached = False
    lastDateReached = False
    csv_content_arr = []
    datestr_arr = []
    date_msg_totals = []
    today_msgs_by_name = []
    all_time_msgs_by_name = []
    
    summary = count_by_date_name(
        split_time_name(
            instream,
            datefmt_str,
            timefmt_str
        ),
        today_datestr
    )

    name_list = summary['NAMES']
    date_name_count = summary['DATE_NAME_COUNT']

    # CSV Header
    csv_content_arr.append(','.join(('Date', ','.join(name_list))))

    tot_count_by_name = [0] * len(name_list)
    for datestr in date_name_count:
        
        # Add date to date array
        datestr_arr.append(datestr)
        
        name_count = date_name_count[datestr]
        rowarr = []
        rowarr.append(datestr)
        for i, name in enumerate(name_list):
            if name in name_count:
                rowarr.append(str(name_count[name]))
                tot_count_by_name[i] = tot_count_by_name[i] + name_count[name]
            else:
                name_count[name] = 0
                rowarr.append('0')

        # CSV entry for current date
        csv_content_arr.append(','.join(rowarr))
        if datestr == today_datestr:
            today_msgs_by_name = [ name_count[x] for x in name_list ]
        date_msg_totals.append(sum( (name_count[x] for x in name_count) ))

    # Total by name
    csv_content_arr.append(','.join(('Totals', ','.join( (str(x) for x in tot_count_by_name) ))))
    
    csv_content = '\n'.join(csv_content_arr)
    #print type(csv_content), len(csv_content)
    #print datestr_arr
    #print date_msg_totals
    #all_time_msgs_by_name = tot_count_by_name #[ (int(x) if x else 0) for x in all_time_msgs_by_name.split(',')[1:] ]
    
    summary_data['CSV'] = csv_content
    summary_data['DATES'] = datestr_arr
    summary_data['TOTAL_MSGS_BY_DATE'] = date_msg_totals
    summary_data['NAMES'] = name_list
    summary_data['TODAY_MSGS_BY_NAME'] = today_msgs_by_name
    summary_data['ALL_TIME_MSGS_BY_NAME'] = tot_count_by_name
    
    #print 'today len', len(today_words)
    #print 'alltime len', len(all_time_words)
    summary_data['TODAY_WORDS'] = summary['TODAY_WORDS']
    summary_data['ALL_TIME_WORDS'] = summary['ALL_TIME_WORDS']

    summary_data['MSGS_BY_MINUTE_OF_DAY'] = summary['MSGS_BY_MINUTE_OF_DAY']
    
    return summary_data

def test_summary():
    input_data = '''
01/01/2000 8:47:15 pm: Abc Def: Hi
01/01/2000 8:48:15 pm: Abc Def: Hi
01/01/2000 8:49:15 pm: Ghi Jkl: Hi Abc
02/01/2000 8:47:15 pm: Abc Def: Hi Def
02/01/2000 8:49:15 pm: Ghi Jkl: Hi Abc
03/01/2000 8:47:15 pm: Abc Def: Hi
'''
    datefmt = 'DD/MM/YYYY'
    timefmt = 'hh:mm:ss aa'
    today_date = '03/01/2000'

    expected_csv = '''Date,abc def,ghi jkl
01/01/2000,2,1
02/01/2000,1,1
03/01/2000,1,0
Totals,4,2'''
    expected_dates = ['01/01/2000','02/01/2000','03/01/2000']
    expected_tot_msg_by_dt =[3, 2, 1]
    expected_names = ['abc def', 'ghi jkl']
    expected_today_msg_by_name = [1,0]
    expected_all_msg_by_name = [4,2]
    expected_today_words = 'hi'
    expected_all_words = 'Hi Hi Hi Abc Hi Def Hi Abc Hi'.lower()
    
    expected_msg_by_minute = [0] * (24 * 60)
    expected_msg_by_minute[20*60+47] = 3 # 8:47 pm
    expected_msg_by_minute[20*60+48] = 1 # 8:48 pm
    expected_msg_by_minute[20*60+49] = 2 # 8:49 pm
    
    summary_data = get_summary_data(input_data, today_date, datefmt, timefmt)
    #print "Checking: ", summary_data['CSV'].strip(), "==", expected_csv
    assert summary_data['CSV'].strip() == expected_csv
    assert summary_data['DATES'] == expected_dates
    assert summary_data['TOTAL_MSGS_BY_DATE'] == expected_tot_msg_by_dt
    #print "Checking: ", summary_data['NAMES'], '==', expected_names
    assert summary_data['NAMES'] == expected_names
    assert summary_data['TODAY_MSGS_BY_NAME'] == expected_today_msg_by_name
    assert summary_data['ALL_TIME_MSGS_BY_NAME'] == expected_all_msg_by_name
    #print "Checking: ", summary_data['TODAY_WORDS'], '==', expected_today_words
    assert summary_data['TODAY_WORDS'].strip() == expected_today_words
    assert summary_data['ALL_TIME_WORDS'].strip() == expected_all_words

    #print "Checking: ", summary_data['MSGS_BY_MINUTE_OF_DAY'], '==', expected_msg_by_minute
    assert summary_data['MSGS_BY_MINUTE_OF_DAY'] == expected_msg_by_minute

def test_file_cmdline_args():
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
        print 'summary: ', summary

if __name__ == '__main__':
    test_summary()

