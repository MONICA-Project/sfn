# sfn_service_queue.py
"""Implementation of a RESTful webservice with a queue task system to handle incoming messages produced from the VCA
framework and forward them on to linksmart"""
import argparse
import requests
import json
import datetime
import os
from rq import Queue
from rq.job import Job
from flask import Flask, request
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).absolute().parents[4]))
from WP5.KU.definitions import KU_DIR
import WP5.KU.SecurityFusionNodeService.loader_tools as tools
from WP5.KU.SecurityFusionNodeService.SecurityFusionNode.security_fusion_node import SecurityFusionNode
from WP5.KU.SecurityFusionNodeService.SecurityFusionNode.worker import conn

__version__ = '0.1'
__author__ = 'RoViT (KU)'

app = Flask(__name__)
q = Queue(connection=conn)

sfn = SecurityFusionNode('001')
linksmart_url = 'http://127.0.0.2:3389/'


@app.route("/")
def hello_world():
    print('REQUEST: HELLO WORLD')
    return "SECURITY FUSION NODE"


@app.route('/message', methods=['POST'])
def add_message():
    print('REQUEST: ADD MESSAGE START TASK')
    if request.is_json:
        log_text = ''
        job = q.enqueue_call(func=sfn.waste_time(20), result_ttl=5000)
        print(job.get_id)

        return job.key, 205
    else:
        return 'No JSON.', 499


@app.route('/result', methods=['POST'])
def get_result():
    print('REQUEST: CHECK JOB STATUS')
    if request.is_json:
        message = json.loads(request.get_json(force=True))
        job = Job.fetch(message['job_key'], connection=conn)
        if job.is_finished:
            return str(job.result), 206
        else:
            return 'Job not Finished', 406
    else:
        return 'No JSON.', 499


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
