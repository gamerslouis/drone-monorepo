import logging
from triggers import parse_triggers

logger = logging.getLogger("monorepo")


class Monorepo:
    def __init__(self, github):
        self.ghub = github

    def parse_pipeline(self, pipe):
        # app.logger.debug("Parsing pipeline:")
        # app.logger.debug(pipe)

        if "include_pipeline" in pipe:
            included = self.ghub.get_included_pipeline(pipe["include_pipeline"])
            del pipe["include_pipeline"]

            if included != "":
                pipe = __merge_pipeline(pipe, included)

        pipeline_triggers = []
        if "trigger" in pipe:
            pipeline_triggers.append(pipe["trigger"])
            del pipe['trigger']

        if "triggers" in pipe:
            pipeline_triggers += pipe["triggers"]
            del pipe["triggers"]

        final_triggers = parse_triggers(
            pipeline_triggers, self.ghub.get_commit_changed_files()
        )

        logger.debug("Pipeline triggers to proceed with")
        logger.debug(final_triggers)
        if len(final_triggers) == 0 and len(pipeline_triggers) > 0:
            return False, []

        # From here on out, the triggers of the main pipeline have been approved
        if "steps" in pipe:
            pipeline_steps = []
            for step in pipe["steps"]:
                logger.debug("Parsing step")
                logger.debug(step)
                modified_step = step.copy()

                if "when" in step:
                    if isinstance(step["when"], dict):
                      step["when"] = [step["when"]]

                    for index, t in enumerate(parse_triggers(
                        step["when"], self.ghub.get_commit_changed_files()
                    )):
                        if index > 0:
                          modified_step['name'] = f"{ modified_step['name'] }-{ index }"

                        modified_step["when"] = t
                        pipeline_steps.append(modified_step)
                else:
                    pipeline_steps.append(step)

            if len(pipeline_steps) > 0:
                pipe["steps"] = pipeline_steps
            else:
                return False, []

        pipelines = []
        pipeline_name = pipe['name']
        for index, t in enumerate(final_triggers):
            pipe["trigger"] = t
            if index > 0:
              pipe['name'] = f"{ pipeline_name }-{ index }"

            pipelines.append(pipe)

        return True, pipelines


def __merge_pipeline(base, target):
    merged_pipeline = base.copy()

    for k, v in target.items():
        if k in merged_pipeline:
            if isinstance(v, str):
                merged_pipeline[k] = v
            elif isinstance(v, list):
                merged_pipeline[k] = merged_pipeline[k] + v
            elif isinstance(v, dict):
                merged_pipeline[k] = __merge_dict(merged_pipeline[k], v, __merge_dict)
        else:
            merged_pipeline[k] = v

    return merged_pipeline


def __merge_dict(a, b, func):
    final = a.copy()
    for k, v in b.items():
        if k in final:
            if isinstance(v, dict):
                final[k] = func(final[k], v, func)
            else:
                final[k] = v

    return final
