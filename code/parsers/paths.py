import fnmatch
import logging
from models.pipelines import Pipeline
from models.steps import Step

logger = logging.getLogger("monorepo")


class PathsChangedParser:
    def __init__(self, backend, req):
        repo = req["repo"]["slug"]
        before = req["build"]["before"]
        after = req["build"]["after"]
        if before == after:
            before = f"{ before }~1"

        self.commit_changed_files = backend.get_commit_changed_files(repo, before, after)

        self.is_pipeline_parser = True
        self.is_step_parser = True

    def parse_pipeline(self, pipe: Pipeline) -> list[Pipeline]:
        trigger = pipe.get_trigger()
        if 'paths' in trigger:
            if not self.__parse_trigger(trigger['paths']):
                return []
              
            del trigger['paths']
            pipe.set_trigger(trigger)
        
        return [pipe]

    def parse_step(self, step: Step) -> list[Step]:
        when = step.get_when()
        if 'paths' in when:
            if not self.__parse_trigger(when['paths']):
                return []
            
            del when['paths']
            step.set_when(when)
        
        return [step]    

    def __parse_trigger(self, trigger):
        if isinstance(trigger, str):
            trigger = {"include": [trigger]}
        if isinstance(trigger, list):  # otherwise its {include:[...],exclude:[...]}
            trigger = {"include": trigger}

        if "exclude" in trigger:
            logger.debug("Excludes: " + ",".join(trigger["exclude"]))
            for p in self.commit_changed_files:
                for pat in trigger["exclude"]:
                    if fnmatch.fnmatch(p, pat):
                        logger.debug("excluding due to matching " + p + " with " + pat)
                        return False

        if "include" in trigger:
            logger.debug("Includes: " + ",".join(trigger["include"]))
            for p in self.commit_changed_files:
                for pat in trigger["include"]:
                    if fnmatch.fnmatch(p, pat):
                        logger.debug("matching: " + p + " with " + pat)
                        return True

        return False
