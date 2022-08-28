import os
import secrets
from pathlib import Path
from flask import Flask, render_template, request, json
from werkzeug.utils import secure_filename, redirect
from tempfile import TemporaryDirectory
import time
import random
from string import hexdigits

app = Flask(__name__)
app.debug = True
app.config['upload_dir'] = TemporaryDirectory()
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = secrets.token_hex(16)

ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'xml']
FILE_DICT = None


def randstr(n, alphabet=hexdigits):
    return "".join([random.choice(alphabet) for _ in range(n)])


def valid_filename(filename):
    return os.path.splitext(filename)[1].lower().lstrip('.') in ALLOWED_EXTENSIONS


def upload_dir():
    p = Path(app.config['upload_dir'].name)
    if not p.exists():
        p.mkdir(parents=True, exist_ok=True)

    return p


def file_dict():
    global FILE_DICT
    # review simple file dict - might be cleared when app is reinitialized

    if FILE_DICT is None:
        FILE_DICT = {}

    return FILE_DICT


@app.route('/')
def index():
    return redirect('upload')


@app.route('/upload', methods=['GET'])
def upload():
    uploaded_files = list(file_dict().values())
    return render_template('upload.html', uploaded_files=uploaded_files)


@app.route('/api/process/<file_id>', methods=['GET'])
def process_file(file_id):
    if file_id not in file_dict():
        return app.response_class(
            response=json.dumps({'msg': 'file id not registered'}),
            status=400,
            mimetype='application/json'
        )
    else:
        file_meta = file_dict()[file_id]

    filename = file_meta['internal_filename']

    if not Path(upload_dir(), filename).exists():
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


@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return app.response_class(
            response=json.dumps({'msg': 'no file selected'}),
            status=400,
            mimetype='application/json'
        )

    file = request.files['file']
    if file is None or not valid_filename(file.filename):
        return app.response_class(
            response=json.dumps({'msg': 'invalid file'}),
            status=400,
            mimetype='application/json'
        )

    file_id = randstr(20)
    internal_filename = secure_filename(os.path.join(file_id, os.path.splitext(file.filename)[1]))
    file.save(Path(upload_dir(), internal_filename))
    file_dict()[file_id] = {'file_id': file_id, 'filename': file.filename, 'internal_filename': internal_filename}

    return app.response_class(
        response=json.dumps(file_dict()[file_id]),
        status=200,
        mimetype='application/json'
    )


def main():
    try:
        app.run()
    finally:
        if 'upload_dir' in app.config:
            app.config['upload_dir'].cleanup()


if __name__ == '__main__':
    main()
