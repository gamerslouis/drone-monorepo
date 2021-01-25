#!/bin/python3

from flask import Flask, request, jsonify
import logging, os, yaml, requests, fnmatch, re, base64

app = Flask(__name__)

headers = {}


@app.route("/healthz", methods=["GET"])
def handle_health():
    return jsonify({})


def parse_pipeline(repo, pipe, commit, commit_changed_files):
    app.logger.debug("Parsing pipeline:")
    app.logger.debug(pipe)
    skip_pipeline = True
    add_pipelines = []

    if "trigger" not in pipe or "paths" not in pipe["trigger"]:
        skip_pipeline = False
    elif "paths" in pipe["trigger"]:
        if isinstance(pipe["trigger"]["paths"], list):
            pipe["trigger"]["paths"] = {"include": pipe["trigger"]["paths"]}

        app.logger.debug("Pipeline path triggers: ")
        if "include" in pipe["trigger"]["paths"]:
            app.logger.debug(
                "Includes: " + ",".join(pipe["trigger"]["paths"]["include"])
            )
        if "exclude" in pipe["trigger"]["paths"]:
            app.logger.debug(
                "Excludes: " + ",".join(pipe["trigger"]["paths"]["exclude"])
            )

        skip_pipeline = not compare_list_with_patterns(
            commit_changed_files, pipe["trigger"]["paths"]
        )
        del pipe["trigger"]["paths"]
        if len(pipe["trigger"].keys()) == 0:
            del pipe["trigger"]

    if not skip_pipeline:
        if "include_pipeline" in pipe:
            included = get_included_pipeline(repo, commit, pipe["include_pipeline"])
            del pipe["include_pipeline"]

            if included != "":
                add_pipelines.append(yaml.dump(merge_pipeline(pipe, included)))

            pipe = False
        elif "steps" in pipe:
            pipeline_steps = []
            for step in pipe["steps"]:
                skip_step = False

                if "when" in step and "paths" in step["when"]:
                    skip_step = not compare_list_with_patterns(
                        commit_changed_files, step["when"]["paths"]
                    )

                if not skip_step:
                    pipeline_steps.append(step)

            if len(pipeline_steps) > 0:
                pipe["steps"] = pipeline_steps
            else:
                pipe = None
    else:
        pipe = False

    return add_pipelines, pipe


@app.route("/", methods=["POST"])
def handle():
    body = request.get_json(force=True)
    app.logger.debug(body)
    m = re.search("https?://.+?/(.+?/.+?)/commit/(.+)", body["build"]["link"])
    app.logger.debug(body["build"]["link"])

    if m != None:
      url = f"https://api.github.com/repos/{ m.group(1) }/compare/{ m.group(2) }~1...{ m.group(2) }"
    else:
      url = body["build"]["link"]

    rep = requests.get(
        url,
        headers=headers,
    )
    app.logger.debug(f"Response from github: { str(rep.status_code) }: { rep.json() }")
    
    if rep.status_code == 404:
      commit_changed_files = []
    else:
      commit_changed_files = [f["filename"] for f in rep.json()["files"]]

    return_pipelines = []
    pipelines = body["config"]["data"].split("---")
    app.logger.debug("PIPELINES:")
    app.logger.debug(pipelines)
    app.logger.debug("END")

    while len(pipelines) > 0:
        pipe = yaml.safe_load(pipelines.pop(0))

        if not pipe:
            app.logger.debug("skip pipeline processing")
            continue

        add_pipelines, final_pipeline = parse_pipeline(
            repo, pipe, commit, commit_changed_files
        )
        if final_pipeline:
            return_pipelines.append(yaml.safe_dump(final_pipeline))

        pipelines += add_pipelines
    app.logger.debug("Finished:")
    app.logger.debug("\n---\n".join(return_pipelines))
    return jsonify({"data": "\n---\n".join(return_pipelines)})


def compare_list_with_patterns(
    paths, patterns
) -> bool:  # if true, an include match was found, if false, an exclude match was found or no match was found
    for p in paths:
        if "exclude" in patterns:
            for pat in patterns["exclude"]:
                if fnmatch.fnmatch(p, pat):
                    app.logger.debug("excluding due to matching " + p + " with " + pat)
                    return False

        if "include" in patterns:
            for pat in patterns["include"]:
                if fnmatch.fnmatch(p, pat):
                    app.logger.debug("including due to matching: " + p + " with " + pat)
                    return True

    return False


def get_included_pipeline(repo, commit, path):
    app.logger.debug(f"Including: { repo }/contents/{ path }?ref={ commit }")
    resp = requests.get(
        f"https://api.github.com/repos/{ repo }/contents/{ path }?ref={ commit }",
        headers=headers,
    ).json()

    if "content" not in resp:
        app.logger.info(f"Couldn't load pipeline { path }")
        return ""
    else:
        pipeline_text = replacements(
            path, base64.b64decode(resp["content"]).decode("utf-8")
        )
        return yaml.safe_load(pipeline_text)


def replacements(path, text):
    text.replace("<current_path>", "/".join(path.split("/")[:-1]))

    return text


def merge_pipeline(base, target):
    merged_pipeline = base.copy()

    for k, v in target.items():
        if k in merged_pipeline:
            if isinstance(v, str):
                merged_pipeline[k] = v
            elif isinstance(v, list):
                merged_pipeline[k] = merged_pipeline[k] + v
            elif isinstance(v, dict):
                merged_pipeline[k] = merge_dict(merged_pipeline[k], v, merge_dict)
        else:
            merged_pipeline[k] = v

    return merged_pipeline


def merge_dict(a, b, func):
    final = a.copy()
    for k, v in b.items():
        if k in final:
            if isinstance(v, dict):
                final[k] = func(final[k], v, func)
            else:
                final[k] = v

    return final


if __name__ == "__main__":
    with open(os.environ["TOKEN_PATH"], "r") as f:
        token = f.read().strip()

    headers = {"Authorization": f"token { token }"}

    app.logger.setLevel(logging.getLevelName(os.environ["LOG_LEVEL"]))

    if "TLS_CERT_PATH" in os.environ and "TLS_KEY_PATH" in os.environ:
        app.run(
            host="0.0.0.0",
            port=3000,
            ssl_context=(os.environ["TLS_CERT_PATH"], os.environ["TLS_KEY_PATH"]),
        )
    else:
        app.run(host="0.0.0.0", port=3000)
