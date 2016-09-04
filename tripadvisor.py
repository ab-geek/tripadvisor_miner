#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import io
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
	
	def scrape(self, location, lang='en'):
		self.baseurl = None
		#disable warnings
		requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
		requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)
		requests.packages.urllib3.disable_warnings(SNIMissingWarning)
		for element in language.language_list:
			if element['dialect'] == lang:
				self.baseurl = "https://"+element["url"][2:]
		if self.baseurl:
			self.s = requests.Session()
			self.headers ={
				'Accept': "text/javascript, text/html, application/xml, text/xml, */*",
				'Accept-Encoding': "gzip, deflate, sdch",
				'Connection':'keep-alive',
				'Host':self.baseurl[8:],
				'Referer':self.baseurl,
				'User-Agent': "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/49.0.2623.87 Chrome/49.0.2623.87 Safari/537.36",
				'X-Requested-With': 'XMLHttpRequest'
				}
			try:
				response = self.s.get(self.baseurl).text
			except:
				return
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
				self.headers['X-Puid'] = gapu

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
			garecord = self.baseurl + "GARecord"
			try:
				response = self.s.get(garecord, params = args, headers = self.headers)
			except:
				pass
			typeahead_url = self.baseurl+"TypeAheadJson"
			args = {
				'action': "RECORD",
				'eventType':'start',
				'uiOrigin':'unknown',
				'startTime':str(int(time.time()*1000)),
				'source':'unknown',
				'global':True,
				'searchSessionId':searchSessionId
			}
			try:
				response = self.s.get(typeahead_url, params = args, headers = self.headers)
			except:
				pass
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
			try:
				response = self.s.get(typeahead_url, params=payload, headers = self.headers)
				url = response.json()
			except:
				pass
			# print url
			# exit(0)
			try:
				url = url["results"][0]["urls"][0]["fallback_url"][1:]
			except:
				print "location not allowed"
				url = None
			if url:
				url = self.baseurl+url
				# print url
				self.headers['Upgrade-Insecure-Requests']=1
				try:
					response = BeautifulSoup(self.s.get(url,headers=self.headers).text,'html')
				except:
					return
				# print response
				last_page = 1
				try:
					last_page = response.find('div',{'class':'pageNumbers'}).find('a',{'class':'pageNum last taLnk'}).get('data-page-number')
				except:
					pass
				last_page = int(last_page)
				pageCount = 1
				try:
					all_page = dict([(element.get('data-page-number'),self.baseurl+element.get('href')[1:]) for element in response.find('div',{'class':'pageNumbers'}).findAll('a')])
				except:
					pass
				while (pageCount <= last_page):
					hotel_details_per_page = {}
					if ((pageCount > 1) and (str(pageCount) not in all_page.keys())):
						# print "pageCount", pageCount
						new_page_url = response.find('div',{'class':'pageNumbers'}).find('a',{'data-page-number':str(pageCount)})
						if new_page_url:
							new_page_url = new_page_url.get('href')
							all_page[str(pageCount)] = self.baseurl+new_page_url[1:]
							# print all_page.keys()
						else:
							pageCount += 1
							continue
					if pageCount > 1:
						try:
							response = BeautifulSoup(self.s.get(all_page[str(pageCount)],headers=self.headers).text,'lxml')
						except:
							pageCount += 1
							continue
					try:
						hotels = response.find('div',{'id':'HAC_RESULTS'}).findAll('div',{'class':'listing_title'})
					except:
						pageCount += 1
						continue
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
							geoId = m.group(5)
							hotel_details_per_page[hotelId]={
															# 'hotelName': element.find('a').getText().encode('utf-8'),
															'hotelName': element.find('a').getText(),
															'url': self.baseurl + element.find('a').get('href')[1:],
															'location':location,
															'language':lang,
															'searchSessionId': searchSessionId,
															'geoId': geoId,

							}
					print "processing "+str(len(hotel_details_per_page.keys()))+" number of hotels from search results"
					self.make_hotel_json(hotel_details_per_page)
					pageCount += 1
	
	def make_hotel_json(self, hotel_details_per_page):
		for hotelId, details in hotel_details_per_page.iteritems():
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
			
			hotelTripadvisorId = hotelId
			hotelName = details['hotelName']
			# if hotelId == '1950138':
			response = BeautifulSoup(self.s.get(details['url'], headers = self.headers).text,'lxml')
			address = response.find('address')
			# print address
			email = address.find('div',{'class': 'ui_icon email fl icnLink'})
			if email:
				span = email.findNext('div',{'class':'fl'})
				if span:
					span = span.find('span',{'class':'taLnk hvrIE6'})
					if span:
						span = span.get('onclick')
						re1 = '(showEmailHotelOverlay\\()'
						re2 = '(\\d+)' #hotel id
						re3 = '(\\s*,\\s*)' #seperator
						re4 = '(\\\'.*?\\\')' #True or False
						re5 = re3 #seperator
						re6 = re4 #single quote string
						re7 = re3 #seperator
						re8 = re4 #single quote string
						re9 = '(\\))'
						rg = re.compile(re1+re2+re3+re4+re5+re6+re7+re8+re9,re.IGNORECASE|re.DOTALL)
						m = rg.search(span)
						if m:
							if m.group(4) == "'false'":
								isOfferEmail = False
							else:
								isOfferEmail = True
							if m.group(6) == "''":
								overrideOfferEmail = None
							else:
								overrideOfferEmail = m.group(6)[1:-1]
							if m.group(8) == "''":
								contactColumn = None
							else:
								contactColumn = int(m.group(8)[1:-1])

						args = {
							'detail':hotelId,
							'isOfferEmail':isOfferEmail,
							'overrideOfferEmail':overrideOfferEmail,
							'contactColumn':contactColumn
						}
						email = BeautifulSoup(self.s.get("https://www.tripadvisor.com/EmailHotel",params = args).text).find('input',{'name':'overrideOfferEmail'})
						if email:
							email = email.get('value')
							hotelEmail = email
			if address.find('span', {'property': 'streetAddress'}):
				strAddress = address.find('span', {'property': 'streetAddress'}).getText()
				if strAddress:
					# streetAddress = strAddress.encode('utf-8')
					streetAddress = strAddress
			if address.find('span',{'property': 'addressCountry'}):
				if address.find('span',{'property': 'addressCountry'}).get('content'):
					country = address.find('span',{'property': 'addressCountry'}).get('content')
			if address.find('span',{'property': 'addressLocality'}):
				if address.find('span',{'property': 'addressLocality'}).getText():
					# city = address.find('span',{'property': 'addressLocality'}).getText().encode('utf-8')
					city = address.find('span',{'property': 'addressLocality'}).getText()
			if address.find('span',{'property': 'addressRegion'}):
				if address.find('span',{'property': 'addressRegion'}).getText():
					# state = address.find('span',{'property': 'addressRegion'}).getText().encode('utf-8')
					state = address.find('span',{'property': 'addressRegion'}).getText()
			self.headers['Referer'] = details['url']
			payload = {
				'interleaved':True,
				'geoPages':True,
				'details':True,
				'types':'hotel',
				'link_type':'geo',
				'neighborhood_geos':True,
				'matchTags':True,
				'matchGlobalTags':True,
				'matchKeywords':True,
				'strictAnd':True,
				'hglt':True,
				'disableMaxGroupSize':True,
				'max':'6',
				'allowPageInsertionOnGeoMatch':False,
				'defaultListInsertionType':'hotel',
				'scopeFilter':'global',
				'injectNeighborhoods':False,
				'injectNewLocation':True,
				'injectLists':True,
				'nearby':True,
				'local':True,
				'parentids':details['geoId'],
				'query':details['hotelName'],
				'action':'API',
				'uiOrigin':'MASTHEAD',
				'source':'MASTHEAD',
				'startTime':str(int(time.time()*1000)),
				'searchSessionId':details['searchSessionId'],
			}
			print "retriving coordinate"
			coord_response = None
			try:
				coord_response = self.s.get(self.baseurl+'TypeAheadJson', params=payload, headers = self.headers).json()['results'][0]['coords']
			except:
				pass
			if coord_response:
				coord_response = coord_response.split(',')
				latitude = float(coord_response[0])
				longitude = float(coord_response[1])
			print "retriving properties"
			if response.find('a',{'property': 'reviewCount'}):
				reviewCount = response.find('a',{'property': 'reviewCount'}).get('content')
				if reviewCount:
					reviewCount = int(reviewCount)

			if response.find('img',{'class':re.compile('rating')}):
				if response.find('img',{'class':re.compile('rating')}).get('alt'):
					tripAdvisorRating = response.find('img',{'class':re.compile('rating')}).get('alt').split()[0]
					if tripAdvisorRating:
						tripAdvisorRating = float(tripAdvisorRating)
			if response.find('div',{'class':'popRanking popIndexValidation rank_text wrap'}):
				if response.find('div',{'class':'popRanking popIndexValidation rank_text wrap'}).getText():
					text = response.find('div',{'class':'popRanking popIndexValidation rank_text wrap'}).getText()
					# if text:
					# 	rankingInCity = text.replace('\n','')
					re1 = '([0-9 ]+(\\W)?[0-9 ]*)'
					re2 = '(\\s+(?:[a-z][a-z]+)\\s+)'
					re3 = '([0-9 ]+(\\W)?[0-9 ]*)'
					rg = re.compile(re1+re2+re3,re.IGNORECASE|re.DOTALL|re.U)
					m = rg.search(text)
					if m:
						rankingInCity = m.group(1)+'/'+m.group(3)
			if response.find('span',{'class':'tag'}):
				if response.find('span',{'class':'tag'}).getText():
					# hotelTagCloud = [element.getText().strip().encode('utf-8') for element in response.findAll('span',{'class':'tag'}) if element.getText()]
					hotelTagCloud = [element.getText().strip() for element in response.findAll('span',{'class':'tag'}) if element.getText()]
			
			if response.find('div',{'id':'AMENITIES_TAB'}):
				aminities_tab = response.find('div',{'id':'AMENITIES_TAB'})
				if aminities_tab.find('div',{'class':'additional_info tabs_description off'}):
					span = aminities_tab.find('div',{'class':'additional_info tabs_description off'}).find('span',{'class':'tabs_descriptive_text'})
					if span:
						if span.getText():
							# officialHotelDescription = span.getText().encode('utf-8')
							officialHotelDescription = span.getText()
				if aminities_tab.find('div',{'class':'additional_info_amenities'}):
					span = aminities_tab.find('div',{'class':'additional_info_amenities'}).find('div',{'class':'content'})
					if span:
						span = span.getText()
						if span:
							# additionalHotelInformation = span.replace('\n\n','\n').encode('utf-8')
							additionalHotelInformation = span.replace('\n\n','\n')
				try:
					all_highlights = aminities_tab.find('div',{'class':'amenity_hdr highlights'}).findNext('div',{'class':'property_tags_wrap'}).findAll('li')
					# amenities['highlights'] = [element.getText().replace("  "," ").replace('\n','').encode('utf-8') for element in all_highlights]
					amenities['highlights'] = [element.getText().replace("  "," ").replace('\n','') for element in all_highlights]
				except:
					pass
				try:
					# amenities['aboutTheProperty'] = [element.getText().replace('\n','').replace('  ',' ').encode('utf-8') for element in aminities_tab.find('div',{'class':'amenity_hdr'},text=re.compile('About the property')).findNext('div').findAll('li')]
					amenities['aboutTheProperty'] = [element.getText().replace('\n','').replace('  ',' ') for element in aminities_tab.find('div',{'class':'amenity_hdr'},text=re.compile('About the property')).findNext('div').findAll('li')]
				except:
					pass
				try:
					# amenities['thingsToDo'] = [element.getText().replace('\n','').replace('  ',' ').encode('utf-8') for element in aminities_tab.find('div',{'class':'amenity_hdr'},text=re.compile('Things to do')).findNext('div').findAll('li')]
					amenities['thingsToDo'] = [element.getText().replace('\n','').replace('  ',' ') for element in aminities_tab.find('div',{'class':'amenity_hdr'},text=re.compile('Things to do')).findNext('div').findAll('li')]
				except:
					pass
				try:
					# amenities['roomTypes'] = [element.getText().replace('\n','').replace('  ',' ').encode('utf-8') for element in aminities_tab.find('div',{'class':'amenity_hdr'},text=re.compile('Room types')).findNext('div').findAll('li')]
					amenities['roomTypes'] = [element.getText().replace('\n','').replace('  ',' ') for element in aminities_tab.find('div',{'class':'amenity_hdr'},text=re.compile('Room types')).findNext('div').findAll('li')]
				except:
					pass
				try:
					# amenities['internet'] = [element.getText().replace('\n','').replace('  ',' ').encode('utf-8') for element in aminities_tab.find('div',{'class':'amenity_hdr'},text=re.compile('Internet')).findNext('div').findAll('li')]
					amenities['internet'] = [element.getText().replace('\n','').replace('  ',' ') for element in aminities_tab.find('div',{'class':'amenity_hdr'},text=re.compile('Internet')).findNext('div').findAll('li')]
				except:
					pass
				try:
					# amenities['services'] = [element.getText().replace('\n','').replace('  ',' ').encode('utf-8') for element in aminities_tab.find('div',{'class':'amenity_hdr'},text=re.compile('Services')).findNext('div').findAll('li')]
					amenities['services'] = [element.getText().replace('\n','').replace('  ',' ') for element in aminities_tab.find('div',{'class':'amenity_hdr'},text=re.compile('Services')).findNext('div').findAll('li')]
				except:
					pass
			print "retriving images"
			if response.find('div',{'id':'PHOTOS_TAB'}):
				photo_tab = response.find('div',{'id':'PHOTOS_TAB'})
				if response.find('div',{'class':'albumGroup managementPhotos '}):
					all_photo_url = self.baseurl + "LocationPhotoAlbum"
					args = {
						'detail':hotelId,
						'geo':details['geoId'],
						'filter':1,
						'albumId':101,
						'heroMinWidth':1311,
						'heroMinHeight':338,
						'albumid':101,
						'albumViewMode':'images',
						'albumPartialsToUpdate':'full',
						'extraAlbumCoverCount':4,
						'area':'QC_Meta_Mini|Photo_Lightbox',
						'metaReferer':'Hotel_Review',
						'metaRequestTiming':int(time.time()*1000),
						}
					# print "first argument passed ", args
					# print "headers", self.headers
					self.headers.pop('Upgrade-Insecure-Requests', None)
					photo_response = BeautifulSoup(self.s.get(all_photo_url,headers = self.headers,params = args).text)
					if photo_response:
						photo_response = photo_response.findAll('div',{'class':"albumGridItem"})
						for element in photo_response:
							url = element.find('img',{"src":re.compile('media-cdn.tripadvisor.com')})
							if url:
								url = url.get('src')
								args2 = dict([element2.split('=') for element2 in element.find('a').get('data-href').split('&')])
								args2['placementName'] = 'media_albums'
								args2['servletClass'] = 'com.TripResearch.servlet.LocationPhotoAlbum'
								args2['servletName'] = 'LocationPhotoAlbum'
								args2['albumPartialsToUpdate'] = 'partial'
								args2['heroMinWidth'] = '974'
								args2['heroMinHeight'] = '306'
								try:
									single_image_response = BeautifulSoup(self.s.post(self.baseurl+"MetaPlacementAjax",data=args2,headers=self.headers).text)
								except:
									pass
								try:
									caption = single_image_response.find('div',{'class':'captionText'}).getText().replace("\n",'').split('"')[-2]
								except:
									caption = ''
								try:
									date = single_image_response.find('div',{'class':'captionText'}).getText().replace("\n",'').split('"')[-1]
								except:
									date = ''
								images.append({'url':url,'caption':caption,'date':date})
							else:
								continue
			print "retriving reviews"
			if response.find('div',{'id':'REVIEWS'}):
				all_review = response.find('div',{'id':'REVIEWS'})
				review_list = all_review.findAll('div',{'class':'reviewSelector'})
				for review in review_list:
					try:
						review_date = review.find('span',{'class':'ratingDate'}).getText()
						if self.baseurl == "https://www.tripadvisor.com/":
							review_date = review_date.strip("Reviewed ")
					except:
						review_date = ''
					try:
						username = review.find('div',{'class':re.compile('username')}).getText().strip()
					except:
						username = ''
					try:
						userRanking = review.find('div',{'class':re.compile('levelBadge')}).get("class")[-1]
					except:
						userRanking = ''
					try:
						userReviewCount = int(re.search('(\\d+)', review.find('div',{'class':'reviewerBadge badge'}).getText().strip().replace(',','').replace('  ','')).group(1))
					except:
						userReviewCount = 0
					try:
						reviewText = review.find('div',{'class':'entry'}).getText().replace('\n\n','')
					except:
						reviewText = ''
					try:
						score = float(re.search('(\\d+(\\.\\d+)?)', review.find('span',{'class':'rate sprite-rating_s rating_s'}).find('img').get('alt').strip().replace(',','').replace('  ','')).group(1))
					except:
						score = 0
					reviews.append({'review_date':review_date,'username':username,'userRanking':userRanking,'userReviewCount':userReviewCount,'reviewText':reviewText,'score':score,})

			result = {
						'hotelTripadvisorId':hotelTripadvisorId,
						'hotelName': hotelName,
						'hotelEmail':hotelEmail,
						'streetAddress': streetAddress,
						'country': country,
						'city': city,
						'state': state,
						'longitude': longitude,
						'latitude': latitude,
						'tripAdvisorRating':tripAdvisorRating,
						'reviewCount':reviewCount,
						'rankingInCity':rankingInCity,
						'hotelTagCloud':hotelTagCloud,
						'officialHotelDescription':officialHotelDescription,
						'additionalHotelInformation':additionalHotelInformation,
						'amenities':amenities,
						'images':images,
						'reviews':reviews,
						}

			new_file_name = details['language']+'-'+details['location']+'-'+hotelId+'.json'
			with io.open(new_file_name, 'w',encoding='utf8') as new_file:
				new_file.write(unicode(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=4)))
			print new_file_name+" file processed"
			# 	exit(0)