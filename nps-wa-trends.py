
import os
from flask import Flask, request, make_response
from npswa import count_by_date_name, split_time_name

ALLOWED_EXTENSIONS = set(['txt', 'text'])

app = Flask(__name__)
app.config.from_pyfile('flask_config.py')

@app.route('/hello')
def hello():
    return 'Hello World!'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
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
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=upfile>
         <input type=submit value=Upload>
    </form>
    '''

def generate_summary_resp(upfile, upfilename):
    headers = {"Content-Disposition": "attachment; filename=%s" % ('summary.csv')}
    csv_content = []
    for line in count_by_date_name(split_time_name(upfile.stream)):
        csv_content.append(line)
    csv_content = '\n'.join(csv_content)
    print type(csv_content), len(csv_content)
    return make_response((csv_content, None, headers))
        
if __name__=='__main__':
    print "ha"
