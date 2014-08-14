import sys
import os
import datetime
import zipfile
import StringIO
from flask import Flask, request, make_response
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

MAIN_PAGE_HEADER = '''
<!doctype html>
<html>
<head>
<script type="text/javascript">

function getChatTextModeInputElementNames() {
    var a = [
        "inp_dtfmt_ddmmyyyy",
        "inp_dtfmt_mmddyyyy",
        "inp_tmfmt_hh12mmssaa",
        "inp_tmfmt_hh24mmss",
        "inp_tmfmt_hh24mm",
        "inp_dtstr",
        "wa_output_options_button",
        "inp_woc_graf",
        "inp_woc_wcloud",
        "inp_woc_csv"
    ];
    return a;
}

function element_disabler(element, index, arr) {
    document.getElementById(element).disabled = true;
}
function element_enabler(element, index, arr) {
    document.getElementById(element).disabled = false;
}

function disableIt(x) {
    x.disabled = true;
}
function enableIt(x) {
    x.disabled = false;
}

function hideIt(x) {
    x.style.visibility = 'hidden';
    x.style.display = 'none';
}
function showIt(x) {
    x.style.visibility = 'visible';
    x.style.display = 'block';
}

function set_plain_text_mode() {

    getChatTextModeInputElementNames().forEach(
        function(element, index, arr) {
            disableIt(document.getElementById(element));
        }
    );
    
    ["wa_chat_text_options", "wa_output_options_button"].forEach(
        function(ele, ind, arr) {
            hideIt(document.getElementById(ele));
        }
    );
    
    hideOutputOptions();
}
function set_chat_text_mode() {

    getChatTextModeInputElementNames().forEach(
        function(element, index, arr) {
            enableIt(document.getElementById(element));
        }
    );

    ["wa_chat_text_options", "wa_output_options_button"].forEach(
        function(ele, ind, arr) {
            showIt(document.getElementById(ele));
        }
    );
}
function showOutputOptions() {
    showIt(document.getElementById("wa_output_options"));
}
function hideOutputOptions() {
    hideIt(document.getElementById("wa_output_options"));
    
    [ "inp_woc_graf", "inp_woc_wcloud", "inp_woc_csv"].forEach(
        function(ele, ind, arr) {
            document.getElementById(ele).checked = true;
        }
    );    
    
}
function toggleOutputOptions() {
    var woo = document.getElementById("wa_output_options");
    var vis = woo.style.visibility;
    if(vis == 'hidden') {
        showOutputOptions();
    } else {
        hideOutputOptions();
    }
}
function remove_error_msg_area(error_number) {
    var err_id = "error_msg_area_" + error_number;
    hideIt(document.getElementById(err_id));
}
</script>
<title>NPS chat summary</title>
</head>
'''

MAIN_PAGE_BODY = '''
<body>
<h1>Upload file</h1>
<form action="/" method=post enctype=multipart/form-data>
  What's your file type?<br>
  <input onclick="set_chat_text_mode()" name="filetype" type="radio" value="wa_chat_text" checked="true">Whatsapp exported chat text<br>
  <input onclick="set_plain_text_mode()" name="filetype" type="radio" value="plain_text">Plain text for word cloud<br><br>
  <div id="wa_chat_text_options">
      <div id="date_format_chooser">
          Select date format used in the file:<br>
          <input id="inp_dtfmt_ddmmyyyy" name="dateformat" type="radio" value="DD/MM/YYYY" checked="true">DD/MM/YYYY<br>
          <input id="inp_dtfmt_mmddyyyy" name="dateformat" type="radio" value="MM/DD/YYYY">MM/DD/YYYY<br>
      </div>
      <br>
      <div id="end_date_input">
          Summarise upto this date(in the above date format):<br>
          <input id="inp_dtstr" type=text name=datestr value="">
      </div>
      <br>
      <div id="time_format_chooser">
          Select time format used in the file:<br>
          <input id="inp_tmfmt_hh12mmssaa" name="timeformat" type="radio" value="hh:mm:ss aa" checked="true">8:47:15 am<br>
          <input id="inp_tmfmt_hh24mmss" name="timeformat" type="radio" value="HH:mm:ss">20:47:15<br>
          <input id="inp_tmfmt_hh24mm" name="timeformat" type="radio" value="HH:mm">20:47<br>
      </div>
      <br>
      <a id="wa_output_options_button" onclick="toggleOutputOptions(); return false;" href="">Toggle output options<br></a>
      <div id="wa_output_options" style="visibility: hidden; display: none">
          What do you need in the output?<br>
          <input id="inp_woc_csv" name="wa_output_config" type="checkbox" value="need_csv" checked="true">CSV<br>
          <input id="inp_woc_graf" name="wa_output_config" type="checkbox" value="need_graphs" checked="true">Graphs<br>
          <input id="inp_woc_wcloud" name="wa_output_config" type="checkbox" value="need_word_clouds" checked="true">Word clouds<br>
      </div>
      <br>
  </div>
  <input type=file name=upfile><input type=submit value=Upload >
</form>
<hr>
{0}
</body>
</html>
'''

ERROR_MSG_DIV = '''
<div id="error_msg_area_{0}">
{1}&nbsp;
<a id="rm_error_msg_area_{0}_button"
   onclick="remove_error_msg_area({0}); return false;" href="">Clear message</a>
</div>
<br>
'''
FILETYPE_PLAIN_TEXT = "plain_text"
FILETYPE_WA_CHAT_TEXT = "wa_chat_text"

OUTPUT_NEED_GRAPHS = "need_csv"
OUTPUT_NEED_GRAPHS = "need_graphs"
OUTPUT_NEED_WORD_CLOUDS = "need_word_clouds"

def get_main_page(*error_msgs):
    error_divs = ''

    for i, err_msg in enumerate(error_msgs):
        if err_msg:
            error_divs += ERROR_MSG_DIV.format(i, err_msg)

    return MAIN_PAGE_HEADER + MAIN_PAGE_BODY.format(error_divs)

@app.route('/', methods=['GET', 'POST'])
def new_summary():
    if request.method == 'POST':
        upfile = request.files['upfile']
        filetype = request.form['filetype']
        print filetype
        datestr = request.form.get('datestr')
        print datestr
        datefmt_str = request.form.get('dateformat')
        print datefmt_str
        timefmt_str = request.form.get('timeformat')
        print timefmt_str
        required_outputs = request.form.getlist("wa_output_config")
        print required_outputs
        return process_req(upfile, filetype, datestr, datefmt_str, timefmt_str, required_outputs)
    return get_main_page('')

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
            ex_info = 'Date entered is invalid or not in correct fromat'
        if ex_info:
            isError = True
            error_msgs.append(ex_info)
            
        if not required_outputs:
            isError = True
            error_msgs.append('No output options selected. Nothing to do.')

        if not isError:
            return gen_summary_charts(upfilestream, upfilename, datestr, datefmt_str, timefmt_str, required_outputs)

    if isError:
        return get_main_page(*error_msgs)

    return get_main_page('Ooops! You uncovered a bug. Contact the developer.')

def generate_summary_resp(upfilestream, upfilename):
    headers = {"Content-Disposition": "attachment; filename=%s" % ('summary.csv')}
    csv_content = []
    for line in count_by_date_name(split_time_name(upfilestream)):
        csv_content.append(line)
    csv_content = '\n'.join(csv_content)
    #print type(csv_content), len(csv_content)
    return make_response((csv_content, None, headers))

def gen_summary_charts(upfilestream, upfilename, datestr, datefmt_str, timefmt_str, required_outputs):
    datestrhyphen = datestr.replace('/', '-')
    filesuffix = '_'.join(( (x[len('need_'):] if 'need_' in x else x) for x in required_outputs ))
    headers = {"Content-Disposition": "attachment; filename=%s" % ('summary_{0}_{1}.zip'.format(filesuffix, datestrhyphen))}
    full_text = upfilestream.read() #.lower()
    
    
    summary = get_summary_data(full_text, datestr, datefmt_str, timefmt_str)
    csv_content = summary['CSV']
    dates_arr = summary['DATES']
    msg_totals = summary['TOTAL_MSGS_BY_DATE']
    names_arr = summary['NAMES']
    day_msgs_by_name = summary['TODAY_MSGS_BY_NAME']
    all_time_msgs_by_name = summary['ALL_TIME_MSGS_BY_NAME']
    today_words = summary['TODAY_WORDS']
    #all_time_words = summary['ALL_TIME_WORDS']
    
    print 'Day msgs: ', len(day_msgs_by_name), day_msgs_by_name
    print 'Names: ', len(names_arr), names_arr
    if not day_msgs_by_name or len(day_msgs_by_name) != len(names_arr):
        return get_main_page('Input file does not contain any entries for '+datestr+' or input file incomplete/corrupted. Please check and re-upload.')
    
    mf = StringIO.StringIO()
    with zipfile.ZipFile(mf, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:

        zf.writestr('summary_{0}.csv'.format(datestrhyphen), csv_content)

        if OUTPUT_NEED_GRAPHS in required_outputs:
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
        
        if OUTPUT_NEED_WORD_CLOUDS in required_outputs:
            today_names = construct_text(names_arr, day_msgs_by_name)
            zf.writestr('today_name_cloud_{0}.png'.format(datestrhyphen), get_cloud_image_bytes(today_names))
            
            #all_time_names = construct_text(names_arr, all_time_msgs_by_name)
            #zf.writestr('all_time_name_cloud_{0}.png'.format(datestrhyphen), get_cloud_image_bytes(all_time_names))

            zf.writestr('today_word_cloud_{0}.png'.format(datestrhyphen), get_cloud_image_bytes(today_words, font_file_name='Symbola.ttf'))
            #zf.writestr('all_time_word_cloud_{0}.png'.format(datestrhyphen), get_cloud_image_bytes(all_time_words, font_file_name='Symbola.ttf'))

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
