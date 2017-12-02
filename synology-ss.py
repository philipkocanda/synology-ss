#!/usr/bin/python

import os, sys, json, urllib, urllib2

AUTH_URL = "%s/webapi/auth.cgi?api=SYNO.API.Auth&method=Login&version=3&account=%s&passwd=%s&session=SurveillanceStation"
API_URL = "%s/webapi/entry.cgi?%s&_sid=%s"

# Common API Errors
API_ERRORS = {
  # Older version (from Surveillance Station Web API V2.0 PDF):
  100: 'Unknown error',
  101: 'Invalid parameters',
  102: 'API does not exist',
  103: 'Method does not exist',
  104: 'This API version is not supported',
  105: 'Authentication failure',
  106: 'Session time out',
  107: 'Multiple login detected',
  # Newer version (determined by trial and error):
  115: 'Authentication failure',
  117: 'Insufficient user privilege',
}

debug = False
session_id = None
config = {}

class SynologyAuthenticationException(Exception):
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return repr(self.value)

class SynologyApiException(Exception):
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return repr(self.value)

def authenticate():
  global session_id

  # Memoize the result
  if session_id:
    return session_id

  request = urllib2.Request(AUTH_URL % (config['url'], config['username'], config['password']))
  raw_response = urllib2.urlopen(request).read()
  response = json.loads(raw_response)

  if response['success'] != True:
    raise SynologyAuthenticationException('Authentication failure. Response: %s' % raw_response)

  session_id = response['data']['sid']
  return session_id

def api_get(query):
  return api_call(query)

def api_post(data):
  return api_call({}, 'POST', data)

def api_call(query = {}, method = 'GET', data = None):
  request_url = API_URL % (config['url'], urllib.urlencode(query), authenticate())

  if method == 'POST':
    data['_sid'] = authenticate()
    encoded_data = urllib.urlencode(data)
  else:
    encoded_data = None

  if debug:
    print "%s %s" % (method, request_url)
    print encoded_data

  headers = {}
  headers["Content-Type"] = "application/x-www-form-urlencoded"

  request = urllib2.Request(request_url, encoded_data)
  request.get_method = lambda: method
  raw_response = urllib2.urlopen(request).read()

  if debug:
    print "Response:"
    print raw_response

  response = json.loads(raw_response)

  if response['success'] != True:
    error_code = int(response['error']['code'])
    if error_code in API_ERRORS:
      friendly_error = '%s (Error code %s)' % (API_ERRORS[error_code], error_code)
    else:
      friendly_error = 'Unknown error code: %s' % error_code

    raise SynologyApiException('API exception: %s. Response: %s' % (friendly_error, raw_response))

  return response

def set_home_mode(value):
  api_post({
    'api': 'SYNO.SurveillanceStation.HomeMode',
    'version': 1,
    'method': 'Switch',
    'on': ('true' if value else 'false'),
  })

  print "Home mode has been turned %s." % ('on' if value else 'off')

def get_home_mode():
  response = api_get({
    'api': 'SYNO.SurveillanceStation.HomeMode',
    'version': 1,
    'method': 'GetInfo',
  })

  print "Home mode is %s." % ('on' if response['data']['on'] == True else 'off')

def list_cameras():
  response = api_get({
    'api': 'SYNO.SurveillanceStation.Camera',
    'version': 3,
    'method': 'List',
  })

  cameras = response['data']['cameras']

  row_format = "{:<5}{:<15}{:<15}{:<15}{:<15}"
  print row_format.format(
    'ID',
    'Camera',
    'IP',
    'State',
    'Resolution',
  )

  print row_format.format(
    '---',
    '------------',
    '------------',
    '------------',
    '------------',
  )

  for camera in cameras:
    print row_format.format(
      camera['id'],
      camera['detailInfo']['camName'],
      camera['detailInfo']['camIP'],
      ('enabled' if camera['enabled'] else 'disabled'),
      camera['resolution'],
    )

def set_camera_state(id, state):
  response = api_post({
    'api': 'SYNO.SurveillanceStation.Camera',
    'version': 7,
    'cameraIds': id,
    'method': 'Enable' if state else 'Disable'
  })

  print "Camera %s has been %s." % (id, 'enabled' if state else 'disabled')

def load_config():
  global config

  path = os.path.realpath(
      os.path.join(os.getcwd(), os.path.dirname(__file__))
  )

  config_file = '%s/config.json' % path

  file = open(config_file,'r')
  config = json.loads(file.read())
  file.close()

def is_truthy(var):
  return var == 'true' or var == 'on' or var == 'enabled' or var == 'enable' or var == 'yes'

def main(argv):
  global debug

  load_config()

  if 'username' not in config or 'password' not in config or 'url' not in config:
    print "Configuration must contain 'username', 'password' and 'url'."
    sys.exit(1)

  if len(argv) == 0:
    print 'Usage:'
    print 'synology-ss.py home_mode'
    print 'synology-ss.py home_mode <on|off>'
    print 'synology-ss.py cameras'
    print 'synology-ss.py camera <id> <on|off>'
    sys.exit(1)

  arg = argv[0]
  arg_1 = (argv[1] if len(argv) > 1 else None)
  arg_2 = (argv[2] if len(argv) > 2 else None)

  if '--debug' in argv:
    argv.remove('--debug')
    debug = True
    print "Debug mode enabled"

  if arg == 'home_mode' and arg_1:
      set_home_mode(is_truthy(arg_1))
  elif arg == 'home_mode' and len(argv) == 1:
    get_home_mode()
  elif arg == 'cameras' and len(argv) == 1:
    list_cameras()
  elif arg == 'camera' and arg_1 and arg_2:
    set_camera_state(arg_1, is_truthy(arg_2))
  else:
    print "Unknown command: %s" % argv
    sys.exit(1)

if __name__ == "__main__":
  main(sys.argv[1:])
