# sfn_service.py
"""Implementation of a RESTful webservice to handle messages produced from the VCA framework and forward them on to
linksmart"""
import argparse
import requests
import json
import datetime
import time
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from redis import Redis
from rq import Queue
from rq.job import Job
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).absolute().parents[3]))
from KU.SecurityFusionNodeService.SecurityFusionNode.security_fusion_node import SecurityFusionNode
from KU.SecurityFusionNodeService.SecurityFusionNode.message_processing import crowd_density_local,  flow_analysis, \
    amalgamate_crowd_density_local, fighting_detection, object_detection

__version__ = '0.2'
__author__ = 'RoViT (KU)'

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sfn_database.db'
# sfn_db = SQLAlchemy(app)
sfn_module = SecurityFusionNode('001')
urls = sfn_module.load_urls(str(Path(__file__).absolute().parents[0]), 'urls')

headers = {'content-Type': 'application/json'}
# QUEUE VARIABLES
conn = Redis()
queue_name = 'default'
q = Queue(name=queue_name, connection=conn)

# TODO: SEND THE REGISTRATION MESSAGE


@app.route("/")
def hello_world():
    print('REQUEST: HELLO WORLD')
    return "SECURITY FUSION NODE"


@app.route("/urls", methods=['POST'])
def update_urls():
    print('REQUEST: UPDATE URLS')
    if request.is_json:
        url_updates = request.get_json(force=True)
        # CHECK IF ITS STILL A STRING AND IF SO LOAD FROM JSON FORMAT
        if type(url_updates) == str:
            url_updates = json.loads(url_updates)

        global urls
        for url in urls:
            if url in url_updates:
                urls[url] = url_updates[url]
                print('Updating Key ({}) to: {}.'.format(url, url_updates[url]))
            else:
                print('Key ({}) not found.'.format(url))

        return 'SFN urls updated', 201
    else:
        return 'No JSON.', 415


@app.route("/register")
def register_sfn():
    print('REQUEST: SEND SFN REGISTRATION')
    data = sfn_module.create_reg_message(datetime.datetime.utcnow().isoformat())
    try:
        resp = requests.post(urls['crowd_density_url'], data=data, headers=headers)
    except requests.exceptions.RequestException as e:
        print(e)
        return 'Linksmart Connection Failed: ' + str(e), 450
    else:
        print('SFN CONFIG ADDED: ' + resp.text, resp.status_code)
        return 'Registered SFN: ' + resp.text, resp.status_code


@app.route('/message', methods=['PUT'])
def add_message():
    print('REQUEST: ADD MESSAGE')
    start = time.time()
    if request.is_json:
        log_text = ''
        resp_code = 0
        # GET THE JSON AND CHECK IF ITS STILL A STRING, IF SO loads JSON FORMAT
        message = request.get_json(force=True)
        if type(message) == str:
            message = json.loads(message)

        camera_id = message['camera_ids'][0]
        wp_module = message['type_module']

        # BEGINNING OF QUE INTEGRATION
        # for i in range(10):
        #     j = Job.create(func=mp.waste_time, args=(10,), id=str(i), connection=conn, ttl=43)
        #     job = q.enqueue_job(j)
        # print('Current Number of Jobs = {}'.format(len(q.get_job_ids())))
        # print('Function has taken: {}s'.format(time.time() - start))
        # BASED ON wp_module PERFORM PROCESSING ON MODULE
        text = ''
        if wp_module == 'crowd_density_local':
            text, resp_code = crowd_density_local(sfn_module, camera_id, urls['crowd_density_url'], message, start)
        elif wp_module == 'flow':
            text, resp_code = flow_analysis(sfn_module, camera_id, urls['flow_analysis_url'], message, start)
        elif wp_module == 'fighting_detection':
            text, resp_code = fighting_detection(sfn_module, camera_id, urls['flow_analysis_url'], message, start)
        elif wp_module == 'object_detection':
            text, resp_code = object_detection(sfn_module, camera_id, urls['flow_analysis_url'], message, start)
        # print('Function has taken: {}s'.format(time.time() - start))
        log_text = log_text + text

        # UNDER AND IF STATEMENT CHECK IF WE WANT TO AMALGAMATE AND CREATE A NEW MESSAGE
        sfn_module.timer = time.time() - sfn_module.last_amalgamation
        if sfn_module.length_db(module_id='crowd_density_local') > 2 and sfn_module.timer > 10:
            text, resp_code = amalgamate_crowd_density_local(sfn_module, urls['crowd_density_url'], start)
            sfn_module.last_amalgamation = time.time()
        else:
            # NO MESSAGES HELD
            text = 'MESSAGES in recent_cam_messages {}. Time since last run {} '.\
                format(sfn_module.length_db(), sfn_module.timer)

        log_text = log_text + text
        print(log_text)
        print('Function has taken: {}s'.format(time.time() - start))
        return log_text, resp_code
    else:
        return 'No JSON.', 415


# ROUTE FOR VCA TO UPDATE CONFIGS
@app.route("/configs", methods=['POST'])
def update_configs():
    print('REQUEST: UPDATE THE CONFIG DB')
    if request.is_json:
        new_configs = request.get_json(force=True)
        # CHECK IF ITS STILL A STRING AND IF SO LOAD FROM JSON FORMAT
        if type(new_configs) == str:
            new_configs = json.loads(new_configs)

        log_text = ''
        for config in new_configs:
            if 'camera_id' in config:
                log_text = sfn_module.insert_config_db(c_id=config['camera_id'], msg=json.dumps(config))
            elif 'module_id' in config:
                log_text = sfn_module.insert_config_db(c_id=config['module_id'], msg=json.dumps(config))
            print(log_text)
        return log_text, 200
    else:
        return 'No JSON.', 415


# JOB ID CHECK
@app.route('/result', methods=['POST'])
def get_result():
    print('REQUEST: CHECK JOB STATUS')
    if request.is_json:
        # GET THE JSON AND CHECK IF ITS STILL A STRING, IF SO loads JSON FORMAT
        message = request.get_json(force=True)
        if type(message) == str:
            message = json.loads(message)
        job = Job.fetch(message['job_key'], connection=conn)
        if job.is_finished:
            return str(job.result), 206
        else:
            return 'Job not Finished', 406
    else:
        return 'No JSON.', 499


# ROUTES FOR THE DUMMY LINKSMART ONLY
@app.route("/linksmart")
def hello_linksmart():
    print('REQUEST: HELLO LINKSMART')
    try:
        resp = requests.get(urls['dummy_linksmart_url'])
    except requests.exceptions.RequestException as e:
        print(e)
        return 'Dummy Linksmart Connection Failed: ' + str(e), 502
    else:
        print(resp.text, resp.status_code)
        return resp.text + ' VIA SECURITY FUSION NODE', 200


@app.route("/linksmart/get_configs")
def get_configs_linksmart():
    print('REQUEST: GET THE CONFIGS FROM LINKSMART')
    try:
        resp = requests.get(urls['dummy_linksmart_url'] + 'configs')
    except requests.exceptions.RequestException as e:
        print(e)
        return 'Dummy Linksmart Connection Failed: ' + str(e), 502
    else:
        global cam_configs
        cam_configs = resp.json()
        text = ''
        # GET A LIST OF CONFIG DICTS, LOOP THROUGH AND ADD TO DB
        for config in cam_configs:
            if 'camera_id' in config:
                text = sfn_module.insert_config_db(c_id=config['camera_id'], msg=json.dumps(config))
            elif 'module_id' in config:
                text = sfn_module.insert_config_db(c_id=config['module_id'], msg=json.dumps(config))

        print('{} NUM CONFIGS RETURNED = {}, {}'.format(text, len(sfn_module.query_config_db()), resp.status_code))
        return 'OBTAINED CONFIGS VIA SECURITY FUSION NODE: ' + str(sfn_module.query_config_db()), 200


# RUN THE SERVICE
parser = argparse.ArgumentParser(description='Development Server Help')
parser.add_argument("-d", "--debug", action="store_true", dest="debug_mode",
                    help="run in debug mode (for use with PyCharm)", default=False)
parser.add_argument("-p", "--port", dest="port",
                    help="port of server (default:%(default)s)", type=int, default=5000)
parser.add_argument("-a", "--address", dest="host",
                    help="host address of server (default:%(default)s)", type=str, default="0.0.0.0")
                    # help="host address of server (default:%(default)s)", type=str, default="127.0.0.1")

cmd_args = parser.parse_args()
app_options = {"port": cmd_args.port,
               "host": cmd_args.host}

if cmd_args.debug_mode:
    app_options["debug"] = True
    app_options["use_debugger"] = False
    app_options["use_reloader"] = False

app.run(**app_options)

# TODO: ADD ON EXIT FUNCTIONALITY, CLOSE DBS etc
