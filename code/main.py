#!/bin/python3

import logging
import os
import yaml
from flask import Flask, request, jsonify

from monorepo import Monorepo
from github import Github


app = Flask("monorepo")
app.logger.setLevel(logging.getLevelName(os.environ["LOG_LEVEL"]))


with open(os.environ["TOKEN_PATH"], "r") as f:
    token = f.read().strip()


@app.route("/healthz", methods=["GET"])
def handle_health():
    return jsonify({})


@app.route("/", methods=["POST"])
def handle():
    body = request.get_json(force=True)

    repo = body["repo"]["slug"]
    before = body["build"]["before"]
    after = body["build"]["after"]
    if before == after:
        before = f"{ before }~1"

    ghub = Github(repo, before, after, token)

    mono = Monorepo(ghub)
    return_pipelines = []
    base_pipeline = None
    pipelines_to_process = body["config"]["data"].split("---")

    while len(pipelines_to_process) > 0:
        pipe = pipelines_to_process.pop(0)
        if isinstance(pipe, str):
          pipe = yaml.safe_load(pipe)

        if not pipe:
            app.logger.debug("skip pipeline processing")
            continue
        elif base_pipeline is None:
            base_pipeline = pipe.copy()

        app.logger.debug(f"Parse { pipe['name'] }")

        result, returned = mono.parse_pipeline(pipe)

        if result:
            app.logger.debug("Returned: ")
            app.logger.debug(returned)
            if len(returned) > 1:
                pipelines_to_process += returned
            else:
                return_pipelines.append(yaml.safe_dump(pipe))

    if len(return_pipelines) > 0:
      app.logger.debug("Returning the following pipelines:")
      app.logger.debug("\n---\n".join(return_pipelines))
      return jsonify({"data": "\n---\n".join(return_pipelines)})
    else:
      empty = { key: value for key, value in base_pipeline.items() if key not in ["trigger", "triggers", "steps"] }

      empty['name'] = "empty"
      empty["steps"] = [{
        "name": "empty",
        "image": "busybox",
        "commands": ["echo 'This build has no steps to execute.'"]
      }]
      app.logger.debug("empty pipeline")

      return jsonify({"data": yaml.safe_dump(empty) })


if __name__ == "__main__":
    if "TLS_CERT_PATH" in os.environ and "TLS_KEY_PATH" in os.environ:
        app.run(
            host="0.0.0.0",
            port=3000,
            ssl_context=(os.environ["TLS_CERT_PATH"], os.environ["TLS_KEY_PATH"]),
        )
    else:
        app.run(host="0.0.0.0", port=3000)
