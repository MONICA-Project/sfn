import argparse
import requests
import json
import datetime
import os
from flask import Flask, request
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).absolute().parents[4]))
from WP5.KU.definitions import KU_DIR
import WP5.KU.SecurityFusionNodeService.loader_tools as tools
from WP5.KU.SecurityFusionNodeService.SecurityFusionNode.security_fusion_node import SecurityFusionNode

app = Flask(__name__)
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

        return log_text, 205
    else:
        return 'Aint no JSON.', 499


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
