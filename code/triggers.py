import fnmatch
import logging

logger = logging.getLogger("monorepo")

# base_triggers = ["branch", "event"]

def parse_triggers(triggers, commit_changed_files=[]):
    ret_triggers = []
    for trigger_group in triggers:
        group = trigger_group.copy()

        if "paths" in trigger_group:
            if _parse_trigger(trigger_group['paths'], commit_changed_files):
                del group["paths"]
                ret_triggers.append(group)
        else:
            ret_triggers.append(group)

        # for name, value in trigger_group.items():
        #     if not isinstance(value, list):
        #       value == [value]

        #     for v in value:
        #       if not fnmatch.fnmatch(build[name], v):
        #         matched = True

    return ret_triggers


def _parse_trigger(trigger, value):
    if isinstance(trigger, str):
        trigger = {"include": [trigger]}
    if isinstance(trigger, list):  # otherwise its {include:[...],exclude:[...]}
        trigger = {"include": trigger}

    if "exclude" in trigger:
        logger.debug("Excludes: " + ",".join(trigger["exclude"]))
        for p in value:
            for pat in trigger["exclude"]:
                if fnmatch.fnmatch(p, pat):
                    logger.debug("excluding due to matching " + p + " with " + pat)
                    return False

    if "include" in trigger:
        logger.debug("Includes: " + ",".join(trigger["include"]))
        for p in value:
            for pat in trigger["include"]:
                if fnmatch.fnmatch(p, pat):
                    logger.debug("matching: " + p + " with " + pat)
                    return True

    return False
