from flask import Flask, abort, jsonify, request
from flask_cors import CORS

from mock_server.stateful_thing import StatefulThing

app = Flask(__name__)
cors = CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"

stateful_thing = StatefulThing()


@app.route("/submit-optimisation-job/", methods=["POST"])
def submit_config():

    print(request.json)

    stateful_thing.run_epoch()

    info = stateful_thing.get_full_status()

    return jsonify(info)


@app.route("/get-status/")
def get_status():
    info = stateful_thing.get_full_status()

    return jsonify(info)

