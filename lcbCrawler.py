# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import re
import requests
import pandas as pd

_formatUrl = 'http://www.leboncoin.fr/annonces/offres/{region}/?o={num_page}&q={criteria}'
_regions = set([
			"alsace",
			"aquitaine",
			"auvergne",
			"basse_normandie",
			"bourgogne",
			"bretagne",
			"centre",
			"champagne_ardenne",
			"corse",
			"franche_comte",
			"haute_normandie",
			"ile_de_france",
			"languedoc_roussillon",
			"limousin",
			"lorraine",
			"midi_pyrenees",
			"nord_pas_de_calais",
			"pays_de_la_loire",
			"picardie",
			"poitou_charentes",
			"provence_alpes_cote_d_azur",
			"rhone_alpes",
			"guadeloupe",
			"martinique",
			"guyane",
			"reunion"
		])

def _getRidOfNonNumeric (string):
	return re.sub(r'[^\d]+', '', string)

def _getRidOfNonAlphaNumeric (string):
	return re.sub('[^0-9a-zA-Z]+', '', string)

class lbcPage:
	content = {}

	def __init__(self, soup, region=None):
		if soup is None:
			return

		product = soup.find('title')
		if product:
			self.content['product'] = product.next

		seller = soup.find('div', {'class': 'upload_by'})
		if seller:
			self.content['seller'] = seller.find('a').next

		price = soup.find('span', {'class': 'price'})
		if price:
			self.content['price'] = _getRidOfNonNumeric(price.next)

		city = soup.find('td', {'itemprop': 'addressLocality'})
		if city:
			self.content['city'] = city.next

		zipcode = soup.find('td', {'itemprop': 'postalCode'})
		if zipcode:
			self.content['zipcode'] = _getRidOfNonNumeric(zipcode.next)

		latitude = soup.find('meta', {'itemprop': 'latitude'})
		if latitude:
			self.content['latitude'] = float(latitude['content'])

		longitude = soup.find('meta', {'itemprop': 'longitude'})
		if longitude:
			self.content['longitude'] = float(longitude['content'])

		params = soup.find('div', {'class': 'lbcParams criterias'})
		if params:
			for param in params.findAll('tr'):
				paramLabel = _getRidOfNonAlphaNumeric(param.next.next.next).lower()
				self.content[paramLabel] = param.next.next.next.next.next.next

		description = soup.find('div', {'itemprop': 'description'}, text=True)
		if description:
			self.content['description'] = description.next

		if region:
			self.content['region'] = region


def _nextUrlPages(criteria, region, num_page):
	""" Return all links to products """
	url = _formatUrl.format(region=region, num_page=num_page, criteria=criteria)
	soupPage = BeautifulSoup(requests.get(url).text.encode('utf-8'), 'html.parser')

	# Tests if the url is empty
	isEmpty = soupPage.find('h1', {'id': 'result_ad_not_found_proaccount'})
	if not isEmpty is None:
		return []
	isEmpty = soupPage.find('h2', {'id': 'result_ad_not_found'})
	if not isEmpty is None:
		return []

	# Get all links for products within
	allLinksFromPage = soupPage.find('div', {'class': 'list-lbc'})
	allLinksFromPage = allLinksFromPage.findAll('a', href=re.compile('http://www.leboncoin.fr/'))
	return [e['href'] for e in allLinksFromPage]


def searchLBC (criteria, regions):
	""" Search @criteria in @regions at leboncoin.fr and @return a pandas DataFrame of the results """
	if not isinstance(regions, list):
		regions = [regions]
	if not set(regions).issubset(_regions):
		raise ValueError('Invalid region names : ' + str(regions))
	if not isinstance(criteria, str):
		criteria = str(criteria)
	criteria = criteria.replace(' ', '+')

	res = []
	for region in regions:
		nPage = 0
		while True:
			nPage += 1
			urlPages = _nextUrlPages(criteria, region, nPage)
			for url in urlPages:
				soupPage = BeautifulSoup(requests.get(url).text.encode('utf-8'), 'html.parser')
				contentPage = lbcPage(soupPage).content
				res.append(contentPage.copy())
			if urlPages == []:
				break
	return pd.DataFrame(res)

print searchLBC('enceinte', ['guyane', 'martinique'])