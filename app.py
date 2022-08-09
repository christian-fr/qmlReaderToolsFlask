import os
import secrets
import uuid
from pathlib import Path
from flask import Flask, render_template, jsonify, request, url_for, flash, session, send_from_directory, send_file
from werkzeug.utils import secure_filename, redirect
from tempfile import TemporaryDirectory

UPLOAD_FOLDER = TemporaryDirectory()

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def prepare_data():
    return {'data': 'this and that'}


@app.route('/')
def hello_world():  # put application's code here
    return redirect('upload')


@app.route('/api/', methods=['GET'])
def mydata_api():
    data = prepare_data()
    return jsonify(data)


ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'xml']


def allowed_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api', methods=['POST', 'GET'])
def api():
    if request.method == 'GET':
        return 'GET that shit'
    elif request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(str(uuid.uuid1())) + os.path.splitext(file.filename)[1]
            upload_path = Path(app.config['UPLOAD_FOLDER'].name)
            full_upload_path = Path(upload_path, filename)
            if not upload_path.exists():
                upload_path.mkdir(parents=True, exist_ok=True)
            file.save(full_upload_path)
            return send_file(str(full_upload_path), attachment_filename=f'output{os.path.splitext(file.filename)[1]}')
            # return redirect(url_for('download_file', name=filename))
        else:
            return "Some error occured."


@app.route('/qrt_menu', methods=['POST', 'GET'])
def qrt_menu():
    if request.method == 'GET':
        return render_template('qrt_menu.html')
    elif request.method == 'POST':
        return render_template('qrt_details.html')



@app.route('/qrt_details', methods=['POST', 'GET'])
def qrt_details():
    if request.method == 'GET':
        return "GET"
    elif request.method == 'POST':
        return "POST"





@app.route('/upload', methods=['POST', 'GET'])
def upload():
    if request.method == 'GET':
        return render_template('qrt_menu.html')
    elif request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(str(uuid.uuid1())) + os.path.splitext(file.filename)[1]
            upload_path = Path(app.config['UPLOAD_FOLDER'].name)
            full_upload_path = Path(upload_path, filename)
            if not upload_path.exists():
                upload_path.mkdir(parents=True, exist_ok=True)
            file.save(full_upload_path)
            return send_file(str(full_upload_path), download_name=f'output{os.path.splitext(file.filename)[1]}')
            # return redirect(url_for('download_file', name=filename))


@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)


def clear_uploads():
    print(UPLOAD_FOLDER)
    Path(UPLOAD_FOLDER.name).rmdir()


if __name__ == '__main__':
    app.config['SESSION_TYPE'] = 'filesystem'
    app.debug = True
    clear_uploads()
    app.run()
