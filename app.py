import os
import secrets
import uuid
from pathlib import Path
from flask import Flask, render_template, request, flash, send_from_directory, json
from werkzeug.utils import secure_filename, redirect
from tempfile import TemporaryDirectory
import time

UPLOAD_FOLDER = TemporaryDirectory()

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
def index():  # put application's code here
    return redirect('upload')


ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'xml']


def valid_filename(filename):
    return os.path.splitext(filename)[1].lower().lstrip('.') in ALLOWED_EXTENSIONS


@app.route('/process', methods=['GET'])
def process_page():
    upload_path = Path(app.config['UPLOAD_FOLDER'].name)
    uploaded_files = list(os.listdir(upload_path))
    return render_template('process.html', uploaded_files=uploaded_files)


@app.route('/process/<file>', methods=['GET'])
def process_file(file):
    upload_path = Path(app.config['UPLOAD_FOLDER'].name)
    if not upload_path.exists():
        return app.response_class(
            response=json.dumps({'msg': 'upload folder does not exist'}),
            status=400,
            mimetype='application/json'
        )

    if not Path(upload_path, file).exists():
        return app.response_class(
            response=json.dumps({'msg': 'file does not exist'}),
            status=400,
            mimetype='application/json'
        )

    # magic
    time.sleep(5)

    return app.response_class(
        response=json.dumps({'msg': 'success'}),
        status=200,
        mimetype='application/json'
    )


@app.route('/upload', methods=['POST', 'GET'])
def upload():
    upload_path = Path(app.config['UPLOAD_FOLDER'].name)
    if not upload_path.exists():
        upload_path.mkdir(parents=True, exist_ok=True)

    if request.method == 'GET':
        uploaded_files = list(os.listdir(upload_path))
        return render_template('qrt_menu.html', uploaded_files=uploaded_files)
    elif request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file is not None and valid_filename(file.filename):
            filename = secure_filename(os.path.join(str(uuid.uuid1()), os.path.splitext(file.filename)[1]))
            full_upload_path = Path(upload_path, filename)
            file.save(full_upload_path)
            return redirect(request.url)
        else:
            flash('No valid file selected')
            return redirect(request.url)


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
