#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import language
import requests
from bs4 import BeautifulSoup
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.packages.urllib3.exceptions import InsecurePlatformWarning
from requests.packages.urllib3.exceptions import SNIMissingWarning
import time
import hashlib
import random
import re

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
		baseurl = None
		for element in language.language_list:
			if element['dialect'] == lang:
				baseurl = "https://"+element["url"][2:]
		if baseurl:
			s = requests.Session()
			headers ={
				'Accept': "text/javascript, text/html, application/xml, text/xml, */*",
				'Accept-Encoding': "gzip, deflate, sdch",
				'Connection':'keep-alive',
				'Host':baseurl[8:],
				'Referer':baseurl,
				'User-Agent': "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/49.0.2623.87 Chrome/49.0.2623.87 Safari/537.36",
				'X-Requested-With': 'XMLHttpRequest'
				}
			response = s.get(baseurl).text

			re1='(\')'	# Any Single Character 1
			re2='(typeahead)'	# Word 1
			re3='(\\.)'	# Any Single Character 2
			re4='(searchSessionId)'	# Word 2
			re5='(\')'	# Any Single Character 3
			re6='(,)'	# Any Single Character 4
			re7='( )'	# White Space 1
			re8='(\')'	# Any Single Character 5
			re9='([^\']+?)'	# Anything ecvept inverted comma
			re10='(\')'	# Any Single Character 7
			re11='(\\))'	# Any Single Character 8
			re12='(;)'	# Any Single Character 9

			rg = re.compile(re1+re2+re3+re4+re5+re6+re7+re8+re9+re10+re11+re12,re.IGNORECASE|re.DOTALL)
			m = rg.search(response)

			searchSessionId = "no_search_session_id"
			if m:
				searchSessionId=m.group(9)

			re1='(ta\\.uid)'	# Fully Qualified Domain Name 1
			re2='( )'	# White Space 1
			re3='(=)'	# Any Single Character 1
			re4='( )'	# White Space 2
			re5='(\')'	# Any Single Character 2
			re6='([^\']+?)'
			re7='(\')'	# Any Single Character 3
			re8='(;)'	# Any Single Character 4

			gapu = None
			rg = re.compile(re1+re2+re3+re4+re5+re6+re7+re8,re.IGNORECASE|re.DOTALL)
			m = rg.search(response)
			if m:
				gapu=m.group(6)

			if gapu:
				headers['X-Puid'] = gapu

			args = {
				'gac':'TopNav_geo_search',
				'gaa': 'focus',
				'gal':None,
				'gav':0,
				'gani':False,
				'gass':'Home',
				'gapu':gapu,
				'gams':0,

			}
			garecord = baseurl + "GARecord"
			response = s.get(garecord, params = args, headers = headers)
			typeahead_url = baseurl+"TypeAheadJson"
			args = {
				'action': "RECORD",
				'eventType':'start',
				'uiOrigin':'unknown',
				'startTime':str(int(time.time()*1000)),
				'source':'unknown',
				'global':True,
				'searchSessionId':searchSessionId
			}
			response = s.get(typeahead_url, params = args, headers = headers)
			payload = {
				'neighborhood_geos': True,
				'max': '6', 
				'uiOrigin': 'GEOSCOPE',
				'startTime': str(int(time.time()*1000)),
				'searchSessionId': searchSessionId,
				'query': location,
				'types': ['geo', 'theme_park'],
				'hglt': True,
				'source': 'GEOSCOPE',
				'interleaved': True,
				'action': 'API',
				'link_type': 'hotel',
				'details': True
			}
			response = s.get(typeahead_url, params=payload, headers = headers)
			url = response.json()
			try:
				url = url["results"][0]["urls"][0]["fallback_url"][1:]
			except:
				print "location not allowed"
				url = None
			if url:
				url = baseurl+url
				# print url
				headers['Upgrade-Insecure-Requests']=1
				response = BeautifulSoup(requests.get(url,headers=headers).text)
				last_page = response.find('div',{'class':'pageNumbers'}).find('a',{'class':'pageNum last taLnk'}).get('data-page-number')
				last_page = int(last_page)
				pageCount = 1
				all_page = dict([(element.get('data-page-number'),baseurl+element.get('href')[1:]) for element in response.find('div',{'class':'pageNumbers'}).findAll('a')])
				while (pageCount <= last_page):
					hotel_details_per_page = {}
					if ((pageCount > 1) and (str(pageCount) not in all_page.keys())):
						# print "pageCount", pageCount
						new_page_url = response.find('div',{'class':'pageNumbers'}).find('a',{'data-page-number':str(pageCount)})
						if new_page_url:
							new_page_url = new_page_url.get('href')
							all_page[str(pageCount)] = baseurl+new_page_url[1:]
							# print all_page.keys()
						else:
							pageCount += 1
							continue
					if pageCount > 1:
						try:
							response = BeautifulSoup(requests.get(all_page[str(pageCount)],headers=headers).text)
						except:
							pageCount += 1
							continue
					hotels = response.find('div',{'id':'HAC_RESULTS'}).findAll('div',{'class':'listing_title'})
					for element in hotels:
						re1='(\\/)'	# Any Single Character 1
						re2='([^-]+?)'	# Variable Name 1
						re3='(-)'	# Any Single Character 2
						re4='(g)'	# Any Single Character 3
						re5='(\\d+)'	# area code
						re6='(-)'	# Any Single Character 4
						re7='(d)'	# Any Single Character 5
						re8='(\\d+)'	# hotel id
						re9='(-)'	# Any Single Character 6

						rg = re.compile(re1+re2+re3+re4+re5+re6+re7+re8+re9,re.IGNORECASE|re.DOTALL)
						m = rg.search(str(element.find('a').get('href')))
						if m:
							hotelId=m.group(8)
							hotel_details_per_page[hotelId]={
															'hotelName': element.find('a').getText().encode('utf-8'),
															'url': baseurl + element.find('a').get('href')[1:],

							}
					# self.make_hotel_json(hotel_details_per_page)
					print pageCount
					print hotel_details_per_page
					pageCount += 1

				# print all_hotel_details
