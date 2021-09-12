# drone-monorepo 
+ This is a forked version of [drone-monorepo](https://github.com/tiagoposse/drone-monorepo) that remove support of paths changed and pipeline inclusion. Since these two function required github token which might have some security issue and not required.

A [Drone Conversion extension](https://docs.drone.io/extensions/conversion/) built to support repositories with multiple applications in it.

It processes .drone.yml files sent to it and runs a series of parsers, described next. There are currently 2 parsers:
- multi-trigger
- run target

## Multiple triggers for pipelines and steps:
  
The current Drone implementation for a pipeline and steps specify 'trigger' and 'when' as dicts where all fields need to evaluated to true in order for the pipeline to run. If you want to run a pipeline for two different triggers, you need two pipelines and the same applies to steps.

This extension provides the ability to use trigger as an array:
```
name: pipe-example
kind: pipeline
trigger:
  - event: custom
  - event: push
```

The parser will return multiple pipelines to the server, each containing a single dict of the list.
```
name: pipe1
kind: pipeline
trigger:
  event: custom
---
name: pipe2
kind: pipeline
trigger:
  event: push
```

## Target pipelines

Allows you to manually specify a pipeline to execute by using a build param called target. This is evaluated against a pipeline name.
Example:
```
drone build create tiagoposse/drone-monorepo -p target=paths
```
