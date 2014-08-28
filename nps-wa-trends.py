import sys
import os
import datetime
import zipfile
import StringIO
from flask import Flask, request, make_response, render_template
from npswa import get_summary_data, DATEFMT_MAP
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

FILETYPE_PLAIN_TEXT = "plain_text"
FILETYPE_WA_CHAT_TEXT = "wa_chat_text"

OUTPUT_NEED_CSV = "need_csv"

OUTPUT_NEED_GRAPHS = "need_graphs"
OUTPUT_NEED_GRP_MSGS_BY_DATE_GRAPH = "need_grp_msgs_by_date_graph"
OUTPUT_NEED_ALL_MSGS_BY_NAME_GRAPH = "need_all_msgs_by_name_graph"
OUTPUT_NEED_DAY_MSGS_BY_NAME_GRAPH = "need_day_msgs_by_name_graph"

OUTPUT_NEED_WORD_CLOUDS = "need_word_clouds"
OUTPUT_NEED_ALL_MSGS_CLOUD = "need_all_msgs_word_cloud"
OUTPUT_NEED_DAY_MSGS_CLOUD = "need_day_msgs_word_cloud"
OUTPUT_NEED_ALL_NAMES_CLOUD = "need_all_names_cloud"
OUTPUT_NEED_DAY_NAMES_CLOUD = "need_day_names_cloud"

@app.route('/', methods=['GET', 'POST'])
def new_summary():
    if request.method == 'POST':
        upfile = request.files['upfile']
        filetype = request.form['filetype']
        #print filetype
        datestr = request.form.get('datestr')
        #print datestr
        datefmt_str = request.form.get('dateformat')
        #print datefmt_str
        timefmt_str = request.form.get('timeformat')
        #print timefmt_str
        required_outputs = request.form.getlist("wa_output_config")
        #print required_outputs
        return process_req(upfile, filetype, datestr, datefmt_str, timefmt_str, required_outputs)
    #error_msgs = []
    return render_template('index.html', error_msgs=[]) #get_main_page('')

def process_req(upfile, filetype, datestr, datefmt_str, timefmt_str, required_outputs):
    error_msgs = []
    isError = False

    if not upfile:
        isError = True
        error_msgs.append('No file given for processing')
    elif not allowed_file(upfile.filename):
        isError = True
        error_msgs.append('Unknown uploaded file extension. Can process .txt or .text files only.')
    else:
        upfilename = upfile.filename
        upfilestream = upfile.stream

    if not filetype in (FILETYPE_PLAIN_TEXT, FILETYPE_WA_CHAT_TEXT):
        isError = True
        error_msgs.append('Unknown filetype')
    
    if filetype == FILETYPE_PLAIN_TEXT and not isError:
        return gen_word_cloud_resp(upfilestream, upfilename)
    elif filetype == FILETYPE_WA_CHAT_TEXT:
        ex_info = None
        try:
            dtdt = datetime.datetime.strptime(datestr, DATEFMT_MAP[datefmt_str])
        except:
            ex_info = 'Date entered is invalid or in wrong format'
        if ex_info:
            isError = True
            error_msgs.append(ex_info)
            
        if not required_outputs:
            isError = True
            error_msgs.append('No output options selected. Nothing to do.')

        if not isError:
            return gen_summary_charts(upfilestream, upfilename, datestr, datefmt_str, timefmt_str, required_outputs)

    if isError:
        return render_template('index.html', error_msgs=error_msgs) #get_main_page(*error_msgs)

    return render_template('index.html', error_msgs=['Ooops! You uncovered a bug. Contact the developer.']) #get_main_page('Ooops! You uncovered a bug. Contact the developer.')


def gen_summary_charts(upfilestream, upfilename, datestr, datefmt_str, timefmt_str, required_outputs):
    datestrhyphen = datestr.replace('/', '-')
    #filesuffix = '_'.join(( (x[len('need_'):] if 'need_' in x else x) for x in required_outputs ))
    headers = {"Content-Disposition": "attachment; filename=%s" % ('summary_{0}.zip'.format(datestrhyphen))}
    full_text = upfilestream.read() #.lower()
    
    
    summary = get_summary_data(full_text, datestr, datefmt_str, timefmt_str)
    csv_content = summary['CSV']
    dates_arr = summary['DATES']
    msg_totals = summary['TOTAL_MSGS_BY_DATE']
    names_arr = summary['NAMES']
    day_msgs_by_name = summary['TODAY_MSGS_BY_NAME']
    all_time_msgs_by_name = summary['ALL_TIME_MSGS_BY_NAME']
    today_words = summary['TODAY_WORDS']
    all_time_words = summary['ALL_TIME_WORDS']
    
    #print 'Day msgs: ', len(day_msgs_by_name), day_msgs_by_name
    #print 'Names: ', len(names_arr), names_arr
    if not day_msgs_by_name or len(day_msgs_by_name) != len(names_arr):
        return render_template('index.html', error_msg=['Input file does not contain any entries for '+datestr+' or input file incomplete/corrupted. Please check and re-upload.'])
    
    mf = StringIO.StringIO()
    with zipfile.ZipFile(mf, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:

        if OUTPUT_NEED_CSV in required_outputs:
            zf.writestr('summary_{0}.csv'.format(datestrhyphen), csv_content)

        if OUTPUT_NEED_GRAPHS in required_outputs:
            if OUTPUT_NEED_DAY_MSGS_BY_NAME_GRAPH in required_outputs:
                today_plot = StringIO.StringIO()
                plottry.bar_plot_names_messages(
                    names_arr,
                    day_msgs_by_name,
		    'Message count for the day',
		    'Messages by person on '+datestr,
		    today_plot,
		    'png'
		)
                today_plot.seek(0)
                zf.writestr(
		    'day_msgs_per_person_{0}.png'.format(datestrhyphen),
		    today_plot.getvalue()
		)
                today_plot.close()

            if OUTPUT_NEED_ALL_MSGS_BY_NAME_GRAPH in required_outputs:
                alltime_plot = StringIO.StringIO()
                plottry.bar_plot_names_messages(
                    names_arr,
                    all_time_msgs_by_name,
		    'Message count for all time',
		    'Messages by person till '+datestr,
		    alltime_plot,
		    'png'
		)
                alltime_plot.seek(0)
                zf.writestr(
		    'all_time_msgs_per_person_{0}.png'.format(datestrhyphen),
		    alltime_plot.getvalue()
		)
                alltime_plot.close()
            
	    if OUTPUT_NEED_GRP_MSGS_BY_DATE_GRAPH in required_outputs:
                grp_trend = StringIO.StringIO()
                plottry.line_plot_dates_messages(
		    dates_arr,
		    msg_totals,
		    'Message count',
		    'Messages by date till '+datestr,
		    grp_trend,
		    'png'
		)
                grp_trend.seek(0)
                zf.writestr(
		    'group_trend_{0}.png'.format(datestrhyphen), 
		    grp_trend.getvalue()
		)
                grp_trend.close()
        
        if OUTPUT_NEED_WORD_CLOUDS in required_outputs:
            if OUTPUT_NEED_DAY_NAMES_CLOUD in required_outputs:
                today_names = construct_text(names_arr, day_msgs_by_name)
                zf.writestr(
		    'today_name_cloud_{0}.png'.format(datestrhyphen),
                    get_cloud_image_bytes(today_names)
		)
            
            if OUTPUT_NEED_ALL_NAMES_CLOUD in required_outputs:
                all_time_names = construct_text(names_arr, all_time_msgs_by_name)
                zf.writestr(
		    'all_time_name_cloud_{0}.png'.format(datestrhyphen),
                    get_cloud_image_bytes(all_time_names)
		)

            if OUTPUT_NEED_DAY_MSGS_CLOUD in required_outputs:
                zf.writestr(
		    'today_word_cloud_{0}.png'.format(datestrhyphen),
                    get_cloud_image_bytes(
		        today_words, 
			font_file_name='Symbola.ttf'
		    )
		)

            if OUTPUT_NEED_ALL_MSGS_CLOUD in required_outputs:
                zf.writestr(
		    'all_time_word_cloud_{0}.png'.format(datestrhyphen),
                    get_cloud_image_bytes(
		        all_time_words, 
			font_file_name='Symbola.ttf'
		    )
		)

    mf.seek(0)
    resp = make_response((mf.getvalue(), None, headers))
    mf.close()

    return resp
    
def gen_word_cloud_resp(upfilestream, upfilename):
    full_text = upfilestream.read().lower()
    resp_bytes = get_cloud_image_bytes(full_text, font_file_name='Symbola.ttf')
    headers = {"Content-Disposition": "attachment; filename=%s" % ('{0}.png'.format(upfilename.replace(' ', '_')))}
    resp = make_response((resp_bytes, None, headers))
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


