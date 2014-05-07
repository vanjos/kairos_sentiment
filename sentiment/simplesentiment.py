#!/usr/bin/python

#
# Sentiment analysis with minimal dictionary
#
VERSION="0.1"
usage = """%prog [options] [command]
Commands:
	try	<text>				Get sentiment for arbitrary text
	twitter <query>			Get sentiment on this query string (trending)
	url <url>               Get the general sentiment regarding a page

Options:

Examples:

	"""

import math
import re
import sys, os
reload(sys)
sys.setdefaultencoding('utf-8')

class Simplesentiment():

	def __init__(self):
		self.STEMMER_WORDNET_ENGLISH    = 1
		self.STEMMER_SNOWBALL_ENGLISH   = 2
		self.STEMMER_LANCASTER_ENGLISH  = 3
		self.STEMMER_PORTER_ENGLISH     = 4
		self.STEMMER_NO_STEMMER         = 99

		self.STEMMERS = {
			self.STEMMER_WORDNET_ENGLISH    :   'WORDNET',
		    self.STEMMER_SNOWBALL_ENGLISH   :   'SNOWBALL',
		    self.STEMMER_LANCASTER_ENGLISH  :   'LANCASTER',
		    self.STEMMER_PORTER_ENGLISH     :   'PORTER',
		    self.STEMMER_NO_STEMMER         :   'NO_STEMMER'
		}

		self.TOKENIZER_SIMPLETON        = 1
		self.TOKENIZER_NLTK             = 2

		self.TOKENIZERS = {
			self.TOKENIZER_SIMPLETON        :   'SIMPLETON',
		    self.TOKENIZER_NLTK             :   'NLTK'
		}

		self.DENOMS = {
			0   :   'SQRT',
		    1   :   'X',
		    2   :   'X^2'
		}

		# The dictionary we'll use
		filenameAFINN = os.path.dirname(os.path.realpath(__file__)) + '/dictionaries/AFINN-111.txt'
		self.afinn = dict(map(lambda (w, s): (w, int(s)), [
		ws.strip().split('\t') for ws in open(filenameAFINN) ]))

	def getDenoms(self):
		return self.DENOMS

	def getTokenizers(self):
		return self.TOKENIZERS

	def getStemmers(self):
		return self.STEMMERS

	def html_escape(self, text):
		"""Produce entities within text."""
		html_escape_table = {
			"&": "&amp;",
			'"': "&quot;",
			"'": "&apos;",
			">": "&gt;",
			"<": "&lt;",
			":": "%3A",
			"#": "%23",
			"@": "%40",
			"?": "%3F",
			" ": "%20",
		}
		return "".join(html_escape_table.get(c,c) for c in text)

	def bayesSentiment(self, text):
		from nltk.tokenize.punkt import PunktSentenceTokenizer
		from senti_classifier import senti_classifier

		# break up text into sentences
		stzr = PunktSentenceTokenizer()
		sents = stzr.tokenize(text)
		pos_score, neg_score = senti_classifier.polarity_scores(sents)
		#print pos_score, neg_score
		return [pos_score, neg_score]


	def sentiment(self, text, t=1, v=99):
		"""
		Returns a float for sentiment strength based on the input text.
		Positive values are positive valence, negative value are negative valence.
		"""
		if t == self.TOKENIZER_SIMPLETON:
			pattern_split = re.compile(r"\W+")
			words = pattern_split.split(text.lower())
		if t == self.TOKENIZER_NLTK:
			import nltk
			raw =  nltk.clean_html(text) #nltk
			words = nltk.word_tokenize(raw)

		if v == self.STEMMER_NO_STEMMER:
			sentiments = map(lambda word: self.afinn.get(word, 0), words)
		else:
			sentiments = map(lambda word: self.afinn.get(self.lemmatize(word, v), 0), words)

		if sentiments:
			# How should you weight the individual word sentiments?
			# You could do N, sqrt(N) or 1 for example. Here I use sqrt(N)
			total   = float(sum(sentiments))
			length  = len(sentiments)
			sentiment = [
				float(total/math.sqrt(length)),
				float(total/length),
				float(total/math.pow(length,2))
			]

		else:
			sentiment = [0, 0, 0]
		return sentiment

	def apilogin(self, urllib2, top_level_url, remaining_url, username, password):
		# build up a password manager...
		password_mgr    =   urllib2.HTTPPasswordMgrWithDefaultRealm()
		password_mgr.add_password(None, top_level_url, username, password)

		handler = urllib2.HTTPBasicAuthHandler(password_mgr)
		opener = urllib2.build_opener(handler)
		opener.open(top_level_url + remaining_url)
		urllib2.install_opener(opener)

	def calaissentiment(self, options, text):
		"""
		"""
		import urllib2, simplejson
		from urllib import urlencode

		BASE_URL    =   ' http://api.opencalais.com/tag/rs/enrich'
		API_KEY     =   '9tv3mnazecc76xhy2empqzyu'

		post_parameters = {
			'x-calais-licenseID'    :   API_KEY,
		    'content-type'          :   'text/raw',
		    'accept'                :   'application/json',
		    'enableMetadataType'    :   'GenericRelations,SocialTags',
		    'content'               :   text
		}

		response = simplejson.load(urllib2.urlopen(urllib2.Request(BASE_URL, data=urlencode(post_parameters), headers=post_parameters)))
		print simplejson.dumps(response, sort_keys=True, indent=8)

	def alchemysentiment(self, options, text=None, url=None):
		"""

		"""
		import urllib2, simplejson, json
		from urllib import urlencode
		if text:
			BASE_URL    = 'http://access.alchemyapi.com/calls/text/TextGetTextSentiment'
		if url:
			BASE_URL    = 'http://access.alchemyapi.com/calls/html/HTMLGetTextSentiment'
		API_KEY     = 'd827d190b313e3f9bca55c86f0fb1ee6ff297334'
		#API_KEY	=	'97b5c535a4809df1980acd0bbce88881030c8ae2'

		post_parameters = {
			'apikey'        :   API_KEY,
		    'outputMode'    :   'json',
		    'showSourceText':   '1'
		}

		if text:
			post_parameters['text'] = text
		if url:
			baseurl = url
			j = urllib2.urlopen(baseurl)
			text = j.read()
			try:
				from feedparser import _getCharacterEncoding as enc
			except ImportError:
				enc = lambda x, y: ('utf-8', 1)
			encoding = enc(j.headers, text)[0]
			if encoding == 'us-ascii':
				encoding = 'utf-8'

			post_parameters['html'] = text.decode(encoding)
			post_parameters['url']  = url

		response = simplejson.load(urllib2.urlopen(urllib2.Request(BASE_URL, data=urlencode(post_parameters))))
		#print simplejson.dumps(response, sort_keys=True, indent=3)

		return response

	def alchemyentityextraction(self, options, text=None, url=None):
		"""
		"""
		import urllib2, simplejson, json
		from urllib import urlencode
		if text:
			BASE_URL    = 	'http://access.alchemyapi.com/calls/text/TextGetRankedNamedEntities'
		if url:
			BASE_URL    = 	'http://access.alchemyapi.com/calls/text/HTMLGetRankedNamedEntities'

		API_KEY     = 'd827d190b313e3f9bca55c86f0fb1ee6ff297334'

		post_parameters = {
			'apikey'        :   API_KEY,
		    'outputMode'    :   'json',
		    'coreference'	:   '1',
		    'disambiguate'	:	'1',
		    'sentiment'		:	'1'
		}

		if text:
			post_parameters['text'] = text
		if url:
			baseurl = url
			j = urllib2.urlopen(baseurl)
			text = j.read()
			try:
				from feedparser import _getCharacterEncoding as enc
			except ImportError:
				enc = lambda x, y: ('utf-8', 1)
			encoding = enc(j.headers, text)[0]
			if encoding == 'us-ascii':
				encoding = 'utf-8'

			post_parameters['html'] = text.decode(encoding)
			post_parameters['url']  = url

		response = simplejson.load(urllib2.urlopen(urllib2.Request(BASE_URL, data=urlencode(post_parameters))))
		#print simplejson.dumps(response, sort_keys=True, indent=3)

		return response

	def openamplifysentiment(self, options, text, analysis=None):
		"""
		analysis        =   ['all','topics','actions','demographics','styles']
		output_format   =   ['xml','json','dart']
		"""
		import urllib2, simplejson
		from urllib import urlencode
		BASE_URL    =   'http://portaltnx20.openamplify.com/AmplifyWeb_v21/AmplifyThis'
		API_KEY     =   '2guat2q36tzc8kzb6g2qj6m8zt2yq9vs'

		post_parameters = {
			'inputtext'     :   text,
			'apiKey'        :   API_KEY,
			'outputformat'  :   'json',
			'analysis'      :   analysis if analysis else 'all',
		}

		response = simplejson.load(urllib2.urlopen(urllib2.Request(BASE_URL, data=urlencode(post_parameters))))

		print simplejson.dumps(response, sort_keys=True, indent=8)

		openamplify_results = {
			'Polarity'          :   {
					'Max'   :   {
						response['ns1:AmplifyResponse']['AmplifyReturn']['Styles']['Polarity']['Max']['Name'] :
							response['ns1:AmplifyResponse']['AmplifyReturn']['Styles']['Polarity']['Max']['Value']
					},
					'Mean'  :   {
						response['ns1:AmplifyResponse']['AmplifyReturn']['Styles']['Polarity']['Mean']['Name'] :
							response['ns1:AmplifyResponse']['AmplifyReturn']['Styles']['Polarity']['Mean']['Value']
					},
		            'Min'   :   {
			            response['ns1:AmplifyResponse']['AmplifyReturn']['Styles']['Polarity']['Min']['Name'] :
				            response['ns1:AmplifyResponse']['AmplifyReturn']['Styles']['Polarity']['Min']['Value']
		            }
			},
			'Demographics'      :   {
				'Age'	    :   {
					response['ns1:AmplifyResponse']['AmplifyReturn']['Demographics']['Age']['Name'] :
						response['ns1:AmplifyResponse']['AmplifyReturn']['Demographics']['Age']['Value']
			    },
			    'Education' :   {
				    response['ns1:AmplifyResponse']['AmplifyReturn']['Demographics']['Education']['Name'] :
					    response['ns1:AmplifyResponse']['AmplifyReturn']['Demographics']['Education']['Value']
			    },
			    'Gender'    :   {
				    response['ns1:AmplifyResponse']['AmplifyReturn']['Demographics']['Gender']['Name'] :
					    response['ns1:AmplifyResponse']['AmplifyReturn']['Demographics']['Gender']['Value']
			    },
				'Language'  :   {
					response['ns1:AmplifyResponse']['AmplifyReturn']['Demographics']['Language']['Name'] :
						response['ns1:AmplifyResponse']['AmplifyReturn']['Demographics']['Language']['Value']
				}
			},
		    'Styles'            :   {
			    'Contrast'  :   {
				    response['ns1:AmplifyResponse']['AmplifyReturn']['Styles']['Contrast']['Name'] :
					    response['ns1:AmplifyResponse']['AmplifyReturn']['Styles']['Contrast']['Value']
			    },
		        'Decisiveness'  :   {
			        response['ns1:AmplifyResponse']['AmplifyReturn']['Styles']['Decisiveness']['Name'] :
				        response['ns1:AmplifyResponse']['AmplifyReturn']['Styles']['Decisiveness']['Value']
		        },
		        'Flamboyance'   :   {
			        response['ns1:AmplifyResponse']['AmplifyReturn']['Styles']['Flamboyance']['Name'] :
				        response['ns1:AmplifyResponse']['AmplifyReturn']['Styles']['Flamboyance']['Value']
		        },
		        'OfferingGuidance'  :   {
			        response['ns1:AmplifyResponse']['AmplifyReturn']['Styles']['OfferingGuidance']['Name'] :
				        response['ns1:AmplifyResponse']['AmplifyReturn']['Styles']['OfferingGuidance']['Value']
		        },
		        'RequestingGuidance'    :   {
			        response['ns1:AmplifyResponse']['AmplifyReturn']['Styles']['RequestingGuidance']['Name'] :
				        response['ns1:AmplifyResponse']['AmplifyReturn']['Styles']['RequestingGuidance']['Value']
		        },
		        'Slang'         :   {
			        response['ns1:AmplifyResponse']['AmplifyReturn']['Styles']['Slang']['Name'] :
				        response['ns1:AmplifyResponse']['AmplifyReturn']['Styles']['Slang']['Value']
		        },
		        'TemporalityResult'    :   {
			        response['ns1:AmplifyResponse']['AmplifyReturn']['Styles']['TemporalityResult']['Temporality']['Name'] :
				        response['ns1:AmplifyResponse']['AmplifyReturn']['Styles']['TemporalityResult']['Temporality']['Value']
		        }
		    }
		}
		#print simplejson.dumps(openamplify_results, sort_keys=True, indent=8)

		return openamplify_results


	def theysaysentiment(self, options, text, level='doc'):
		"""
		levels = ['doc', 'sentence', 'entity', 'entityrelation', 'word']
		"""
		import simplejson, urllib, urllib2
		BASE_URL    = 'http://api.theysay.io/v1/'
		TRAIL_URL   = 'sentiment?'
		USERNAME    = 'ghafoura@theysayanalytics.com'
		PASSWORD    = 'Disent-Ils2984'
		headers     = {
			'Content-Type'  :   'application/json',
		    'Accept'        :   'application/json'
		}

		data = {}
		data['text']   = ' '.join(text) if isinstance(text, list) else text
		TRAIL_URL       += urllib.urlencode(data)

		theysayresults  =   {}

		level = level if level else 'doc'

		self.apilogin(urllib2, BASE_URL, TRAIL_URL + '&level=' + level, USERNAME, PASSWORD)

		req         = urllib2.Request(BASE_URL + TRAIL_URL + '&level=' + level , headers=headers)
		response    = simplejson.load(urllib2.urlopen(req))

		print simplejson.dumps(response, sort_keys=True, indent=2)
		if level == 'doc':
			theysayresults  =   {'Overall Sentiment': response['sentiment']}
		elif level == 'entityrelation':
			for relation in response:
				if not theysayresults:
					theysayresults  =   {relation['entity1']['text'] + ' ---> ' + relation['entity2']['text'] : relation['sentiment'] }
				else:
					theysayresults[relation['entity1']['text'] + ' ---> ' + relation['entity2']['text']] = relation['sentiment']
		return theysayresults


	def twitterer(self, options, query=None):
		"""
		Returns a float for sentiment strength based on the query string.
		Sort of like trending on twitter.
		"""
		import simplejson
		import urllib
		from dateutil import parser

		#try:
		twitterquery=""

		# build up a query
		if options:
			if ('tweeter' in options and options['tweeter']):
				twitterquery = 'from:%s ' % options['tweeter']
			if ('fromdate' in options and options['fromdate']):
				try:
						fromdate = parser.parse(options['fromdate']).date()
				except:
						print 'Cannot convert this date: %s' % options['fromdate']
				twitterquery += 'since:%s ' % fromdate
			if ('todate' in options and options['todate']):
				try:
						todate = parser.parse(options['todate']).date()
				except:
						print 'Cannot convert this date: %s' % options['todate']
				twitterquery += 'until:%s ' % todate
			if ('hashtag' in options and options['hashtag']):
				twitterquery += '#%s ' % options['hashtag']
			if ('mention' in options and options['mention']):
				twitterquery += '@%s ' % options['mention']
			if ('negate' in options and options['negate']):
				twitterquery += '-%s ' % options['negate']

		if (query):
			twitterquery += str(query)

		json = simplejson.load(urllib.urlopen("http://search.twitter.com/search.json?q=" + self.html_escape(twitterquery.lower())))

		if (json['results']):
			values = {}

			print("%29s" % 'DENOMINATORS / NORMALIZATION')
			print("%9s %9s %9s %14s %14s %35s" % ("X^2", "X", "SQRT", "T_METHOD", "L_METHOD", "URL"))
			for t_method in self.getTokenizers():
				print '-' * 120
				for l_method in self.getStemmers():
					sentiment = self.sentiment(' '.join(tweet['text'] for tweet in json['results']), t_method, l_method)
					for denom, name in self.getDenoms().items():
						if not values:
							values = {'%s [%14s:%14s] (%s)' % ("http://search.twitter.com/search.json?q=" + twitterquery.lower(),
							                                   self.TOKENIZERS[t_method], self.STEMMERS[l_method],
							                                   name) : sentiment[denom]}
						else:
							values['%s [%14s:%14s] (%s)' % ("http://search.twitter.com/search.json?q=" + twitterquery.lower(),
							                                self.TOKENIZERS[t_method], self.STEMMERS[l_method],
							                                name)] = sentiment[denom]
					print '%9f %9f %9f %14s %14s %s' % (sentiment[0], sentiment[1], sentiment[2],
					                                    self.TOKENIZERS[t_method], self.STEMMERS[l_method], "http://search.twitter.com/search.json?q=" + twitterquery.lower())
			return values
		else:
			return ["http://search.twitter.com/search.json?q=" + twitterquery.lower(), 0]
			#except:
		#	print 'Cannot check for what you have requested'

	def lemmatize(self, token, v=1):
		if v == self.STEMMER_WORDNET_ENGLISH:
			from nltk.stem.wordnet import WordNetLemmatizer
			lmtzr = WordNetLemmatizer()
			return lmtzr.lemmatize(token)

		if v == self.STEMMER_SNOWBALL_ENGLISH:
			from nltk import stem
			lmtzr =stem.snowball.EnglishStemmer()
			return lmtzr.stem(token)

		if v == self.STEMMER_LANCASTER_ENGLISH:
			from nltk.stem.lancaster import LancasterStemmer
			lmtzr = LancasterStemmer()
			return lmtzr.stem(token)

		if v == self.STEMMER_PORTER_ENGLISH:
			from nltk.stem.porter import PorterStemmer
			lmtzr = PorterStemmer()
			return lmtzr.stem(token)

	def strippedurl(self, options, url):
		sys.path.append(os.path.dirname(__file__))
		from sentiment.testsentiment.models.html2text import _html2text

		try: #Python3
			import urllib.request as urllib
		except:
			import urllib

		def optwrap(text):
			"""Wrap all paragraphs in the provided text."""
			#if not BODY_WIDTH:
			if 1:
				return text

			assert wrap, "Requires Python 2.3."
			result = ''
			newlines = 0
			for para in text.split("\n"):
				if len(para) > 0:
					if para[0] != ' ' and para[0] != '-' and para[0] != '*':
						for line in wrap(para, BODY_WIDTH):
							result += line + "\n"
						result += "\n"
						newlines = 2
					else:
						if not onlywhite(para):
							result += para + "\n"
							newlines = 1
				else:
					if newlines < 2:
						result += "\n"
						newlines += 1
			return result

		def wrapwrite(text):
			text = text.encode('utf-8')
			try: #Python3
				sys.stdout.buffer.write(text)
			except AttributeError:
				sys.stdout.write(text)

		def html2text_file(html, out=wrapwrite, baseurl=''):
			h = _html2text(out, baseurl)
			h.feed(html)
			h.feed("")
			return h.close()

		def html2text(html, baseurl=''):
			return optwrap(html2text_file(html, None, baseurl))

		if url.startswith('http://') or url.startswith('https://'):
			baseurl = url
			j = urllib.urlopen(baseurl)
			text = j.read()
			try:
				from feedparser import _getCharacterEncoding as enc
			except ImportError:
				enc = lambda x, y: ('utf-8', 1)
			encoding = enc(j.headers, text)[0]
			if encoding == 'us-ascii':
				encoding = 'utf-8'

			data = text.decode(encoding)

		else:
			print 'Cannot open this URL %s' % url

		values = {}

		print("%29s" % 'DENOMINATORS / NORMALIZATION')
		print("%9s %9s %9s %14s %14s %35s" % ("X^2", "X", "SQRT", "T_METHOD", "L_METHOD", "URL"))
		for t_method in self.getTokenizers():
			print '-' * 120
			for l_method in self.getStemmers():
				sentiment = self.sentiment(html2text(data, baseurl), t_method, l_method)
				for denom, name in self.getDenoms().items():
					if not values:
						values = {'%s [%14s:%14s] (%s)' % (baseurl, self.TOKENIZERS[t_method], self.STEMMERS[l_method],
						                                   name) : sentiment[denom]}
					else:
						values['%s [%14s:%14s] (%s)' % (baseurl, self.TOKENIZERS[t_method], self.STEMMERS[l_method],
						                                name)] = sentiment[denom]
				print '%9f %9f %9f %14s %14s %s' % (sentiment[0], sentiment[1], sentiment[2],
				                                   self.TOKENIZERS[t_method], self.STEMMERS[l_method], baseurl)
		return values


	def simplesentiment(self, text):
		"""
		Returns a value for a piece of text, any arbitrary text
		"""
		try:
				print("%6.2f %s" % (sentiment(text), text))
		except:
			print 'Cannot check this query: %s' % (text)

if __name__ == '__main__':
	# Probably don't want/need to run this manually all that often, more here for testing
	from optparse import OptionParser

	# let's get what we need from command line
	parser = OptionParser(version=VERSION, usage=usage)

	""" Twitter options """
	parser.add_option("-U", "--user", help="Twitter User", action="store", type="string", default=None,
		dest="tweeter")
	parser.add_option("-F", "--fromdate", help="Date to search Twitter from - of the form: YYYY-MM-DD",
		action="store", type="string", default=None, dest="fromdate")
	parser.add_option("-T", "--todate", help="Date to search Twitter until - of the form: YYYY-MM-DD",
		action="store", type="string", default=None, dest="todate")
	parser.add_option("-H", "--hashtag", help="Hashtag search for Twitter #", action="store", type="string", default=None,
		dest="hashtag")
	parser.add_option("-M", "--mention", help="Mention of particular user on Twitter @", action="store", type="string",
		default=None, dest="mention")
	parser.add_option("-N", "--negate", help="Negate some term to search for on Twitter", action="store", type="string",
		default=None, dest="negate")

	(options, args) = parser.parse_args()

	if len(args) < 1:
		parser.print_help()
		sys.exit(1)

	command = args[0].lower()

	ss = Simplesentiment()
	options_dict = vars(options)
	if command == "try":
		ss.simplesentiment(' '.join(args[1:]))
	elif command in ('twitter','twitterer','tweet'):
		ss.twitterer(options_dict, ' '.join(args[1:]))
	elif command in ('url', 'site', 'http', 'web'):
		ss.strippedurl(options_dict, args[1])
		ss.alchemysentiment(options_dict, url=args[1])
	elif command in ('bayes'):
		ss.bayesSentiment(args[1:])
	elif command in ('theysay'):
		for level in ('doc','entity','entityrelation'):
			ss.theysaysentiment(options_dict, args[1:], level)
	elif command in ('openamplify'):
		ss.openamplifysentiment(options_dict, args[1:], analysis=None)
	elif command in ('alchemy', 'alchemyapi'):
		ss.alchemysentiment(options_dict, args[1:])
	elif command in ('opencalais','calais'):
		ss.calaissentiment(options_dict, args[1:])