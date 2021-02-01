import base64
import logging
import requests
import yaml

logger = logging.getLogger("monorepo")


class Github:
    def __init__(self, token):
        self.token = token
        self.headers = {"Authorization": f"token { token }"}

    def get_included_pipeline(self, path, repo, commit):
        logger.debug(f"Including: { repo }/contents/{ path }?ref={ commit }")
        resp = requests.get(
            f"https://api.github.com/repos/{ repo }/contents/{ path }?ref={ commit }",
            headers=self.headers,
        ).json()

        if "content" not in resp:
            logger.info(f"Couldn't load pipeline { path }")
            return ""
        else:
            text_to_replace = base64.b64decode(resp["content"]).decode("utf-8")
            pipeline_text = text_to_replace.replace(
                "<current_path>", "/".join(path.split("/")[:-1])
            )
            return yaml.safe_load(pipeline_text)

    def get_commit_changed_files(self, repo, before, after):
        rep = requests.get(
            f"https://api.github.com/repos/{ repo }/compare/{ before }...{ after }",
            headers=self.headers,
        )

        logger.debug(f"Response from github: { str(rep.status_code) }")

        if rep.status_code == 404:
            return []
        else:
            return [f["filename"] for f in rep.json()["files"]]