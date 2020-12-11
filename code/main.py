#!/bin/python3

from flask import Flask, request, jsonify
import json, os, yaml, requests, fnmatch, re, base64
app = Flask(__name__)

headers = {}

def get_included_pipeline(repo, commit, includes):
  included_pipelines = []
  for i in includes:
    resp = requests.get(f"https://api.github.com/repos/{ repo }/contents/{ i }?ref={ commit }")
    included_pipelines.append(base64.b64decode(resp.json()['content']).decode('utf-8'))

@app.route('/healthz', methods=['GET'])
def handle_health():
  return jsonify({})

@app.route('/', methods=['POST'])
def handle():
  body = request.get_json(force=True)
  m = re.search('https?://.+?/(.+?/.+?)/commit/(.+)', body['build']['link'])
  repo = m.group(1)
  commit = m.group(2)
  rep = requests.get(f"https://api.github.com/repos/{ repo }/compare/{ commit }~1...{ commit }", headers=headers)
  commit_changed_files = [ f['filename'] for f in rep.json()['files'] ]

  with open('req.txt', 'r') as f:
    content = json.loads(f.read().replace('#', ''))

  pipelines = content['config']['data'].split('---')

  return_pipelines = []
  while len(pipelines) > 0:
    pipe = yaml.safe_load(pipelines[0])
    skip_pipeline = True

    if 'trigger' not in pipe or 'paths' not in pipe['trigger']:
      skip_pipeline = False
    elif 'paths' in pipe['trigger']:
      if isinstance(pipe['trigger']['paths'], list):
        pipe['trigger']['paths'] = { 'include': pipe['trigger']['paths'] }

      app.logger.debug('Pipeline path triggers: ')
      if 'include' in pipe['trigger']['paths']:
        app.logger.debug('Includes: ' + ','.join(pipe['trigger']['paths']['include']))
      if 'exclude' in pipe['trigger']['paths']:
        app.logger.debug('Excludes: ' + ','.join(pipe['trigger']['paths']['exclude']))

      skip_pipeline = not compare_list_with_patterns(commit_changed_files, pipe['trigger']['paths'])
      del pipe['trigger']['paths']

    if not skip_pipeline and 'steps':
      if 'include_pipelines' in pipe:
        for path in pipe['include_pipelines']:
          pipelines.append(get_included_pipeline(repo, commit, path))

      pipeline_steps = []
      for step in pipe['steps']:
        skip_step = False

        if 'when' in step and 'paths' in step['when']:
          skip_step = not compare_list_with_patterns(commit_changed_files, step['when']['paths'])
        
        if not skip_step:
          pipeline_steps.append(step)

      pipe['steps'] = pipeline_steps

      return_pipelines.append(yaml.safe_dump(pipe))

  return jsonify({ 'data': '\n---\n'.join(return_pipelines) })


def get_config():
  with open(os.environ['CONFIG_PATH'], 'r') as f:
    conf = yaml.safe_load(f.read())
  
  with open(conf['token_path'], 'r') as f:
    conf['token'] = f.read().strip()

  return conf

def compare_list_with_patterns(paths, patterns) -> bool: # if true, an include match was found, if false, an exclude match was found, or no match was found
  for p in paths:
    if 'exclude' in patterns:
      for pat in patterns['exclude']:
        if fnmatch.fnmatch(p, pat):
          app.logger.debug('excluding due to matching ' + p + ' with ' + pat)
          return False
      
    if 'include' in patterns:
      for pat in patterns['include']:
        if fnmatch.fnmatch(p, pat):
          app.logger.debug('including due to matching: ' + p + ' with ' + pat)
          return True

  return False

if __name__ == '__main__':
  conf = get_config()

  headers = {
    'Authorization': conf['token']
  }

  with open('./req.txt', 'r') as f:
    body = json.loads(f.read())

  m = re.search('https?://.+?/(.+?/.+?)/commit/(.+)', body['build']['link'])
  repo = m.group(1)
  commit = m.group(2)
  get_included_pipeline(repo, commit, [])
  # app.run(host='0.0.0.0', port=3000)

