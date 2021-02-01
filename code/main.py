#!/bin/python3

import logging
import json
import os
import yaml
from flask import Flask, request, jsonify

from parsers.includes import IncludesParser
from parsers.paths import PathsChangedParser
from parsers.trigger_groups import TriggerGroupsParser
from backends.github import Github
from models.pipelines import Pipeline

from monorepo import Monorepo

app = Flask("monorepo")
app.logger.setLevel(logging.getLevelName(os.environ["LOG_LEVEL"]))

from json import JSONEncoder

def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)

_default.default = JSONEncoder().default
JSONEncoder.default = _default

mono = None
ghub = None

with open(os.environ["TOKEN_PATH"], "r") as f:
    token = f.read().strip()

mono = Monorepo(Github(token))


@app.route("/healthz", methods=["GET"])
def handle_health():
    return jsonify({})


@app.route("/", methods=["POST"])
def handle():
    body = request.get_json(force=True)

    raw_pipelines = body["config"]["data"].split("---")

    init_pipelines = [ Pipeline(yaml.safe_load(r)) for r in raw_pipelines if r != ""]
    # app.logger.debug("Parse the following pipelines:")
    # app.logger.debug(init_pipelines)

    base_pipeline = init_pipelines[0].clone()

    parsers = [
      IncludesParser(mono.get_backend(), body),
      TriggerGroupsParser(mono.get_backend(), body),
      PathsChangedParser(mono.get_backend(), body)
    ]

    mono.set_parsers(parsers)
    pipelines = mono.parse_pipelines(init_pipelines)

    if len(pipelines) > 0:
      app.logger.debug("Returning the following pipelines:")
      # for r in pipelines:
      #   app.logger.debug(json.dumps(r))
      app.logger.debug("\n---\n".join([p.to_text() for p in pipelines ]))
      return jsonify({"data": "\n---\n".join([p.to_text() for p in pipelines ])})
    else:
      app.logger.debug("empty pipeline")
      app.logger.debug(base_pipeline)
      return jsonify(
        {
          "data": str(Pipeline({
            'name': 'empty',
            'steps': [{
              "name": "empty",
              "image": "busybox",
              "commands": ["echo 'This build has no steps to execute.'"]
            }],
            'type': base_pipeline.get_type(),
            'kind': 'pipeline'
          }))
        }
      )


if __name__ == "__main__":
    if "TLS_CERT_PATH" in os.environ and "TLS_KEY_PATH" in os.environ:
        app.run(
            host="0.0.0.0",
            port=3000,
            ssl_context=(os.environ["TLS_CERT_PATH"], os.environ["TLS_KEY_PATH"]),
        )
    else:
        app.run(host="0.0.0.0", port=3000)
