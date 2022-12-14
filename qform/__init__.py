import os
import re
import secrets
from collections import OrderedDict, defaultdict
from functools import wraps
from pathlib import Path
from typing import Any, Dict, Optional, List, Union, Tuple
from qrt.util.util import qml_details, make_flowchart
from flask import Flask, render_template, request, json, send_file, session, flash, Request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename, redirect
from tempfile import TemporaryDirectory
import time
import random
from string import hexdigits
from qrt.util.qml import read_xml, Questionnaire, VarRef
from xml.etree.ElementTree import ParseError

app = Flask(__name__)
app.debug = True
app.config['upload_dir'] = TemporaryDirectory()
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = secrets.token_hex(16)


def check_credentials(cred: Union[str, None]):
    if cred is not None:
        cred = cred.strip()
        if len(cred) == 0:
            cred = None
    return cred


flask_user = check_credentials(os.environ.get('FLASK_USER'))
flask_pass = check_credentials(os.environ.get('FLASK_PASS'))

limiter = Limiter(app=app, key_func=get_remote_address)

ALLOWED_EXTENSIONS = ['xml']
FILE_DICT = None
GEN_DICT = None


def login_restricted(func):
    @wraps(func)
    def func_wrapper(*args, **kwargs):
        if flask_user is None or flask_pass is None:
            session['logged_in'] = True
        if not session.get('logged_in'):
            return render_template('login.html')
        else:
            return func(*args, **kwargs)

    return func_wrapper


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


@app.errorhandler(404)
def page_not_found(e):
    return index()


@app.errorhandler(429)
def too_many_requests(e):
    flash(f'too many login attempts (>{e.description})')
    return index()


def gen_dict():
    global GEN_DICT
    # review simple gen data dict - might be cleared when app is reinitialized

    if GEN_DICT is None:
        GEN_DICT = {}

    if 'session_id' not in GEN_DICT:
        GEN_DICT['session_id'] = {}

    return GEN_DICT['session_id']


@app.before_request
def init_session():
    if 'session_id' not in session:
        session['session_id'] = randstr(20)


@app.route('/')
@login_restricted
def index():
    # if not session.get('logged_in'):
    #     return render_template('login.html')
    return redirect('upload')


@app.route('/login', methods=['POST'])
@limiter.limit("100/day")
@limiter.limit("10/minute")
def do_login():
    if flask_user is None or flask_pass is None:
        session['logged_in'] = True
        # flash('no users have been set, login is not possible')
        return index()
    if request.form['username'] == flask_user and request.form['password'] == flask_pass:
        session['logged_in'] = True
    else:
        flash('wrong password!')
    return index()


@app.route('/login', methods=['GET'])
def get_login():
    return index()


def get_flashed_messages():
    return session.get('_flashes')


@app.route('/upload', methods=['GET'])
@login_restricted
def upload():
    uploaded_files = [{k: v for k, v in f.items() if k not in ['questionnaire']} for f in file_dict().values()]
    # uploaded_files = list(file_dict().values())
    return render_template('upload.html', uploaded_files=uploaded_files, flowcharts=uploaded_files)


@app.route('/gen_mqsc', methods=['GET'])
def form_mqsc():
    gen_data = gen_dict()
    if gen_data == {}:
        gen_data = {'type': 'mqsc',
                    'q_uid': 'mqsc',
                    'q_visible': '',
                    'headers': {
                        1: {'uid': 'q',
                            'type': 'question',
                            'visible': '',
                            'text': ''}
                    },
                    'aos': {
                        1: {'uid': 'ao1',
                            'value': '',
                            'label': '',
                            'visible': ''}
                    },
                    'items': {
                        1: {'uid': 'it1',
                            'variable': '',
                            'text': '',
                            'visible': ''}
                    }
                    }
    return render_template('gen_mqsc.html', gen_data=gen_data)


def nested_dict(input_dict: Dict[str, str], prefix: str) -> Dict[int, Dict[str, str]]:
    result = defaultdict(dict)
    for k, v in input_dict.items():
        if not k.startswith(prefix):
            continue
        result[int(k.split('_')[0].strip(prefix))][k.split('_')[1]] = v
    return result


def get_action_obj(input_request: Request) -> Optional[Tuple[str, int, str]]:
    for action in ['down', 'up', 'remove']:
        if action in request.form:
            target = request.form[action]
            obj_type = None
            if target.startswith('header'):
                obj_type = 'header'
            elif target.startswith('ao'):
                obj_type = 'ao'
            elif target.startswith('item'):
                obj_type = 'item'

            obj_index = int(target.replace(obj_type, ''))
            return action, obj_index, obj_type
    return None


@app.route('/gen_mqsc', methods=['POST'])
def form_mqsc_post():
    data = {'type': request.form['type'],
            'q_uid': request.form['question_uid'],
            'q_visible': request.form['question_visible'],
            'headers': nested_dict(request.form, 'header'),
            'aos': nested_dict(request.form, 'ao'),
            'items': nested_dict(request.form, 'item')
            }
    if 'submit' in request.form:
        action = request.form['submit']
        if action == 'clear':
            data.clear()
        elif action == 'add_header':
            tmp_dict = {max(data['headers'].keys()) + 1: {'uid': f'q{max(data["headers"].keys()) + 1}',
                                                          'visible': '',
                                                          'type': 'question',
                                                          'value': '',
                                                          'text': ''}}
            data['headers'].update(tmp_dict)

        elif action == 'add_item':
            pass
        elif action == 'add_ao':
            pass
        elif action == 'gen_xml':
            pass

    action_data = get_action_obj(request)
    if action_data is not None:
        obj_action, obj_index, obj_type = action_data
        if obj_action == 'remove':
            if obj_index in data[obj_type + 's']:
                data[obj_type + 's'].pop(obj_index)
        if obj_index in data[obj_type + 's']:
            if obj_action == 'up':
                tmp_dict = {obj_index - 1: data[obj_type + 's'][obj_index],
                            obj_index: data[obj_type + 's'][obj_index - 1]}
                data[obj_type + 's'].pop(obj_index - 1)
                data[obj_type + 's'].pop(obj_index)
                data[obj_type + 's'].update(tmp_dict)

            elif obj_action == 'down':
                tmp_dict = {obj_index + 1: data[obj_type + 's'][obj_index],
                            obj_index: data[obj_type + 's'][obj_index + 1]}
                data[obj_type + 's'].pop(obj_index + 1)
                data[obj_type + 's'].pop(obj_index)
                data[obj_type + 's'].update(tmp_dict)
        new_dict = {}
        for k in sorted(data[obj_type + 's']):
            new_index = len(new_dict) + 1
            new_dict[new_index] = data[obj_type + 's'][k]
            new_dict[new_index]['uid'] = re.sub(r'[0-9]+', '', data[obj_type + 's'][k]['uid']) + str(new_index)
        data[obj_type + 's'] = new_dict
    gen_dict().clear()
    gen_dict().update(data)
    return render_template('gen_mqsc.html', gen_data=gen_dict())


@app.route('/api/gen_mqsc', methods=['POST'])
def generate_mqsc():
    pass


def process_xml(file_id) -> None:
    file_meta = file_dict()[file_id]
    filename = file_meta['internal_filename']
    q = read_xml(Path(upload_dir(), filename))
    file_dict()[file_id]['questionnaire'] = q


def process_graphs(file_id):
    file_meta = file_dict()[file_id]
    flowchart_file1 = Path(upload_dir(), file_id + '_flowchart_var_cond.png')
    flowchart_file2 = Path(upload_dir(), file_id + '_flowchart_var.png')
    flowchart_file3 = Path(upload_dir(), file_id + '_flowchart.png')

    make_flowchart(q=file_meta['questionnaire'], out_file=flowchart_file1, show_var=True, show_cond=True)
    make_flowchart(q=file_meta['questionnaire'], out_file=flowchart_file2, show_var=True, show_cond=False)
    make_flowchart(q=file_meta['questionnaire'], out_file=flowchart_file3, show_var=False, show_cond=False,
                   color_nodes=True)

    file_meta['flowchart'] = [str(flowchart_file1), str(flowchart_file2), str(flowchart_file3)]


@app.route('/api/process/<file_id>', methods=['GET'])
@login_restricted
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
    try:
        process_xml(file_id)

    except ParseError as err:
        return app.response_class(
            response=json.dumps({'msg': f'error while parsing file: {err.msg}'}),
            status=400,
            mimetype='application/json'
        )

    process_graphs(file_id)

    return app.response_class(
        response=json.dumps({'msg': 'success'}),
        status=200,
        mimetype='application/json'
    )


@app.route('/api/details/<file_id>', methods=['GET'])
@login_restricted
def file_details(file_id):
    if file_id not in file_dict():
        return app.response_class(
            response=json.dumps({'msg': 'file id not registered'}),
            status=400,
            mimetype='application/json'
        )
    else:
        if 'questionnaire' not in file_dict()[file_id]:
            return app.response_class(
                response=json.dumps({'msg': 'file has not been processed'}),
                status=400,
                mimetype='application/json'
            )
        else:
            q = file_dict()[file_id]['questionnaire']
    assert isinstance(q, Questionnaire)

    pages_list = list(q.pages)
    return app.response_class(
        response=json.dumps({'msg': 'success',
                             'pages_list': [p.uid for p in file_dict()[file_id]['questionnaire'].pages],
                             'filename': file_dict()[file_id]['filename']}),
        status=200,
        mimetype='application/json'
    )


@app.route('/details/<file_id>', methods=['GET'])
@login_restricted
def details(file_id):
    if file_id not in file_dict():
        return app.response_class(
            response=json.dumps({'msg': 'file id not registered'}),
            status=400,
            mimetype='application/json'
        )
    else:
        if 'questionnaire' not in file_dict()[file_id]:
            try:
                process_xml(file_id)
            except ParseError as err:
                return app.response_class(
                    response=json.dumps({'msg': f'error while parsing file: {err.msg}'}),
                    status=400,
                    mimetype='application/json'
                )
    # return app.response_class(
    #     response=json.dumps({'msg': 'file has not been processed'}),
    #     status=400,
    #     mimetype='application/json'
    # )

    q = file_dict()[file_id]['questionnaire']
    assert isinstance(q, Questionnaire)

    # details_data = prepare_dict_for_html(qml_details(q, file_id))
    details_data = qml_details(q, file_id)
    return render_template('details.html', details_data=details_data)


def serialize(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, VarRef):
        serial = obj.__dict__
        return {obj.variable.name: [obj.variable.type, obj.condition]}

    return obj.__dict__


# def prepare_dict_for_html(input_dict) -> Dict[str, List[str]]:
#     details_data = OrderedDict()
#     for k1, v1 in input_dict.items():
#         if v1:
#             if isinstance(v1, str):
#                 pass
#             elif isinstance(v1, list):
#                 details_data[k1] = [v1]
#             elif isinstance(v1, dict):
#                 tmp_dict = OrderedDict()
#                 tmp_keys_list = list(input_dict[k1].keys())
#                 tmp_keys_list.sort()
#                 details_data[k1] = []
#                 for k2 in tmp_keys_list:
#                     v2 = input_dict[k1][k2]
#                     if isinstance(v2, list):
#                         v2.sort(key=lambda x: x)
#                     details_data[k1].append(json.dumps({k2: v2}, default=serialize))
#                 # details_data[k1] = {str((k2, [str(val) for val in v2] if isinstance(v2, list) else [v2])) for k2, v2 in input_dict[k1].items()}
#             else:
#                 raise NotImplementedError()
#
#         else:
#             details_data[k1] = ["--"]
#     return details_data


@app.route('/flowchart/<file_id>', methods=['GET'])
@login_restricted
def flowchart(file_id):
    flowchart_i = file_id[file_id.rfind('_') + 1:]
    file_id = file_id[:file_id.rfind('_')]

    if file_id not in file_dict():
        return app.response_class(
            response=json.dumps({'msg': 'file id not registered'}),
            status=400,
            mimetype='application/json'
        )
    else:
        if 'questionnaire' not in file_dict()[file_id]:
            return app.response_class(
                response=json.dumps({'msg': 'file has not been processed'}),
                status=400,
                mimetype='application/json'
            )

    flowchart_file = file_dict()[file_id]['flowchart'][int(flowchart_i)]
    return send_file(flowchart_file)


@app.route('/api/upload', methods=['POST'])
@login_restricted
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


@app.route('/api/remove/<file_id>', methods=['GET'])
@login_restricted
def remove_file(file_id):
    if file_id not in file_dict():
        return app.response_class(
            response=json.dumps({'msg': 'file id not registered'}),
            status=400,
            mimetype='application/json'
        )
    else:
        file_dict().pop(file_id)

    return app.response_class(
        response=json.dumps({'msg': 'success'}),
        status=200,
        mimetype='application/json'
    )


@app.route('/remove/<file_id>', methods=['GET'])
@login_restricted
def remove_file_link(file_id):
    if file_id not in file_dict():
        return app.response_class(
            response=json.dumps({'msg': 'file id not registered'}),
            status=400,
            mimetype='application/json'
        )
    else:
        file_dict().pop(file_id)
    return redirect('/upload')


def main():
    try:
        app.run(host='0.0.0.0')
    finally:
        if 'upload_dir' in app.config:
            app.config['upload_dir'].cleanup()


if __name__ == '__main__':
    main()
