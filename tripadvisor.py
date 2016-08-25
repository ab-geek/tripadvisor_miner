#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import language
import requests
from bs4 import BeautifulSoup
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.packages.urllib3.exceptions import InsecurePlatformWarning
from requests.packages.urllib3.exceptions import SNIMissingWarning

class TripAdvisor:
	hotelTripadvisorId = ""
	hotelName = ""
	hotelEmail = ""
	streetAddress = ""
	country = ""
	city = ""
	state = ""
	longitude = 0.0
	latitude = 0.0
	tripAdvisorRating = 0.0
	reviewCount = 0
	rankingInCity = ""
	hotelTagCloud = []
	officialHotelDescription = ""
	additionalHotelInformation = ""

	amenities ={}
	amenities['highlights'] = []
	amenities['aboutTheProperty'] = []
	amenities['thingsToDo'] = []
	amenities['roomTypes'] = []
	amenities['internet'] = []
	amenities['services'] = []

	images = []
	# ***specs for object
	# ***ONLY SCRAPE MANAGEMENT PHOTOS
	# ***refer to screenshot "photo-caption.png" for the field values
	# url | string | null
	# caption | string | null
	# date | string (as long as it is a parsable format; e.g. "(Jul 2016)" ) | null


	reviews = []
	# ****specs for object
	# date | string (as long as it is a parsable format; e.g. "2016/01/30") | null
	# username | string | null
	# userRanking | string; e.g. "Level 02 Contributor" | null
	# userReviewCount | integer | null
	# reviewText | string | null
	# score | integer | null

	def scrape(self, location, lang='en'):
		url = None
		for element in language.language_list:
			if element['dialect'] == lang:
				url = element["url"]
		if url:
			s = requests.Session()
			s.get(url)
			response = s.post("https://www.tripadvisor.com/UpdateSessionDatesAjax")
			print response.json()