#!/bin/python3

from flask import Flask, request, jsonify
import logging, os, yaml, requests, fnmatch, re, base64
app = Flask(__name__)

headers = {}

def replacements(path, text):
  text.replace('<current_path>', '/'.join(path.split('/')[:-1]))

  return text

def get_included_pipeline(repo, commit, path):
  app.logger.debug(f"Including: { repo }/contents/{ path }?ref={ commit }")
  resp = requests.get(f"https://api.github.com/repos/{ repo }/contents/{ path }?ref={ commit }", headers=headers).json()
  
  if 'content' not in resp:
    app.logger.info(f"Couldn't load pipeline { path }")
    return ""
  else:
    pipeline_text = replacements(path, base64.b64decode(resp['content']).decode('utf-8'))
    return yaml.safe_load(pipeline_text)

@app.route('/healthz', methods=['GET'])
def handle_health():
  return jsonify({})

def parse_pipeline(repo, pipe, commit, commit_changed_files):
  app.logger.debug('Parsing pipeline:')
  app.logger.debug(pipe)
  skip_pipeline = True
  add_pipelines = []

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

  if not skip_pipeline:
    if 'include_pipeline' in pipe:
      included = get_included_pipeline(repo, commit, pipe['include_pipeline'])
      if 'environment' in pipe:
        if 'environment' in included:
          orig_env = included['environment']
          for k,v in pipe['environment'].items():
            orig_env[k] = v
        else:
          included['environment'] = pipe['environment']

      if included != '':
        add_pipelines.append(yaml.dump(included))
      
      pipe = False
    elif 'steps' in pipe:
      pipeline_steps = []
      for step in pipe['steps']:
        skip_step = False

        if 'when' in step and 'paths' in step['when']:
          skip_step = not compare_list_with_patterns(commit_changed_files, step['when']['paths'])
        
        if not skip_step:
          pipeline_steps.append(step)

      pipe['steps'] = pipeline_steps
  else:
    pipe = False

  return add_pipelines, pipe

@app.route('/', methods=['POST'])
def handle():
  body = request.get_json(force=True)
  m = re.search('https?://.+?/(.+?/.+?)/commit/(.+)', body['build']['link'])
  repo = m.group(1)
  commit = m.group(2)

  rep = requests.get(f"https://api.github.com/repos/{ repo }/compare/{ commit }~1...{ commit }", headers=headers)
  content = rep.json()

  commit_changed_files = [ f['filename'] for f in content['files'] ]

  return_pipelines = []
  pipelines = body['config']['data'].split('---')
  app.logger.debug('PIPELINES:')
  app.logger.debug(pipelines)
  app.logger.debug('END')

  while len(pipelines) > 0:
    pipe = yaml.safe_load(pipelines.pop(0))

    if not pipe:
      app.logger.debug('skip pipeline processing')
      continue

    add_pipelines, final_pipeline = parse_pipeline(repo, pipe, commit, commit_changed_files)
    if final_pipeline:
      return_pipelines.append(yaml.safe_dump(final_pipeline))

    pipelines += add_pipelines
  app.logger.debug('\n---\n'.join(return_pipelines))
  return jsonify({ 'data': '\n---\n'.join(return_pipelines) })


def get_config():
  with open(os.environ['CONFIG_PATH'], 'r') as f:
    conf = yaml.safe_load(f.read())
  
  with open(conf['token_path'], 'r') as f:
    conf['token'] = f.read().strip()

  return conf

def compare_list_with_patterns(paths, patterns) -> bool: # if true, an include match was found, if false, an exclude match was found or no match was found
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

  app.logger.setLevel(logging.getLevelName(os.environ['LOG_LEVEL']))

  if 'TLS_CERT_PATH' in os.environ and 'TLS_KEY_PATH' in os.environ:
    app.run(host='0.0.0.0', port=3000, ssl_context=(os.environ['TLS_CERT_PATH'], os.environ['TLS_KEY_PATH']))
  else:
    app.run(host='0.0.0.0', port=3000)
