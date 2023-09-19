import importlib
import os
import re
import secrets
import textwrap
import uuid
from collections import defaultdict
from functools import wraps
from pathlib import Path
from typing import Dict, Optional, Union, Tuple

import lxml.etree
import waitress as waitress
from qform.hash import verify_password
from qrt.util.qmlgen import gen_mqsc
from qrt.util.util import qml_details
from qrt.util.graph import make_flowchart
from flask import Flask, render_template, request, json, send_file, session, flash, Request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename, redirect
from tempfile import TemporaryDirectory
import random
from string import hexdigits
from qrt.util.qml import read_xml, Questionnaire, VarRef
from xml.etree.ElementTree import ParseError
from dotenv import load_dotenv

load_dotenv()

__version__ = "0.0.2"

app = Flask(__name__)
app.debug = True
app.config['upload_dir'] = TemporaryDirectory()
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = secrets.token_hex(16)


@app.context_processor
def utility_processor():
    def calc_rows(input_str: str, cols: int) -> int:
        return max([len(textwrap.wrap(input_str, cols)), 1])

    return dict(calc_rows=calc_rows)


def cleanup_credentials(cred: Union[str, None]):
    if cred is not None:
        cred = cred.strip()
        if len(cred) == 0:
            cred = None
    return cred


flask_user = cleanup_credentials(os.environ.get('FLASK_USER'))
flask_pw_hash = cleanup_credentials(os.environ.get('FLASK_PW_HASH'))

limiter = Limiter(app=app, key_func=get_remote_address)

ALLOWED_EXTENSIONS = ['xml']
FILE_DICT = None
GEN_DICT = None
SESSION_LIST = None


def log_in():
    session['logged_in'] = True
    session['uid'] = uuid.uuid4()
    session_list().append(session['uid'])


def log_out():
    file_ids_list = [k for k, v in file_dict().items() if v['session_uid'] == session.get('uid')]
    [file_dict().pop(file_id) for file_id in file_ids_list]
    session_list().remove(session['uid'])
    session.clear()


def login_restricted(func):
    @wraps(func)
    def func_wrapper(*args, **kwargs):
        if flask_user is None or flask_pw_hash is None:
            flash('not configured')
            return render_template('login.html')
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


def session_list():
    global SESSION_LIST
    # review simple file dict - might be cleared when app is reinitialized

    if SESSION_LIST is None:
        SESSION_LIST = []

    return SESSION_LIST


@app.errorhandler(400)
def page_not_found(e):
    flash(f'{e.description}')
    return index()


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
    if not session.get('logged_in'):
        return render_template('login.html')
    return redirect('upload')


@app.route('/login', methods=['POST'])
@limiter.limit("100/day")
@limiter.limit("10/minute")
def do_login():
    if flask_pw_hash is None or flask_pw_hash.strip() == '' or \
            flask_user is None or flask_user.strip() == '':
        flash('no users have been set, login is not possible')
        return index()
    us_correct = request.form['username'].encode('utf-8') == flask_user.encode('utf-8')
    pw_correct = False
    try:
        pw_correct = verify_password(request.form['password'], flask_pw_hash)
    except ValueError as err:
        flash(err.args[0])
    if pw_correct and us_correct:
        log_in()
        return index()
    else:
        flash('wrong password!')
    return index()


@app.route('/logout', methods=['GET'])
@limiter.limit("100/day")
@limiter.limit("10/minute")
def do_logout():
    log_out()
    return index()


@app.route('/login', methods=['GET'])
@limiter.limit("100/day")
@limiter.limit("10/minute")
def get_login():
    return index()


def get_flashed_messages():
    return session.get('_flashes')


@app.route('/upload', methods=['GET'])
@login_restricted
def upload():
    uploaded_files = [{k: v for k, v in f.items() if k not in ['questionnaire']} for f in file_dict().values() if
                      f['session_uid'] == session.get('uid')]
    # uploaded_files = list(file_dict().values())
    return render_template('upload.html', uploaded_files=uploaded_files, flowcharts=uploaded_files,
                           version=__version__)


@app.route('/gen_mqsc', methods=['GET'])
@login_restricted
def form_mqsc():
    gen_data = gen_dict()
    if gen_data == {}:
        gen_data = {'type': 'mqsc',
                    'q_uid': 'mqsc',
                    'q_visible': '',
                    'headers': {
                        1: {'uid': 'q1',
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
                            'visible': '',
                            'attached_opens': {}}
                    }
                    }
    return render_template('gen_mqsc.html', gen_data=gen_data)


def nested_dict(input_dict: Dict[str, str], prefix: str) -> Dict[int, Dict[str, str]]:
    result = defaultdict(dict)
    for k, v in input_dict.items():
        if not k.startswith(prefix):
            continue
        try:
            result[int(k.split('_')[0].strip(prefix))][k.split('_')[1]] = v
        except ValueError as err:
            print()
    if prefix == 'item':
        print()
        tmp_dict = {}
        for k, v in input_dict.items():
            if not k.startswith('item'):
                continue
            elif k.find('attop') == -1:
                continue
            else:
                it_index = int(k[len('item'):].split('_')[0])
                tmp_str = k[len(f'item{it_index}'):]
                attop_index = int(tmp_str.lstrip('_').split('_')[0].replace('attop', ''))
                attop_key = tmp_str.lstrip('_').split('_')[1]
                if 'attached_opens' not in result[it_index]:
                    result[it_index]['attached_opens'] = {}
                if attop_index not in result[it_index]['attached_opens']:
                    result[it_index]['attached_opens'][attop_index] = {}
                result[it_index]['attached_opens'][attop_index][attop_key] = v

        # {k.strip('item').split('_')[0]: {k.strip('item').split('_')[1:]: v} for k, v in input_dict.items() if k.startswith('item')}

    return result


def get_action_obj(input_request: Request) -> Optional[Tuple[str, int, str]]:
    for action in ['down', 'up', 'remove', 'add_attached_open']:
        if action in request.form:
            obj_type = None
            target = request.form[action]
            if target.startswith('header'):
                obj_type = 'header'
            elif target.startswith('ao'):
                obj_type = 'ao'
            elif target.startswith('item'):
                if target.find('attop') == -1:
                    obj_type = 'item'
                else:
                    search_index = target.find('attop')
                    obj_type = 'attop' + target[search_index + len('attop'):]
            elif target.startswith('add_attached_open'):
                obj_type = 'add_attached_open'
            else:
                return None
            obj_index = int(target.replace(obj_type, ''))
            return action, obj_index, obj_type
    return None


@app.route('/gen_mqsc', methods=['POST'])
@login_restricted
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
            if len(data['headers']) == 0:
                new_key = 1
            else:
                new_key = max(data['headers'].keys()) + 1
            tmp_dict = {max(data['headers'].keys()) + 1: {'uid': f'q{max(data["headers"].keys()) + 1}',
                                                          'visible': '',
                                                          'type': 'question',
                                                          'value': '',
                                                          'text': ''}}
            data['headers'].update(tmp_dict)

        elif action == 'add_item':
            tmp_dict = {max(data['items'].keys()) + 1: {'uid': f'it{max(data["items"].keys()) + 1}',
                                                        'variable': '',
                                                        'text': '',
                                                        'visible': '',
                                                        'attached_opens': {}
                                                        }}
            data['items'].update(tmp_dict)

        elif action == 'add_ao':
            tmp_dict = {max(data['aos'].keys()) + 1: {'uid': f'ao{max(data["aos"].keys()) + 1}',
                                                      'value': '',
                                                      'label': '',
                                                      'visible': ''
                                                      }}
            data['aos'].update(tmp_dict)

        elif action == 'gen_xml':
            data['qml'] = generate_mqsc(data)
            data['html'] = "html"

        elif action == 'update':
            pass

    action_data = get_action_obj(request)
    if action_data is not None:
        obj_action, obj_index, obj_type = action_data
        if obj_action == 'add_attached_open':
            if obj_index in data['items']:
                if 'attached_opens' not in data['items'][obj_index]:
                    data['items'][obj_index]['attached_opens'] = {}
                    new_index = 1
                elif len(
                        data['items'][obj_index]['attached_opens']) == 0:
                    new_index = 1
                else:
                    new_index = max(data['items'][obj_index]['attached_opens'].keys()) + 1
                data['items'][obj_index]['attached_opens'][new_index] = {
                    'uid': f'att{new_index}', 'prefix': '', 'postfix': '',
                    'visible': ''}
        elif obj_action == 'remove':
            if obj_index in data[obj_type + 's']:
                data[obj_type + 's'].pop(obj_index)
        elif obj_action in ['up', 'down'] and obj_index in data[obj_type + 's']:
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
                # ToDo: comment and fix line below
                new_dict[new_index]['uid'] = re.sub(r'[0-9]+', '', data[obj_type + 's'][k]['uid']) + str(new_index)
            data[obj_type + 's'] = new_dict
    gen_dict().clear()
    gen_dict().update(data)

    return render_template('gen_mqsc.html', gen_data=gen_dict())


@app.route('/api/gen_mqsc', methods=['POST'])
@login_restricted
def generate_mqsc(data_dict):
    return gen_mqsc(data_dict)


def process_xml(file_id) -> None:
    file_meta = file_dict()[file_id]
    filename = file_meta['internal_filename']
    try:
        q = read_xml(Path(upload_dir(), filename))
    except ParseError:
        try:
            lxml.etree.parse(Path(upload_dir(), filename))
        except lxml.etree.XMLSyntaxError as synterr:
            raise ParseError(synterr.msg)
    file_dict()[file_id]['questionnaire'] = q


def process_graphs(file_id):
    if importlib.util.find_spec('pygraphviz') is None:
        raise ModuleNotFoundError('module "pygraphviz" not found')

    file_meta = file_dict()[file_id]
    flowchart_file1 = Path(upload_dir(), file_id + '_flowchart_var_cond.svg')
    flowchart_file2 = Path(upload_dir(), file_id + '_flowchart_var.svg')
    flowchart_file3 = Path(upload_dir(), file_id + '_flowchart.svg')
    flowchart_file4 = Path(upload_dir(), file_id + '_flowchart_var_cond_repl.svg')

    make_flowchart(q=file_meta['questionnaire'], out_file=flowchart_file4, show_var=False, show_cond=False,
                   color_nodes=True, replace_zofar_cond=True)
    make_flowchart(q=file_meta['questionnaire'], out_file=flowchart_file3, show_var=False, show_cond=False,
                   color_nodes=True)
    make_flowchart(q=file_meta['questionnaire'], out_file=flowchart_file2, show_var=True, show_cond=False)
    make_flowchart(q=file_meta['questionnaire'], out_file=flowchart_file1, show_var=True, show_cond=True)

    file_meta['flowchart'] = [str(flowchart_file1), str(flowchart_file2), str(flowchart_file3), str(flowchart_file4)]


@app.route('/api/process/<file_id>', methods=['GET'])
@login_restricted
def process_file(file_id):
    if file_id not in [k for k, v in file_dict().items() if v['session_uid'] == session.get('uid')]:
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
        print("xml")
        process_xml(file_id)

    except ParseError as err:
        return app.response_class(
            response=json.dumps({'msg': f'error while parsing file: {err.msg}'}),
            status=400,
            mimetype='application/json'
        )

    try:
        process_graphs(file_id)
    except ModuleNotFoundError as err:
        print(err)
        return app.response_class(
            response=json.dumps({'msg': err.msg}),
            status=400,
            mimetype='application/json'
        )

    return app.response_class(
        response=json.dumps({'msg': 'success'}),
        status=200,
        mimetype='application/json'
    )


@app.route('/api/details/<file_id>', methods=['GET'])
@login_restricted
def file_details(file_id):
    if file_id not in [k for k, v in file_dict().items() if v['session_uid'] == session.get('uid')]:
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
    q = file_dict()[file_id]['questionnaire']
    assert isinstance(q, Questionnaire)

    details_dict = qml_details(file_dict()[file_id]['questionnaire'], file_dict()[file_id]['filename'])
    assert 'msg' not in details_dict
    return app.response_class(
        response=json.dumps({'msg': 'success', **details_dict}),
        status=200,
        mimetype='application/json'
    )


@app.route('/details/<file_id>', methods=['GET'])
@login_restricted
def details(file_id):
    api_response = file_details(file_id)
    if api_response.status_code != 200:
        return app.response_class(
            response=json.dumps(api_response.json),
            status=api_response.status_code,
            mimetype='application/json'
        )
    else:
        details_data = api_response.json
        details_data.pop('msg')
        return render_template('details.html', details_data=details_data)


def serialize(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, VarRef):
        serial = obj.__dict__
        return {obj.variable.name: [obj.variable.type, obj.condition]}

    return obj.__dict__


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
    file_dict()[file_id] = {'file_id': file_id, 'filename': file.filename, 'internal_filename': internal_filename,
                            'session_uid': session.get('uid')}

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
        waitress.serve(app, host="0.0.0.0", port=int(os.getenv("SERVICE_PORT")))
        # app.run(host='0.0.0.0')
    finally:
        if 'upload_dir' in app.config:
            app.config['upload_dir'].cleanup()


if __name__ == '__main__':
    main()
