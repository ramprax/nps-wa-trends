import sys
import os
import datetime
import zipfile
import StringIO
from flask import Flask, request, make_response
from npswa import count_by_date_name, split_time_name
import plottry

ALLOWED_EXTENSIONS = set(['txt', 'text'])

app = Flask(__name__)
app.config.from_pyfile('flask_config.py')

@app.route('/hello')
def hello():
    return 'Hello World!'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/old', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        upfile = request.files['upfile']
        upfilename = upfile.filename
        if upfile and allowed_file(upfile.filename):
            return generate_summary_resp(upfile, upfilename)
    return '''
    <!doctype html>
    <title>NPS chat summary</title>
    <h1>Upload chat txt file</h1>
    <form action="/old" method=post enctype=multipart/form-data>
      <p><input type=file name=upfile>
         <input type=submit value=Upload>
    </form>
    <hr>
    '''

DEFAULT_RESPONSE = '''
<!doctype html>
<title>NPS chat summary</title>
<h1>Upload chat txt file</h1>
<form action="/" method=post enctype=multipart/form-data>
  Summarise upto this date(dd/mm/yyyy): <input type=text name=datestr value="DD/MM/YYYY">
  <br><input type=file name=upfile><input type=submit value=Upload >
</form>
<hr>
{0}
'''

@app.route('/', methods=['GET', 'POST'])
def new_summary():
    if request.method == 'POST':
        upfile = request.files['upfile']
        datestr = request.form['datestr']
        return process_req(upfile, datestr)
    return DEFAULT_RESPONSE.format(' ')


def process_req(upfile, datestr):
    ex_info = None
    try:
        dtdt = datetime.datetime.strptime(datestr, '%d/%m/%Y')
    except:
        ex_info = 'Date entered is invalid or not in DD/MM/YYYY fromat'

    if ex_info:
        return DEFAULT_RESPONSE.format(ex_info)    
    upfilename = upfile.filename
    if not upfile:
        return DEFAULT_RESPONSE.format('No file given for processing')
    if not allowed_file(upfile.filename):
        return DEFAULT_RESPONSE.format('Unknown file type. Can process .txt or .text files only.')
    
    return gen_summary_charts(upfile, upfilename, datestr)

def generate_summary_resp(upfile, upfilename):
    headers = {"Content-Disposition": "attachment; filename=%s" % ('summary.csv')}
    csv_content = []
    for line in count_by_date_name(split_time_name(upfile.stream)):
        csv_content.append(line)
    csv_content = '\n'.join(csv_content)
    print type(csv_content), len(csv_content)
    return make_response((csv_content, None, headers))

def gen_summary_charts(upfile, upfilename, datestr):
    datestrhyphen = datestr.replace('/', '-')
    headers = {"Content-Disposition": "attachment; filename=%s" % ('summary_charts_{0}.zip'.format(datestrhyphen))}
    csv_content, dates_arr, msg_totals, names_arr, day_msgs_by_name = get_summary_data(upfile.stream, datestr)
    
    today_plot = StringIO.StringIO()
    plottry.bar_plot_names_messages(names_arr, day_msgs_by_name, 'Message count', 'Messages by person on '+datestr, today_plot, 'png')
    today_plot.seek(0)
    
    grp_trend = StringIO.StringIO()
    plottry.line_plot_dates_messages(dates_arr, msg_totals, 'Message count', 'Messages by date till '+datestr, grp_trend, 'png')
    grp_trend.seek(0)

    mf = StringIO.StringIO()
    with zipfile.ZipFile(mf, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('summary_{0}.csv'.format(datestrhyphen), csv_content)
        zf.writestr('day_msgs_per_person_{0}.png'.format(datestrhyphen), today_plot.getvalue())
        zf.writestr('group_trend_{0}.png'.format(datestrhyphen), grp_trend.getvalue())

    mf.seek(0)
    resp = make_response((mf.getvalue(), None, headers))
    today_plot.close()
    grp_trend.close()
    mf.close()

    return resp


def get_summary_data(instream, datestr):
    print '#### datestr = ', datestr
    done = False
    csv_content_arr = []
    datestr_arr = []
    date_msg_totals = []
    for line in count_by_date_name(split_time_name(instream)):
        print '#### line = ', line
        if not line:
            continue
        csv_content_arr.append(line)
        if line.startswith('Date'):
            names_line = line
            continue
        if line.startswith(datestr):
            today_msgs_by_name = line
            done = True
        line_cols = line.split(',')
        # Extract & append date
        datestr_arr.append(line_cols[0]) # append date
        # Get sum for each date
        date_msg_totals.append(sum([ int(x) for x in line_cols[1:] ]))
        
        if done:
            break
    csv_content = '\n'.join(csv_content_arr)
    print type(csv_content), len(csv_content)
    print datestr_arr
    print date_msg_totals
    today_msgs_by_name = [ int(x) for x in today_msgs_by_name.split(',')[1:] ]
    names_line = names_line.split(',')[1:]
    return csv_content, datestr_arr, date_msg_totals, names_line, today_msgs_by_name
    

if __name__=='__main__':
    print "ha"
