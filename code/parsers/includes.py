from models.pipelines import Pipeline

class IncludesParser:
    def __init__(self, backend, req = None):
        self.backend = backend
        self.repo = req["repo"]["slug"]
        self.commit = req["build"]["after"]
        self.is_pipeline_parser = True
        self.is_step_parser = False

    def parse_pipeline(self, pipe: Pipeline) -> list[Pipeline]:
        return_pipelines = [pipe]

        if 'include_pipeline' in pipe.get_raw():
            included = self.backend.get_included_pipeline(pipe.get_raw()['include_pipeline'], self.repo, self.commit)

            if included != "":
                return_pipelines.append(pipe.merge_pipeline(included))

        return return_pipelines