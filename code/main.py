#!/bin/python3

import logging
import os
import yaml
from flask import Flask, request, jsonify

from parsers.includes import IncludesParser
from parsers.paths import PathsChangedParser
from parsers.trigger_groups import TriggerGroupsParser
from parsers.target_pipelines import TargetPipelineParser
from backends.github import Github
from models.pipelines import Pipeline
from models.steps import Step

from monorepo import Monorepo

app = Flask("monorepo")
app.logger.setLevel(logging.getLevelName(os.environ["LOG_LEVEL"]))

from json import JSONEncoder

def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)

_default.default = JSONEncoder().default
JSONEncoder.default = _default

with open(os.environ["TOKEN_PATH"], "r") as f:
    token = f.read().strip()

mono = Monorepo(Github(token))


@app.route("/healthz", methods=["GET"])
def handle_health():
    return jsonify({})


@app.route("/", methods=["POST"])
def handle():
    body = request.get_json(force=True)

    others = []
    raw_pipelines = body["config"]["data"].split("---")
    app.logger.debug("Pipelines:")

    init_pipelines = []
    for r in raw_pipelines:
      if r == "":
        continue
      
      # app.logger.debug(f"|{ r }|")
      parsed = yaml.safe_load(r)
      if parsed is None:
          continue
      elif 'kind' in parsed and parsed['kind'] != "pipeline":
          others.append(r)
          continue

      init_pipelines.append(Pipeline(parsed))

    parsers = [
      IncludesParser(mono.get_backend(), body),
      TriggerGroupsParser(mono.get_backend(), body),
      PathsChangedParser(mono.get_backend(), body),
      TargetPipelineParser(mono.get_backend(), body)
    ]

    mono.set_parsers(parsers)
    pipelines = mono.parse_pipelines(init_pipelines)

    if len(pipelines) > 0:
      app.logger.debug("Returning the following pipelines:")
      app.logger.debug("\n---\n".join([yaml.safe_dump(p.to_json()) for p in pipelines ] + [o for o in others]))
  
      return jsonify({"data": "\n---\n".join([yaml.safe_dump(p.to_json()) for p in pipelines ] + [o for o in others])})
    else:
      app.logger.debug("empty pipeline")

      empty = {
        'name': 'empty',
        'steps': [{
          'name': 'empty',
          'image': 'busybox',
          'commands': ["echo 'This build has no steps to execute.'"]
        }],
        'kind': 'pipeline',
        'type': os.environ['DEFAULT_PIPELINE_TYPE'],
        'platform': {
            'os': os.environ['DEFAULT_PLATFORM'].split('-')[0],
            'arch':  os.environ['DEFAULT_PLATFORM'].split('-')[1]
        }
      }

      app.logger.debug(empty)

      return jsonify(
        {
          "data": yaml.safe_dump(empty)
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
