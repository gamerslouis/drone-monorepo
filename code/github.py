import base64
import logging
import requests
import yaml

logger = logging.getLogger("monorepo")


class Github:
    def __init__(self, repo, before_commit, after_commit, token):
        self.token = token
        self.repo = repo
        self.before_commit = before_commit
        self.commit = after_commit
        self.headers = {"Authorization": f"token { token }"}
        self.commit_changed_files = None

    def get_included_pipeline(self, path):
        logger.debug(f"Including: { self.repo }/contents/{ path }?ref={ self.commit }")
        resp = requests.get(
            f"https://api.github.com/repos/{ self.repo }/contents/{ path }?ref={ self.commit }",
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

    def get_commit_changed_files(self):
        if self.commit_changed_files is not None:
            return self.commit_changed_files

        rep = requests.get(
            f"https://api.github.com/repos/{ self.repo }/compare/{ self.before_commit }...{ self.commit }",
            headers=self.headers,
        )

        logger.debug(f"Response from github: { str(rep.status_code) }")

        if rep.status_code == 404:
            return []
        else:
            return [f["filename"] for f in rep.json()["files"]]
