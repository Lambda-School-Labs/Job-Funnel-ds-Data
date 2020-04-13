
import os
import subprocess
import sys
import logging
import time

from flask import Flask, jsonify, request
from flask.logging import default_handler
from datafunctions.log.log import startLog, getLogFile, tailLogFile


SCRAPER_NAME = './run_scrapers.py'
SCRAPER_NAME_PS = SCRAPER_NAME[2:]
MODEL_NAME = './run_models.py'
MODEL_NAME_PS = MODEL_NAME[2:]
startLog(getLogFile(__file__))
APP_LOG = logging.getLogger(__name__)

APP_LOG.info('Creating app...')
application = Flask(__name__)
werkzeug_logger = logging.getLogger('werkzeug')
for handler in APP_LOG.handlers:
	werkzeug_logger.addHandler(handler)
	application.logger.addHandler(handler)


@application.route('/')
def index():
	return '''
		<html><head></head><body>
			Health check: <a href="/health">/health</a>
			<br>
			Start scrapers: <a href="/start">/start</a>
			<br>
			Kill scrapers: <a href="/kill">/kill</a>
			<br>
			Start models: <a href="/start-models">/start-models</a>
			<br>
			Kill models: <a href="/kill-models">/kill-models</a>
			<br>
			Application logs: <a href="/logs?file=application.py&amp;lines=50">/logs?file=application.py</a>
			<br>
			Scraper logs: <a href="/logs?file=run_scrapers.py&amp;lines=100">/logs?file=run_scrapers.py</a>
			<br>
			Model logs: <a href="/logs?file=run_models.py&amp;lines=100">/logs?file=run_models.py</a>
		</body></html>
	'''


@application.route('/logs', methods=['GET'])
def logs():
	"""
	Gets the last n lines of a given log
	"""
	APP_LOG.info(f'/logs called with args {request.args}')
	logfile = request.args.get('file', None)
	lines = request.args.get('lines', 1000)

	if logfile is None:
		return('''
		<pre>
			Parameters:
				file: The file to get logs for
					Required
					Usually one of either application.py or run_scrapers.py
				lines: Number of lines to get
					Defaults to 1000
		</pre>
		''')

	try:
		res = tailLogFile(logfile, n_lines=lines)
		return (f'<pre>{res}</pre>')
	except Exception as e:
		return(f'Exception {type(e)} getting logs: {e}')


@application.route('/health', methods=['GET'])
def health():
	"""
	Prints various health info about the machine.
	"""

	APP_LOG.info('/health called')
	outputs = {}
	outputs['scrapers running'] = check_running(SCRAPER_NAME)
	outputs['models running'] = check_running(MODEL_NAME)
	outputs['free'] = os.popen('free -h').read()
	outputs['dstat'] = os.popen('dstat -cdlimnsty 1 0').read()
	outputs['top'] = os.popen('top -bn1').read()
	outputs['ps'] = os.popen('ps -Afly --forest').read()
	APP_LOG.info(f'Health results: {outputs}')

	r = ''
	for key, val in outputs.items():
		r += f'''
			<hr />
			<h4>{key}</h4>
			<pre style="white-space: pre-wrap; overflow-wrap: break-word;">{val}</pre>
		'''

	return r


@application.route('/kill', methods=['GET', 'POST'])
def kill():
	"""
	Kills the web scrapers.
	"""

	initial_state = check_running(SCRAPER_NAME)
	running = initial_state
	try:
		APP_LOG.info('/kill called')
		tries = 0
		max_tries = 5
		while running and tries < max_tries:
			APP_LOG.info(f'Scraper running, attempting to kill it (try {tries + 1} of {max_tries})')
			r = os.system(
				f'kill $(ps -Af | grep {SCRAPER_NAME_PS} | grep -v grep | grep -oP "^[a-zA-Z\s]+[0-9]+" | grep -oP "[0-9]+")'
			)
			APP_LOG.info(f'Kill call exited with code: {r}')
			tries += 1
			running = check_running(SCRAPER_NAME)
			if running:
				wait_time = 2
				APP_LOG.info(f'Waiting {wait_time} seconds...')
				time.sleep(wait_time)
	except Exception as e:
		APP_LOG.warn(f'Exception while killing scrapers: {e}')
		APP_LOG.warn(e, exc_info=True)

	return f'''
		<html><body>
			<h4>initially running</h4>
			<pre>{initial_state}</pre>
			<hr />
			<h4>scrapers running</h4>
			<pre>{running}</pre>
		</html></body>
	'''


@application.route('/start', methods=['GET', 'POST'])
def start():
	"""
	Starts the web scrapers.
	"""

	tries = 0
	result = {
		'running': False,
		'tries': 0,
		'message': 'Unknown failure.'
	}
	try:
		APP_LOG.info('/start called')
		max_tries = 5
		while not check_running(SCRAPER_NAME) and tries < max_tries:
			APP_LOG.info(f'Scraper not running, attempting to start it (try {tries + 1} of {max_tries})')
			start_and_disown(SCRAPER_NAME)
			wait_time = 0
			APP_LOG.info(f'Waiting {wait_time} seconds...')
			time.sleep(wait_time)
			tries += 1

		if check_running(SCRAPER_NAME):
			APP_LOG.info(f'Scraper running.')
			if tries == 0:
				result = {
					'running': True,
					'tries': tries,
					'message': f'{SCRAPER_NAME} already running.'
				}
			else:
				result = {
					'running': True,
					'tries': tries,
					'message': f'{SCRAPER_NAME} started after {tries} tries.'
				}
		else:
			result = {
				'running': False,
				'tries': tries,
				'message': f'Failed to start {SCRAPER_NAME} after {tries} tries.'
			}
			# APP_LOG.info(f'run_scrapers stdout: {p.stdout.read()}')
			# APP_LOG.info(f'run_scrapers stderr: {p.stderr.read()}')

		APP_LOG.info(f'result: {result}')

	except Exception as e:
		result = {
			'running': False,
			'tries': tries,
			'message': f'Aborting after {type(e)} exception on try {tries}: {e}'
		}
		APP_LOG.warn(f'result: {result}')
		APP_LOG.warn(e, exc_info=True)

	return jsonify(result)


@application.route('/kill-models', methods=['GET', 'POST'])
def kill_models():
	"""
	Kills the topic models.
	"""

	initial_state = check_running(MODEL_NAME)
	running = initial_state
	try:
		APP_LOG.info('/kill-models called')
		tries = 0
		max_tries = 5
		while running and tries < max_tries:
			APP_LOG.info(f'Models running, attempting to kill it (try {tries + 1} of {max_tries})')
			r = os.system(
				f'kill $(ps -Af | grep {MODEL_NAME_PS} | grep -v grep | grep -oP "^[a-zA-Z\s]+[0-9]+" | grep -oP "[0-9]+")'
			)
			APP_LOG.info(f'Kill call exited with code: {r}')
			tries += 1
			running = check_running(MODEL_NAME)
			if running:
				wait_time = 2
				APP_LOG.info(f'Waiting {wait_time} seconds...')
				time.sleep(wait_time)
	except Exception as e:
		APP_LOG.warn(f'Exception while killing models: {e}')
		APP_LOG.warn(e, exc_info=True)

	return f'''
		<html><body>
			<h4>initially running</h4>
			<pre>{initial_state}</pre>
			<hr />
			<h4>models running</h4>
			<pre>{running}</pre>
		</html></body>
	'''


@application.route('/start-models', methods=['GET', 'POST'])
def start_models():
	"""
	Starts the topic models.
	"""

	tries = 0
	result = {
		'running': False,
		'tries': 0,
		'message': 'Unknown failure.'
	}
	try:
		APP_LOG.info('/start-models called')
		max_tries = 5
		while not check_running(MODEL_NAME) and tries < max_tries:
			APP_LOG.info(f'Models not running, attempting to start it (try {tries + 1} of {max_tries})')
			start_and_disown(MODEL_NAME)
			wait_time = 0
			APP_LOG.info(f'Waiting {wait_time} seconds...')
			time.sleep(wait_time)
			tries += 1

		if check_running(MODEL_NAME):
			APP_LOG.info(f'Models running.')
			if tries == 0:
				result = {
					'running': True,
					'tries': tries,
					'message': f'{MODEL_NAME} already running.'
				}
			else:
				result = {
					'running': True,
					'tries': tries,
					'message': f'{MODEL_NAME} started after {tries} tries.'
				}
		else:
			result = {
				'running': False,
				'tries': tries,
				'message': f'Failed to start {MODEL_NAME} after {tries} tries.'
			}

		APP_LOG.info(f'result: {result}')

	except Exception as e:
		result = {
			'running': False,
			'tries': tries,
			'message': f'Aborting after {type(e)} exception on try {tries}: {e}'
		}
		APP_LOG.warn(f'result: {result}')
		APP_LOG.warn(e, exc_info=True)

	return jsonify(result)


def check_running(pname):
	APP_LOG.info(f'check_running called, pname: {pname}')
	result = os.system(f'ps -Af | grep -v grep | grep -v log | grep {pname}')
	APP_LOG.info(f'exit code: {result}')
	return result == 0


def start_and_disown(pname):
	with open(os.devnull, 'r+b', 0) as DEVNULL:
		subprocess.Popen(['nohup', sys.executable, pname],
			stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL, close_fds=True, preexec_fn=os.setpgrp)


if __name__ == '__main__':
	APP_LOG.info('Starting Flask dev server...')
	application.run()