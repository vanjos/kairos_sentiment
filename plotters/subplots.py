import numpy as np
import pandas as pd
import matplotlib as mpl
mpl.use('TKAgg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.animation as animation
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
import timeit, random

# global scoping
frequencies = []
start = 0
clock = timeit.default_timer
multiplier = 1
DFrames = {}

def getKairos(what):
  import requests
  trailing_url = {
    'metricnames' : 'metricnames',
    'tagnames'    : 'tagnames',
    'tagvalues'   : 'tagvalues',
  }

  if what not in trailing_url:
    raise Exception('Not a valid Kairos enpoint')

  PORT = 8080
  BASE_URL    =   'http://kairosdb.viafoura.net:' + str(PORT) + '/api/v1/' + trailing_url[what]

  return requests.get(url=BASE_URL)

def queryKairos(what, body):
  import json, requests
  from urllib import urlencode
  trailing_url = {
    'metrics'     : 'datapoints/query',
    'tags'        : 'datapoints/query/tags'
  }

  if what not in trailing_url:
    raise Exception('Not a valid Kairos enpoint')

  PORT = 8080
  BASE_URL    =   'http://kairosdb.viafoura.net:' + str(PORT) + '/api/v1/' + trailing_url[what]

  return requests.post(url=BASE_URL, data=json.dumps(body))

def main(debug=False):
  global frequencies, start, multiplier, DFrames
  import re, datetime, time
  if debug:
    start = clock()

  tags_time_back = '86400'
  metrics_time_back = '60'
  units     = 'seconds'

  check_interval = '5'

  what_matters = ('sentiment','relevance','count')

  #what KairosDB puts in itself
  base_metricnames  = ["kairosdb.datastore.query_collisions","kairosdb.datastore.write_size","kairosdb.jvm.free_memory","kairosdb.jvm.max_memory","kairosdb.jvm.thread_count","kairosdb.jvm.total_memory","kairosdb.protocol.http_request_count","kairosdb.protocol.telnet_request_count"]
  base_tagnames     = ["buffer","host","method"]
  base_tagvalues    = ["data_points","ip-10-63-16-84","metricnames","put","row_key_index","string_index","tagnames","tags","tagvalues","version"]

  # open up Kairos and figure out what we have...
  metricnames = [m for m in getKairos('metricnames').json()['results'] if "/" in m and m not in base_metricnames]
  tagnames = [t for t in getKairos('tagnames').json()['results'] if t not in base_tagnames]
  tagvalues = [tv for tv in getKairos('tagvalues').json()['results'] if tv not in base_tagvalues]
  if debug:
    print("FINISHING KAIROS IN {:.2f}".format(clock()-start))

  # the starting point of a KairosDB tags query
  tags_query = {
    'start_relative'  : {
      'value' : tags_time_back,
      'unit'  : units
    },    
  }

  metrics_to_find = raw_input('Metrics to look for (comma separated): ').strip()
  metrics_in_tags_query = []

  # find ANYTHING from Kairos with sentiment/relevance relating to what is being asked for
  for findme in [f for f in metrics_to_find.split(',')]:
    # only look for specific sentiment OR relevance
    for lookupvalue in ('sentiment','relevance','count'):
      for tag in [t for t in tagvalues if re.match(r"((\w+_)+)?(\w+/)?(\w+)?" + findme + "(_?(\w+)?)/(\w+/)?((\w+)?_?)" + lookupvalue, t)]:
        metrics_in_tags_query.append({'name'  : tag})

  tags_query['metrics'] = metrics_in_tags_query

  if debug:
    # here for printing purposes only
    import json,simplejson
    start = clock()

  # so what do we actually have to query from overall (from Kairos)
  all_available = queryKairos('tags',tags_query).json()
  
  if debug:
    print("FINISHING queryingForSpecific Tags IN {:.2f}".format(clock()-start))
    #print 'ALL TAGS: ', simplejson.dumps(all_available,indent=2), '\n========================================'

  all_results = []
  for i in range(0,len(all_available['queries'])):
    all_results += all_available['queries'][i]['results']

  # this gets us all the metrics and tags available that match our request
  ##  SET THIS UP TO STEP!!!  need to yield results from this
  metrics_tags_available = {ar['name'] : ar['tags'] for ar in all_results}

  if debug:
    print 'THESE TAGS ARE AVAILABLE: ', simplejson.dumps(metrics_tags_available, indent=2), '\n========================================'


  multiplier = 600
  # base Kairos metrics query, must be included with every request
  metrics_query = {
    #'start_relative'  : {
    'start_absolute'  : str(int(round(time.time() * 1000)) - (int(metrics_time_back) * multiplier * 1000)) ,
    #'end_absolute'    : str(int(round(time.time() * 1000)) - ((int(metrics_time_back) - 15) * multiplier * 1000))
      #'value' : str(int(metrics_time_back) * 60) ,
      #'unit'  : units
    #},    
  }

  # how we want the Kairos return values to be aggregated
  aggregators = [
    {
      "name": "sum",
      "sampling": {
        "value": check_interval,
        "unit": units
      }
    }
  ]

  # all the metrics we want that we know about from Kairos
  metrics_to_batch = []
  for m_names in metrics_tags_available:
    metrics_to_batch.append({
        'tags'  : metrics_tags_available[m_names],
        'name'  : m_names,
        'aggregators' : aggregators
    })

  # bundle it all up
  metrics_query['metrics'] = metrics_to_batch


  def getKMetrics(metrics_query):
    if debug:
      start = clock()
    metrics_to_plot = queryKairos('metrics',metrics_query).json()['queries']
    if debug:
      print 'METRICS TO PLOT: ', simplejson.dumps(metrics_to_plot, indent=2), '\n========================================'
      print("FINISHING queryingForSpecific Metrics IN {:.2f}".format(clock()-start))

    samples = dict(zip(what_matters, [{},{},{}]))

    # the time series of all sentiment related to the requested keyword
    for rez in [r['results'] for r in metrics_to_plot if int(r['sample_size'])]:
      for lookingfor in what_matters:
        for result in [rez[i] for i in range(0,len(rez)) if lookingfor in rez[i]['name']]:
          samples[lookingfor][result['name']] = result['values']

    if debug:
      print 'OUR SAMPLES: ', simplejson.dumps(samples, indent=2), '\n========================================'

    # it's now time to re-combine these properly (probably should've done this up above)
    for graph in ('sentiment','relevance','count'):
      ### INDIVIDUAL ENTITIES
      samples[graph] = {
        re.findall(r'(\w+_?\w+?)?/?(\w+_?\w+?(?=/\w+))',r)[0][1 if 'overall' not in r else 0].replace('_',' ').title(): samples[graph][r] for r in samples[graph]
      }

    # Dataframe dict
    # d_sentiment = { 'name1' : Series([list of values]), index=[list of times])
    #                 'name2' : Series([list of values]), index=[list of times])
    #                 'nameN' : Series([list of values]), index=[list of times])}

    time_series = {}
    for g in samples:
      time_series[g] = {}
      for r in samples[g]:
        for p in samples[g][r]:
          if r not in time_series[g]:
            time_series[g][r] = {'values': [p[1]], 'indices': [datetime.datetime.fromtimestamp((p[0] - (p[0] % 1000)) / 1000)]}
          else:
            time_series[g][r]['values'].append(p[1])
            time_series[g][r]['indices'].append(datetime.datetime.fromtimestamp((p[0] - (p[0] % 1000)) / 1000)) 

    if debug:
      print samples, '\n', time_series

    dfs = dict(zip(what_matters, [{},{},{}]))

    for ind_matter in what_matters:
      for t in time_series[ind_matter]:
        if debug:
          print 'FOR ', ind_matter, '--->', t, ':', time_series[ind_matter][t]['values'], '\n,\n',  time_series[ind_matter][t]['indices'], '\n'
        dfs[ind_matter][t] = pd.Series(time_series[ind_matter][t]['values'], index=time_series[ind_matter][t]['indices'])

    ind_matter = 'sentiment'
    #for t in time_series[ind_matter]:
    #  print 'FOR ', ind_matter, '--->', t, ':', time_series[ind_matter][t]['values'], '\n,\n',  time_series[ind_matter][t]['indices'], '\n'

    return dfs

  dfs = getKMetrics(metrics_query)

  #fig = plt.figure().add_subplot()
  #for ind_matter in what_matters:
    #DFrames[ind_matter] = pd.DataFrame(dfs[ind_matter])
  #print dfs['sentiment']
  #DFrames = {}
  #for term in dfs['sentiment']:
  #  DFrames[term] = dfs['sentiment'][term].plot()
  #  DFrames[term].set_ylabel(term.title())
  #  DFrames[term].set_ylabel('Sentiment')
  DFrames['sentiment'] = pd.DataFrame(dfs['sentiment'])
  fig = DFrames['sentiment'].plot()
    #print ind_matter, '\n--------------------------------------------\n', DFrames[ind_matter], '\n', DFrames[ind_matter].index.values, '\n#####################################################\n', DFrames[ind_matter].ix, '\n==========================================='
    #for x in DFrames[ind_matter].index.values:
    #  print x
    #  print DFrames[ind_matter].ix[x], '\n--------------------------------------------'
    #ax = DFrames[ind_matter].plot()
  #ax = DFrames['sentiment'].plot()
  #print 'DFRAME: \n', DFrames['sentiment'].transpose()
  #print '\n\nDFRAME.columns.values \n', DFrames['sentiment'].transpose().columns.values
  #print '\n\nDFRAME.ix[0] \n', DFrames['sentiment'].transpose().ix[0]
  #print '\n\nDFRAME.index \n', DFrames['sentiment'].transpose().index
  
  #print '\nDFrames VALUES: ', DFrames['sentiment'].index.values, '\n'
  plt.legend(loc='best')
  plt.show()
  exit(1)

  def animate(nframes):
    global multiplier, DFrames
    plt.cla()

    multiplier -= 1
  #  # base Kairos metrics query, must be included with every request
    metrics_query['start_absolute']  = str(int(round(time.time() * 1000)) - (int(metrics_time_back) * multiplier * 1000))
    metrics_query['end_absolute']    = str(int(round(time.time() * 1000)) - ((int(metrics_time_back) - 15) * multiplier * 1000))
  #
    dfs_new = getKMetrics(metrics_query)
  #  #for term in dfs_new['sentiment']:
  #  #  DFrames[term] = dfs_new['sentiment'][term].plot()
  #  #  DFrames[term].set_ylabel(term.title())
  #  #  DFrames[term].set_ylabel('Sentiment')
    DFrames['sentiment'] = pd.DataFrame(dfs_new['sentiment'])
  #  #print DFrames['sentiment'].transpose().ix[0], '\n'
    fig = DFrames['sentiment'].plot()
    return fig
    #plt.plot(DFrames['sentiment'].transpose().columns.values, DFrames['sentiment'].transpose().ix[nframes])
  #  DFrames['sentiment'].plot()
  #
  ani = animation.FuncAnimation(fig, animate, frames=300, interval=10, blit=False)
  plt.show()
  #DFrames['sentiment'].plot()


if __name__ == '__main__':
  try:
    import sys
    DEBUG = False
    if len(sys.argv) > 1:
      DEBUG = True
    main(DEBUG)
  except KeyboardInterrupt:
    print '\nGoodbye!'
