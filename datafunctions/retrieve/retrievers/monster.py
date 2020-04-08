#!/usr/bin/env python

import os
import sys
import logging
import time
import psycopg2
import random
import requests
import datetime
import html2text
import re

from decouple import config
from typing import Optional, List

from urllib.parse import urlencode
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located, element_to_be_clickable
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import WebDriverException

from datafunctions.retrieve.retrievefunctions import DataRetriever
from datafunctions.utils import titlecase

# logging.basicConfig(stream=sys.stdout, level=logging.INFO)
MONSTER_LOG = logging.getLogger(__name__)

curpath = os.path.dirname(os.path.abspath(__file__))
PHANTOMJSPATH = os.path.join(curpath, '../webdrivers/phantomjs-2.1.1-linux-x86_64/bin/phantomjs')


class MonsterScraper(DataRetriever):
	default_title_list = ['Data Scientist', 'UX Designer', 'Designer', 'Data Analyst', 'Web Engineer', 'Software Engineer', 'UI Engineer', 'Backend Engineer', 'Machine Learning Engineer', 'Frontend Engineer', 'Support Engineer', 'Full-stack Engineer', 'QA Engineer', 'Web Developer', 'Software Developer', 'UI Developer', 'Backend Developer', 'Machine Learning Developer', 'Frontend Developer', 'Support Developer', 'Full-stack Developer', 'QA Developer', 'Developer']
	search_base_url = 'https://www.monster.com/jobs/search/'
	details_base_url = 'https://job-openings.monster.com/v2/job/pure-json-view'

	def __init__(self, max_wait=5):
		self.driver = None
		self.html_converter = html2text.HTML2Text()
		# self.html_converter.ignore_links = True
		# self.html_converter.ignore_images = True
		# self.html_converter.ignore_emphasis = True
		# self.html_converter.ignore_anchors = True
		self.html_converter.body_width = 0
		self.get_info_delay = 2  # Number of seconds to wait between requests to get info
		self.max_wait = max_wait
		self.wait = None

	def establish_driver(self):
		"""
		Establishes the webdriver.
			If a webdriver already exists, closes that one first.
		"""

		MONSTER_LOG.info('Establishing webdriver...')
		self.deestablish_driver()

		try:
			MONSTER_LOG.info('Creating webdriver...')
			driver = webdriver.PhantomJS(
				executable_path=PHANTOMJSPATH,
				service_log_path=os.path.devnull,
			)
			driver.set_window_size('1920', '1080')
			MONSTER_LOG.info(f'webdriver created: {driver}')
			self.driver = driver
			self.wait = WebDriverWait(self.driver, self.max_wait)
		except Exception as e:
			MONSTER_LOG.warn(f'Exception {type(e)} while creating new driver: {e}')
			MONSTER_LOG.warn(e, exc_info=True)
			self.driver = None

		return self.driver

	def deestablish_driver(self):
		"""
		Quits and deletes the driver.
		"""

		MONSTER_LOG.info('Deestablishing old driver...')
		try:
			MONSTER_LOG.info(f'Current driver: {self.driver}')
			if self.driver is not None:
				MONSTER_LOG.info('Closing extant webdriver...')
				self.driver.quit()
		except WebDriverException as e:
			MONSTER_LOG.info(f'Extant driver already closed: {e}')
		except AttributeError as e:
			MONSTER_LOG.info(f'No extand driver found: {e}')
		except Exception as e:
			MONSTER_LOG.warn(f'Exception {type(e)} while closing extant driver: {e}')
			MONSTER_LOG.warn(e, exc_info=True)

		del self.driver
		del self.wait
		self.driver = None
		self.wait = None

	def build_search_url(self, job_title='', job_location='', time=1):
		params = {
			'where': job_location,
			'q': job_title,
			'tm': time,
		}
		MONSTER_LOG.info(f'Building search url with base url {self.search_base_url} and params {params}')
		query = urlencode(params)
		search_url = f'{self.search_base_url}?{query}'
		MONSTER_LOG.info(f'Built search url: {search_url}')
		return (search_url)

	def build_details_url(self, jobid):
		params = {
			'jobid': jobid,
		}
		MONSTER_LOG.info(f'Building details url with base url {self.details_base_url} and params {params}')
		query = urlencode(params)
		details_url = f'{self.details_base_url}?{query}'
		MONSTER_LOG.info(f'Built url: {details_url}')
		return (details_url)

	def add_to_db(self, db_conn, result):
		MONSTER_LOG.info('Adding result to database...')
		job_exists_query = """
			WITH listings AS (
				SELECT id
				FROM job_listings
				WHERE title = %(title)s
			), descriptions AS (
				SELECT job_id
				FROM job_descriptions
				WHERE description = %(description)s
			)
			SELECT listings.id
			FROM listings
			INNER JOIN descriptions
			ON listings.id = descriptions.job_id
			LIMIT 1;
		"""

		job_exists_query_2 = """
			WITH listings AS (
				SELECT id
				FROM job_listings
				WHERE title = %(title)s
			), c AS (
				SELECT id
				FROM companies
				WHERE name = %(name)s
			)
			SELECT listings.id
			FROM listings
			INNER JOIN job_companies
			ON job_companies.job_id = listings.id
			INNER JOIN c
			ON job_companies.company_id = c.id
			LIMIT 1
		"""

		job_listings_query = """
			INSERT INTO job_listings(title, post_date_utc)
			VALUES (%(title)s, to_timestamp(%(post_date_utc)s))
			RETURNING id;
		"""

		job_descriptions_query = """
			INSERT INTO job_descriptions(job_id, description)
			VALUES (%(job_id)s, %(description)s);
		"""

		job_links_query = """
			INSERT INTO job_links(job_id, external_url)
			VALUES (%(job_id)s, %(external_url)s);
		"""

		job_link_exists_query = """
			SELECT job_id
			FROM job_links
			WHERE external_url = %(external_url)s
			LIMIT 1;
		"""

		company_exists_query = """
			SELECT id
			FROM companies
			WHERE name = %(name)s
			LIMIT 1;
		"""

		companies_query = """
			INSERT INTO companies(name, description, logo_url)
			VALUES (%(name)s, %(description)s, %(logo_url)s)
			RETURNING id;
		"""

		company_populated_query = """
			SELECT id
			FROM companies
			WHERE name = %(name)s
				AND description IS NOT NULL
			LIMIT 1;
		"""

		companies_update_query = """
			UPDATE companies
			SET logo_url = %(logo_url)s,
				description = %(description)s
			WHERE id = %(company_id)s
			RETURNING id;
		"""

		job_companies_query = """
			INSERT INTO job_companies(job_id, company_id)
			VALUES (%(job_id)s, %(company_id)s);
		"""

		location_exists_query = """
			SELECT id
			FROM locations
			WHERE city = %(city)s
				AND state_province = %(state_province)s
			LIMIT 1;
		"""

		locations_query = """
			INSERT INTO locations(city, state_province, country)
			VALUES (%(city)s, %(state_province)s, %(country)s)
			RETURNING id;
		"""

		job_locations_query = """
			INSERT INTO job_locations(job_id, location_id)
			VALUES (%(job_id)s, %(location_id)s);
		"""

		try:
			MONSTER_LOG.info('Setting isolation level to READ COMMITTED')
			db_conn.set_isolation_level(1)

			MONSTER_LOG.info('Starting transactions...')
			curr = db_conn.cursor()

			# Get the company id if it exists
			curr.execute(
				company_exists_query,
				{
					'name': result['company_name'],
				}
			)
			qr = curr.fetchone()
			if qr is not None:
				MONSTER_LOG.info(f'Company {result["company_name"]} already exists in DB.')
				company_id = qr[0]
			else:
				# Otherwise, insert the company and get the id
				MONSTER_LOG.info(f'Company {result["company_name"]} not yet in DB, adding...')
				curr.execute(
					companies_query,
					{
						'name': result['company_name'],
						'description': result['company_description'],
						'logo_url': result['company_logo_url'],
					}
				)
				company_id = curr.fetchone()[0]

			# Get the company id if it is not fully populated
			curr.execute(
				company_populated_query,
				{
					'name': result['company_name'],
				}
			)
			qr = curr.fetchone()
			if qr is not None:
				MONSTER_LOG.info(f'Company {result["company_name"]} fully-populated in DB.')
				company_id = qr[0]
			else:
				# Otherwise, insert the company and get the id
				MONSTER_LOG.info(f'Company {result["company_name"]} not complete in DB, populating...')
				curr.execute(
					companies_update_query,
					{
						'company_id': company_id,
						'description': result['company_description'],
						'logo_url': result['company_logo_url'],
					}
				)
				company_id = curr.fetchone()[0]

			# Get the location id if it exists
			curr.execute(
				location_exists_query,
				{
					'city': result['city'],
					'state_province': result['state_province'],
				}
			)
			qr = curr.fetchone()
			if qr is not None:
				MONSTER_LOG.info(f'Location {result["city"]}, {result["state_province"]} already exists in DB.')
				location_id = qr[0]
			else:
				# Otherwise, insert the location and get the id
				MONSTER_LOG.info(f'Location {result["city"]}, {result["state_province"]} not yet in DB, adding...')
				curr.execute(
					locations_query,
					{
						'city': result['city'],
						'state_province': result['state_province'],
						'country': result['country'],
					}
				)
				location_id = curr.fetchone()[0]

			# Get the job listing id if it exists
			curr.execute(
				job_exists_query,
				{
					'title': result['title'],
					'description': result['description'],
				}
			)
			qr = curr.fetchone()
			# Get the job listing id if it exists, by company
			curr.execute(
				job_exists_query_2,
				{
					'title': result['title'],
					'name': result['company_name'],
				}
			)
			job_id = None
			qr2 = curr.fetchone()

			# Get the job listing id if it exists, by link url
			curr.execute(
				job_link_exists_query,
				{
					'external_url': result['inner_link'],
				}
			)
			qr3 = curr.fetchone()
			if qr is not None:
				MONSTER_LOG.info(f'Job listing for {result["title"]} already exists in DB.')
				job_id = qr[0]
			if qr2 is not None:
				MONSTER_LOG.info(f'Job listing for {result["title"]} at company {result["company_name"]} already exists in DB.')
				job_id = qr2[0]
			if qr3 is not None:
				MONSTER_LOG.info(f'A job listing with url {result["inner_link"]} already exists in DB.')
				job_id = qr3[0]
			if job_id is None:
				# Otherwise, insert the job listing and get the id
				MONSTER_LOG.info(f'Job listing for {result["title"]} not yet in DB, adding...')
				curr.execute(
					job_listings_query,
					{
						'title': result['title'],
						'post_date_utc': result['timestamp'],
					}
				)
				job_id = curr.fetchone()[0]

				# Also add the relation to companies
				MONSTER_LOG.info(f'Adding relation job_id {job_id} to company_id {company_id}...')
				curr.execute(
					job_companies_query,
					{
						'job_id': job_id,
						'company_id': company_id,
					}
				)

				# Also add the relation to locations
				MONSTER_LOG.info(f'Adding relation job_id {job_id} to location_id {location_id}...')
				curr.execute(
					job_locations_query,
					{
						'job_id': job_id,
						'location_id': location_id,
					}
				)

				# And the description
				MONSTER_LOG.info('Saving description...')
				curr.execute(
					job_descriptions_query,
					{
						'job_id': job_id,
						'description': result['description'],
					}
				)

				# And the link to the job
				MONSTER_LOG.info('Saving link...')
				curr.execute(
					job_links_query,
					{
						'job_id': job_id,
						'external_url': result['inner_link'],
					}
				)

			curr.close()
			MONSTER_LOG.info('Committing changes...')
			db_conn.commit()
			MONSTER_LOG.info('Added result to database.')

		except Exception as e:
			MONSTER_LOG.warn(f'Exception {type(e)} while executing transaction: {e}')
			MONSTER_LOG.warn(e, exc_info=True)

			MONSTER_LOG.info('Attempting to close cursor...')
			try:
				curr.close()
			except Exception as e2:
				MONSTER_LOG.warn(f'Exception {type(e2)} while closing cursor, skipping: {e2}')

			MONSTER_LOG.info('Attempting to rollback transaction...')
			try:
				db_conn.rollback()
			except Exception as e2:
				MONSTER_LOG.warn(f'Exception {type(e2)} while rolling back, skipping: {e2}')

	def get_jobs(self, db_conn, job_title='', job_location=''):
		self.establish_driver()
		url = self.build_search_url(job_title=job_title, job_location=job_location)
		max_tries = 3
		tries = 0
		wait_time = 5
		while tries < max_tries:
			MONSTER_LOG.info(f'Getting url: {url} (try {tries + 1} of {max_tries})')
			try:
				self.driver.get(url)
				break
			except Exception as e:
				tries += 1
				MONSTER_LOG.warn(f'Exception {type(e)} while getting search page: {e}')
				MONSTER_LOG.warn(e, exc_info=True)
				MONSTER_LOG.info('Reestablishing driver...')
				self.establish_driver()
				time.sleep(wait_time)

		content_xpath = '//*[@id="SearchResults"]/*[contains(@class, "card-content") and not(contains(@class, "apas-ad"))]'
		MONSTER_LOG.info(f'Waiting for element: {content_xpath}')
		self.wait.until(
			presence_of_element_located(
				(By.XPATH, content_xpath)
			)
		)

		load_button_xpath = '//*[@id="loadMoreJobs"]'

		page_count = 1
		tries = 0
		max_tries = 3
		wait_time = 0
		while tries < max_tries:
			MONSTER_LOG.info(f'Attempting to load more jobs (try {tries + 1} of {max_tries}) (page {page_count})')
			try:
				load_button = self.wait.until(
					presence_of_element_located(
						(By.XPATH, load_button_xpath)
					)
				)

				self.driver.execute_script("arguments[0].click();", load_button)

				tries = 0
				page_count += 1

				MONSTER_LOG.info(f'Loaded jobs, waiting {wait_time} seconds...')
				time.sleep(wait_time)
			except Exception as e:
				tries += 1
				MONSTER_LOG.warn(f'Exception {type(e)} while loading more jobs: {e}')
				MONSTER_LOG.warn(e, exc_info=True)
				time.sleep(wait_time)

		MONSTER_LOG.info(f'Getting elements: {content_xpath}')
		result_elements = self.driver.find_elements_by_xpath(
			content_xpath
		)
		result_elements_count = len(result_elements)
		MONSTER_LOG.info(f'Got {result_elements_count} elements.')

		MONSTER_LOG.info(f'Getting jobids, start time: {datetime.datetime.now()}')
		result_element_jobids = []
		for index, result_element in enumerate(result_elements):
			try:
				MONSTER_LOG.info(f'Getting jobid for element {index + 1} of {result_elements_count}')
				result_element_jobids.append(result_element.get_attribute('data-jobid'))
				result_elements[index] = None  # More RAM reduction
			except Exception as e:
				MONSTER_LOG.warn(f'Exception {type(e)} while getting jobid for element {index + 1}: {e}')
				MONSTER_LOG.warn(e, exc_info=True)
		MONSTER_LOG.info(f'Done getting jobids, end time: {datetime.datetime.now()}')

		del result_elements  # Reduce RAM usage
		self.deestablish_driver()

		MONSTER_LOG.info(f'Getting job info, start time: {datetime.datetime.now()}')
		for index, result_element_jobid in enumerate(result_element_jobids):
			try:
				MONSTER_LOG.info(f'Waiting {self.get_info_delay} seconds...')
				time.sleep(self.get_info_delay)
				MONSTER_LOG.info(f'Getting job info for element {index + 1} of {result_elements_count}')
				result = self.get_details_json(result_element_jobid)
				self.add_to_db(db_conn, result)
			except Exception as e:
				MONSTER_LOG.warn(f'Exception {type(e)} while getting info for element {index + 1}: {e}')
				MONSTER_LOG.warn(e, exc_info=True)
		MONSTER_LOG.info(f'Done getting job info, end time: {datetime.datetime.now()}.')

	def get_details_json(self, result_element_jobid, max_tries=5):
		MONSTER_LOG.info(f'Getting info for jobid: {result_element_jobid}')
		for tries in range(max_tries):
			try:
				details_url = self.build_details_url(result_element_jobid)
				MONSTER_LOG.info(f'Getting url: {details_url}')
				data = requests.get(details_url).json()
				break
			except Exception as e:
				MONSTER_LOG.warn(f'Exception getting info for jobid: {result_element_jobid}: {e}')
				MONSTER_LOG.warn(e, exc_info=True)
				wait_time = 3
				MONSTER_LOG.info(f'Waiting {wait_time} seconds...')
				time.sleep(wait_time)
		else:
			raise Exception('Unable to get info after 5 tries.')

		MONSTER_LOG.info('Converting description to text...')
		description_text = re.sub(
			r'\n\n(\s+\n)+',
			'\n\n',
			re.sub(
				r'\n+',
				'\n\n',
				self.html_converter.handle(
					data['jobDescription'].replace('\n', '<br />')
				)
			)
		)

		MONSTER_LOG.info('Converting company description to text...')
		company_description = re.sub(
			r'\n\n(\s+\n)+',
			'\n\n',
			re.sub(
				r'\n+',
				'\n\n',
				self.html_converter.handle(
					data['companyInfo'].get('description', '').replace('\n', '<br />')
				)
			)
		)

		MONSTER_LOG.info(f'Getting info...')
		title = data['companyInfo']['companyHeader'].replace(f' at {data["companyInfo"].get("name", "")}', '').strip()
		if data['isCustomApplyOnlineJob']:
			link = data['customApplyUrl']
		else:
			link = data['submitButtonUrl']
		result = {
			'description': description_text.strip(),
			'company_name': data['companyInfo'].get('name', ''),
			'company_logo_url': data['companyInfo'].get('logo', {}).get('src', ''),
			'company_description': company_description.strip(),
			'title': title,
			'inner_link': link,
			'country': data.get('jobLocationCountry', ''),
			'state_province': titlecase(data.get('jobLocationRegion', '')),
			'city': titlecase(data.get('jobLocationCity', '')),
			'timestamp': int(time.time()),
		}
		MONSTER_LOG.info('Got details.')
		MONSTER_LOG.info(f'Result: {result}')

		return (result)

	def get_and_store_data(
			self,
			db_connection,
			title_list: Optional[List[str]] = None,
			**kwargs
	) -> None:
		if title_list is None:
			title_list = self.default_title_list
			random.shuffle(title_list)

		for job in title_list:
			try:
				self.get_jobs(db_connection, job_title=job)
			except Exception as e:
				MONSTER_LOG.warning(f'Failure while getting jobs for title {job}: {e}')
				MONSTER_LOG.warn(e, exc_info=True)

	def __enter__(self):
		return (self)

	def __exit__(self, exc_type, exc_value, tb):
		MONSTER_LOG.info(f'__exit__ called, cleaning up...')
		MONSTER_LOG.info(f'exc_type: {exc_type}')
		self.deestablish_driver()


