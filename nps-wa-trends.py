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
<style>
input[disabled]{
  color: #666;     
}
</style>
<script type="text/javascript">

function getOutputOptionDefaults() {
    var ooDefaults = new Object();

    ooDefaults["inp_woc_graf"] = true;
    ooDefaults["inp_woc_graf_grp_msgs_by_date"] = true;
    ooDefaults["inp_woc_graf_day_msgs_by_name"] = true;
    ooDefaults["inp_woc_graf_all_msgs_by_name"] = false;

    ooDefaults["inp_woc_wcloud"] = true;
    ooDefaults["inp_woc_wcloud_all_names"] = false;
    ooDefaults["inp_woc_wcloud_day_names"] = true;
    ooDefaults["inp_woc_wcloud_all_msgs"] = false;
    ooDefaults["inp_woc_wcloud_day_msgs"] = true;

    ooDefaults["inp_woc_csv"] = false;

    return ooDefaults;
}
function getOutputOptions() {
    var ooo = new Object();
    ooo["inp_woc_csv"] = [];
    ooo["inp_woc_graf"] = [
        "inp_woc_graf_grp_msgs_by_date",
        "inp_woc_graf_day_msgs_by_date",
        "inp_woc_graf_all_msgs_by_date"
    ];
    ooo["inp_woc_wcloud"] = [
        "inp_woc_wcloud_all_names",
        "inp_woc_wcloud_day_names",
        "inp_woc_wcloud_all_msgs",
        "inp_woc_wcloud_day_msgs"
    ];
    return ooo;
}

function getGraphOptionInputNames() {
    var a = [
        "inp_woc_graf_grp_msgs_by_date",
        "inp_woc_graf_day_msgs_by_name",
        "inp_woc_graf_all_msgs_by_name"
    ];
    return a;
}
function getWordCloudOptionInputNames() {
    var a = [
        "inp_woc_wcloud_all_names",
        "inp_woc_wcloud_day_names",
        "inp_woc_wcloud_all_msgs",
        "inp_woc_wcloud_day_msgs"
    ];
    return a;
}
function updateOutputSubOptions(enable, elementIds) {
    var callable = enable ? element_enabler : element_disabler;
    
    elementIds.forEach(callable);
}
function getChatTextModeInputElementNames() {
    var a = [
        "inp_dtfmt_ddmmyyyy",
        "inp_dtfmt_mmddyyyy",
        "inp_tmfmt_hh12mmssaa",
        "inp_tmfmt_hh24mmss",
        "inp_tmfmt_hh24mm",
        "inp_dtstr",
        "wa_output_options_button",
    ];
    var woo = getOutputOptionDefaults();
    for(var ooid in woo) {
        a.push(ooid);
    }
    return a;
}
function getChatTextModeDivIds() {
    var a = [
        "wa_chat_text_options",
        "wa_output_options_button"
    ];
    return a;
}
function getWaOutputOptionsContainerId() {
    return "wa_output_options";
}
function getWaOutputOptionsContainerElement() {
    return document.getElementById(getWaOutputOptionsContainerId());
}
function element_disabler(elementId, index, arr) {
    disableIt(document.getElementById(elementId));
}
function element_enabler(elementId, index, arr) {
    enableIt(document.getElementById(elementId));
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

    getChatTextModeInputElementNames().forEach(element_disabler);
    
    getChatTextModeDivIds().forEach(
        function(ele, ind, arr) {
            hideIt(document.getElementById(ele));
        }
    );
    hideOutputOptions();
}
function set_chat_text_mode() {

    getChatTextModeInputElementNames().forEach(element_enabler);

    getChatTextModeDivIds().forEach(
        function(ele, ind, arr) {
            showIt(document.getElementById(ele));
        }
    );
    restoreOutputOptionDefaults();
}
function restoreOutputOptionDefaults() {
    var ooDefaults = getOutputOptionDefaults();
    for(var ooid in ooDefaults) {
        document.getElementById(ooid).checked =
            ooDefaults[ooid];
    }
    var ooo = getOutputOptions();
    for(var ooid in ooo) {
        updateOutputSubOptions(document.getElementById(ooid).checked, ooo[ooid]);
    }
}
function toggleOutputOptions() {
    var woo = getWaOutputOptionsContainerElement();
    var vis = woo.style.visibility;
    if(vis == 'hidden') {
        showOutputOptions();
    } else {
        hideOutputOptions();
    }
}
function showOutputOptions() {
    var oobutton = document.getElementById("wa_output_options_button");
    oobutton.innerHTML = "Restore defaults and hide output options";
    var woo = getWaOutputOptionsContainerElement();
    showIt(woo);
}
function hideOutputOptions() {
    var oobutton = document.getElementById("wa_output_options_button");
    oobutton.innerHTML = "Show output options";
    var woo = getWaOutputOptionsContainerElement();
    hideIt(woo);
    restoreOutputOptionDefaults();
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
<body onload="restoreOutputOptionDefaults()">
<h1>Upload file</h1>
<form action="/" method=post enctype=multipart/form-data>
  What's your file type?<br>
  <input onclick="set_chat_text_mode()" name="filetype" type="radio" value="wa_chat_text" checked="true">Whatsapp exported chat text</input><br>
  <input onclick="set_plain_text_mode()" name="filetype" type="radio" value="plain_text">Plain text for word cloud</input><br><br>
  <div id="wa_chat_text_options">
      <div id="date_format_chooser">
          Select date format used in the file:<br>
          <input id="inp_dtfmt_ddmmyyyy" name="dateformat" type="radio" value="DD/MM/YYYY" checked="true">DD/MM/YYYY</input><br>
          <input id="inp_dtfmt_mmddyyyy" name="dateformat" type="radio" value="MM/DD/YYYY">MM/DD/YYYY</input><br>
      </div>
      <br>
      <div id="end_date_input">
          Summarise upto this date(in the above date format):<br>
          <input id="inp_dtstr" type=text name=datestr value=""></input>
      </div>
      <br>
      <div id="time_format_chooser">
          Select time format used in the file:<br>
          <input id="inp_tmfmt_hh12mmssaa" name="timeformat" type="radio" value="hh:mm:ss aa" checked="true">8:47:15 am</input><br>
          <input id="inp_tmfmt_hh24mmss" name="timeformat" type="radio" value="HH:mm:ss">20:47:15</input><br>
          <input id="inp_tmfmt_hh24mm" name="timeformat" type="radio" value="HH:mm">20:47</input><br>
      </div>
      <br>
      <a id="wa_output_options_button" onclick="toggleOutputOptions(); return false;" href="">Show output options</a><br>
      <div id="wa_output_options" style="visibility: hidden; display: none">
          What do you need in the output?<br>
          <input id="inp_woc_csv" name="wa_output_config" type="checkbox" value="need_csv" checked="false">CSV</input><br>
	  <dl>
            <dt><input id="inp_woc_graf" onclick="updateOutputSubOptions(this.checked, getGraphOptionInputNames())" name="wa_output_config" type="checkbox" value="need_graphs" checked="true">Graphs</input></dt>
	      <dd>
                  <input id="inp_woc_graf_grp_msgs_by_date" name="wa_output_config" type="checkbox" value="need_grp_msgs_by_date_graph" checked="true">Group messages by date graphs</input></dt>
              </dd>
	      <dd>
                  <input id="inp_woc_graf_day_msgs_by_name" name="wa_output_config" type="checkbox" value="need_day_msgs_by_name_graph" checked="true">Messages by name graph for the given date</input></dt>
              </dd>
	      <dd>
                  <input id="inp_woc_graf_all_msgs_by_name" name="wa_output_config" type="checkbox" value="need_all_msgs_by_name_graph" checked="false">Messages by name graph for all dates</input></dt>
              </dd>
	  <dt><input id="inp_woc_wcloud" onclick="updateOutputSubOptions(this.checked, getWordCloudOptionInputNames())" name="wa_output_config" type="checkbox" value="need_word_clouds" checked="true">Word clouds</input></dt>
	      <dd>
	          <input id="inp_woc_wcloud_all_names" name="wa_output_config" type="checkbox" value="need_all_names_cloud" checked="false">Word cloud of names based on entire message history</input>
	      </dd>
	      <dd>
	          <input id="inp_woc_wcloud_day_names" name="wa_output_config" type="checkbox" value="need_day_names_cloud" checked="true">Word cloud of names based on messages on the given date</input>
	      </dd>
	      <dd>
	          <input id="inp_woc_wcloud_all_msgs" name="wa_output_config" type="checkbox" value="need_all_msgs_word_cloud" checked="false">Word cloud of entire message history</input>
	      </dd>
	      <dd>
	          <input id="inp_woc_wcloud_day_msgs" name="wa_output_config" type="checkbox" value="need_day_msgs_word_cloud" checked="true">Word cloud of messages on the given date</input>
	      </dd>

	  </dl>
      </div>
      <br>
  </div>
  <input type=file name=upfile></input><input type=submit value=Upload ></input>
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
    all_time_words = summary['ALL_TIME_WORDS']
    
    #print 'Day msgs: ', len(day_msgs_by_name), day_msgs_by_name
    #print 'Names: ', len(names_arr), names_arr
    if not day_msgs_by_name or len(day_msgs_by_name) != len(names_arr):
        return get_main_page('Input file does not contain any entries for '+datestr+' or input file incomplete/corrupted. Please check and re-upload.')
    
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
            
	    if OUTPUT_NEED_ALL_MSGS_BY_DATE in required_outputs:
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
