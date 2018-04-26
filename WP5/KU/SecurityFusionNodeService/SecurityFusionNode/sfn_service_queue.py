# sfn_service_queue.py
"""Implementation of a RESTful webservice with a queue task system to handle incoming messages produced from the VCA
framework and forward them on to linksmart"""
import argparse
import requests
import json
import datetime
import os
from redis import Redis
from rq import Queue
from rq.job import Job
from rq.registry import StartedJobRegistry
from flask import Flask, request
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).absolute().parents[4]))
from WP5.KU.definitions import KU_DIR
import WP5.KU.SecurityFusionNodeService.loader_tools as tools
from WP5.KU.SecurityFusionNodeService.SecurityFusionNode.security_fusion_node import SecurityFusionNode
import WP5.KU.SecurityFusionNodeService.SecurityFusionNode.security_fusion_node as sfn
# from WP5.KU.SecurityFusionNodeService.SecurityFusionNode.sfn_worker import conn

__version__ = '0.1'
__author__ = 'RoViT (KU)'

app = Flask(__name__)
sfn_module = sfn.SecurityFusionNode('001')
urls = {'dummy_linksmart_url': 'http://127.0.0.2:3389/',
        # 'crowd_density_url': 'https://portal.monica-cloud.eu/scral/sfn/crowdmonitoring',
        'crowd_density_url': 'http://127.0.0.2:3389/crowd_density',
        'flow_analysis_url': 'http://127.0.0.2:3389/flow_analysis',
        }
headers = {'content-Type': 'application/json'}

cam_configs = []
recent_cam_messages = [
    # tools.load_json_txt(os.path.join(KU_DIR, 'Algorithms/'), 'KFF_CAM_8_00004')
                      ]
# QUEUE VARIABLES
conn = Redis()
queue_name = 'default'
q = Queue(name=queue_name, connection=conn)


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


@app.route('/message', methods=['POST'])
def add_message():
    print('REQUEST: ADD MESSAGE START TASK')
    if request.is_json:
        log_text = ''
        # GET THE JSON AND CHECK IF ITS STILL A STRING, IF SO loads JSON FORMAT
        message = request.get_json(force=True)
        if type(message) == str:
            message = json.loads(message)
        for i in range(10):
            job = q.enqueue(sfn.waste_time, 10, ttl=43)
        print('Current Number of Jobs = {}'.format(len(q.get_job_ids())))

        return job.get_id(), 205
    else:
        return 'No JSON.', 499


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
        return 'Dummy Linksmart Connection Failed: ' + e, 502
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
        return 'Dummy Linksmart Connection Failed: ' + e, 502
    else:
        global cam_configs
        cam_configs = resp.json()
        print('NUMBER OF CONFIGS RETURNED = ' + str(len(cam_configs)), resp.status_code)
        return 'OBTAINED CONFIGS VIA SECURITY FUSION NODE: ' + str(cam_configs), 200


# RUN THE SERVICE
parser = argparse.ArgumentParser(description='Development Server Help')
parser.add_argument("-d", "--debug", action="store_true", dest="debug_mode",
                    help="run in debug mode (for use with PyCharm)", default=False)
parser.add_argument("-p", "--port", dest="port",
                    help="port of server (default:%(default)s)", type=int, default=5000)
parser.add_argument("-a", "--address", dest="host",
                    # help="host address of server (default:%(default)s)", type=str, default="0.0.0.0")
                    help="host address of server (default:%(default)s)", type=str, default="127.0.0.1")

cmd_args = parser.parse_args()
app_options = {"port": cmd_args.port,
               "host": cmd_args.host}

if cmd_args.debug_mode:
    app_options["debug"] = True
    app_options["use_debugger"] = False
    app_options["use_reloader"] = False

app.run(**app_options)
