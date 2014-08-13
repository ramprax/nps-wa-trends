import sys
import os
import datetime
import zipfile
import StringIO
from flask import Flask, request, make_response
from npswa import get_summary_data
from wc_gen import make_word_cloud_image
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
    #print type(csv_content), len(csv_content)
    return make_response((csv_content, None, headers))

def gen_summary_charts(upfile, upfilename, datestr):
    datestrhyphen = datestr.replace('/', '-')
    headers = {"Content-Disposition": "attachment; filename=%s" % ('summary_charts_{0}.zip'.format(datestrhyphen))}
    full_text = upfile.stream.read() #.lower()
    
    
    summary = get_summary_data(full_text, datestr)
    csv_content = summary['CSV']
    dates_arr = summary['DATES']
    msg_totals = summary['TOTAL_MSGS_BY_DATE']
    names_arr = summary['NAMES']
    day_msgs_by_name = summary['TODAY_MSGS_BY_NAME']
    all_time_msgs_by_name = summary['ALL_TIME_MSGS_BY_NAME']
    today_words = summary['TODAY_WORDS']
    all_time_words = summary['ALL_TIME_WORDS']
    
    if not day_msgs_by_name or len(day_msgs_by_name) != len(names_arr):
        return DEFAULT_RESPONSE.format('Input file does not contain any entries for '+datestr+' or input file incomplete/corrupted. Please check and re-upload.')
    
        
    
    mf = StringIO.StringIO()
    with zipfile.ZipFile(mf, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:

        zf.writestr('summary_{0}.csv'.format(datestrhyphen), csv_content)

        today_plot = StringIO.StringIO()
        plottry.bar_plot_names_messages(names_arr, day_msgs_by_name, 'Message count', 'Messages by person on '+datestr, today_plot, 'png')
        today_plot.seek(0)
        zf.writestr('day_msgs_per_person_{0}.png'.format(datestrhyphen), today_plot.getvalue())
        today_plot.close()
        
        grp_trend = StringIO.StringIO()
        plottry.line_plot_dates_messages(dates_arr, msg_totals, 'Message count', 'Messages by date till '+datestr, grp_trend, 'png')
        grp_trend.seek(0)
        zf.writestr('group_trend_{0}.png'.format(datestrhyphen), grp_trend.getvalue())
        grp_trend.close()
        
        today_names = construct_text(names_arr, day_msgs_by_name)
        zf.writestr('today_name_cloud_{0}.png'.format(datestrhyphen), get_cloud_image_bytes(today_names))
        
        all_time_names = construct_text(names_arr, all_time_msgs_by_name)
        zf.writestr('all_time_name_cloud_{0}.png'.format(datestrhyphen), get_cloud_image_bytes(all_time_names))

        zf.writestr('today_word_cloud_{0}.png'.format(datestrhyphen), get_cloud_image_bytes(today_words, font_file_name='Symbola.ttf'))
        zf.writestr('all_time_word_cloud_{0}.png'.format(datestrhyphen), get_cloud_image_bytes(all_time_words, font_file_name='Symbola.ttf'))

    mf.seek(0)
    resp = make_response((mf.getvalue(), None, headers))
    mf.close()

    return resp

def get_cloud_image_bytes(text, font_file_name='Ubuntu-R.ttf'):
    cloud_image = StringIO.StringIO()
    make_word_cloud_image(text, cloud_image, font_file_name=font_file_name)
    cloud_image.seek(0)
    cloud_image_bytes = cloud_image.getvalue()
    cloud_image.close()
    return cloud_image_bytes
    

def construct_text(word_arr, freq_arr):
    word_text = ' '
    for i in xrange(len(word_arr)):
        freq = freq_arr[i]
        word = word_arr[i]
        word_text = ' '.join((word_text, ' '.join([word] * freq)))
    return word_text

    

if __name__=='__main__':
    print "ha"
