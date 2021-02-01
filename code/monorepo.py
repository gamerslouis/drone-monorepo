import logging

from models.pipelines import Pipeline

logger = logging.getLogger("monorepo")


class Monorepo:
    def __init__(self, backend):
        self.__backend = backend
        self.__pipeline_parsers = []
        self.__step_parsers = []

    def set_parsers(self, parsers):
        self.__pipeline_parsers = []
        self.__step_parsers = []

        for p in parsers:
            if p.is_pipeline_parser:
                self.__pipeline_parsers.append(p)
            
            if p.is_step_parser:
                self.__step_parsers.append(p)


    def get_backend(self):
        return self.__backend

    def parse_pipelines(self, pipelines_to_process):
      return_pipelines = []

      logger.debug('Starting to parse.')
      while len(pipelines_to_process) > 0:
          pipe = pipelines_to_process.pop(0)

          if not pipe:
              logger.debug("skip pipeline processing")
              continue

          add_pipelines = self.parse_pipeline(pipe)

          if len(add_pipelines) > 1:
              pipelines_to_process += add_pipelines
          else:
              return_pipelines += add_pipelines
  
      return return_pipelines


    def parse_pipeline(self, pipe) -> list[Pipeline]:
      ''' Call all registered parsers that receive a pipeline '''

      steps_to_process = pipe.get_steps()
      return_steps = []
      while len(steps_to_process) > 0:
          step = steps_to_process.pop(0)

          for parser in self.__step_parsers:
              add_steps = parser.parse_step(step)
              step = None
              if len(add_steps) == 1:
                  step = add_steps[0]
              elif len(add_steps) > 1:
                  steps_to_process += add_steps
                  break
              elif len(add_steps) == 0:
                  break

          if step != None:
              return_steps.append(step)

      pipe.set_steps(return_steps)

      pipelines_to_process = [pipe]
      return_pipelines = []

      while len(pipelines_to_process) > 0:
          pipe = pipelines_to_process.pop(0)
          logger.debug("Parsing pipeline: ")
          logger.debug(pipe)

          if not pipe:
              logger.debug("skip pipeline processing")
              continue

          for parser in self.__pipeline_parsers:
              logger.debug("Execute parser: " + str(parser.__class__))
              add_pipelines = parser.parse_pipeline(pipe)
              pipe = None

              if len(add_pipelines) == 1:
                  pipe = add_pipelines[0]
              elif len(add_pipelines) > 1:
                  pipelines_to_process += add_pipelines
                  break
              elif len(add_pipelines) == 0:
                  break

          if pipe != None:
              return_pipelines.append(pipe)

      return return_pipelines