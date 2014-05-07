import numpy as np
import matplotlib
matplotlib.use('TKAgg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import timeit, random

# global scoping
frequencies = []
start = 0
clock = timeit.default_timer

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

def animate(arg, rects):
  global frequencies, start, clock
  frameno, frequencies = arg
  for rect, f in zip(rects, frequencies):
      rect.set_height(f)
  print("FPS: {:.2f}".format(frameno / (clock() - start))) 

def step():
  global frequencies
  for frame, bin_idx in enumerate(np.linspace(0,1000000,100000000), 1):
    #Here we just change the first bin, so it increases through the animation.
    frequencies[random.randint(0,len(frequencies)-1 if len(frequencies) > 1 else 0)] = bin_idx
    yield frame, frequencies

def main():
  global frequencies, start
  start = clock()
  import re

  time_back = '86400'
  units     = 'seconds'

  check_interval = '5'

  ###
  # querying from KairosDB --- https://code.google.com/p/kairosdb/wiki/[QueryMetrics|QueryMetricTags]
  #
  # will need to find from QueryMetricTags which tags each metric we get back has...
  # then do some work on aggregation of those

  """
  'tags'    : {
    'start_absolute(m)'  : 'int',
    'end_absolute(m)'    : 'int',
    'metrics(m)'         : {
      'name(m)'  : 'string',
      'tags(m)'  : {
        'tagname': [
          'string'
        ]
      }
    }
  }
  """

  #what KairosDB puts in itself
  base_metricnames  = ["kairosdb.datastore.query_collisions","kairosdb.datastore.write_size","kairosdb.jvm.free_memory","kairosdb.jvm.max_memory","kairosdb.jvm.thread_count","kairosdb.jvm.total_memory","kairosdb.protocol.http_request_count","kairosdb.protocol.telnet_request_count"]
  base_tagnames     = ["buffer","host","method"]
  base_tagvalues    = ["data_points","ip-10-63-16-84","metricnames","put","row_key_index","string_index","tagnames","tags","tagvalues","version"]

  # open up Kairos and figure out what we have...
  metricnames = [m for m in getKairos('metricnames').json()['results'] if "/" in m and m not in base_metricnames]
  #print metricnames, '\n'
  tagnames = [t for t in getKairos('tagnames').json()['results'] if t not in base_tagnames]
  #print tagnames, '\n'
  tagvalues = [tv for tv in getKairos('tagvalues').json()['results'] if tv not in base_tagvalues]
  #print tagvalues, '\n'
  print("FINISHING KAIROS IN {:.2f}".format(clock()-start))

  # the starting point of a KairosDB tags query
  tags_query = {
    'start_relative'  : {
      'value' : '86400',
      'unit'  : units
    },    
  }

  metrics_to_find = raw_input('Metrics to look for (comma separated): ').strip()
  metrics_in_tags_query = []

  # find ANYTHING from Kairos with sentiment/relevance relating to what is being asked for
  for findme in [f for f in metrics_to_find.split(',')]:
    # only look for specific sentiment OR relevance
    for lookupvalue in ('sentiment','relevance'):
      for tag in [t for t in tagvalues if re.match(r"((\w+_)+)?(\w+/)?(\w+)?" + findme + "(_?(\w+)?)/(\w+/)?((\w+)?_?)" + lookupvalue, t)]:
        metrics_in_tags_query.append(
          {
            'name'  : tag
          }
        )

  tags_query['metrics'] = metrics_in_tags_query

  # here for printing purposes only
  import json,simplejson

  start = clock()
  all_available = queryKairos('tags',tags_query).json()
  print("FINISHING queryingForSpecific Tags IN {:.2f}".format(clock()-start))
  #print simplejson.dumps(all_available,indent=2)
  all_results = []
  for i in range(0,len(all_available['queries'])):
    all_results += all_available['queries'][i]['results']

  # this gets us all the metrics and tags available that match our request
  ##  SET THIS UP TO STEP!!!  need to yield results from this
  metrics_tags_available = {ar['name'] : ar['tags'] for ar in all_results}
  print metrics_tags_available

  """
    'metrics' : {
    'start_absolute(m)'  : 'int',
    'end_absolute(m)'    : 'int',
    'cache_time(o)'      : 'int',
    'metrics(m)'         : {
      'tags(m)': {
          'tagnames(m)'  : [
            'string'
            ],
      },
      'name(m)'          : 'string',
      'aggregators(o)'   : [
        {
          'name(m)'      : 'avg|dev|div:divisor|percentile|least_squares|max|min|rate:unit|sum',
          'sampling(o)'    : {
            'value'     : 'int',
            'unit'      : 'milliseconds|seconds|minutes|hours|days|weeks|months|years'
          },
          'div:divisor' : 'int',
          'rate:unit'   : 'milliseconds|seconds|minutes|hours|days|weeks|months|years'
        }
      ],
      'group_by(o)'      : [
        {
          'name'            : ['tag:tags|time:range_size&group_count|value:range_size'],
          'tag:tags'        : [
            'string'
          ],
          'time:range_size'  : {
            'value'     : 'int',
            'unit'      : 'string'
          },
          'time:group_count': 'int',
          'value:range_size': {
              'name'        : 'string',
              'range_size'  : 'int'
          }
        }
      ]
  }
  """

  metrics_query = {
    'start_relative'  : {
      'value' : '86400',
      'unit'  : units
    },    
  }

  aggregators = [
    {
      "name": "sum",
      "sampling": {
        "value": check_interval,
        "unit": units
      }
    }
  ]

  metrics_to_batch = []
  for m_names in metrics_tags_available:
    metrics_to_batch.append({
        'tags'  : metrics_tags_available[m_names],
        'name'  : m_names,
        'aggregators' : aggregators
    })

  metrics_query['metrics'] = metrics_to_batch

  start = clock()
  metrics_to_plot = queryKairos('metrics',metrics_query).json()['queries']
  #print simplejson.dumps(metrics_to_plot, indent=2)
  print("FINISHING queryingForSpecific Metrics IN {:.2f}".format(clock()-start))

  samples = {}
  # the time series of all sentiment related to the requested keyword
  for rez in [r['results'] for r in metrics_to_plot if int(r['sample_size'])]:
    for result in [rez[i] for i in range(0,len(rez)) if 'sentiment' in rez[i]['name']]:
      samples[result['name']] = result['values']

  print samples
  start = clock()

  fig, ax = plt.subplots()

  alphab = [s for s in samples]
  #alphab = [ar['name'] for ar in all_results]
  print alphab
  exit(1)

  #['Raptors', 'Nets', 'Kidd', 'Casey', 'Toronto', 'Brooklyn', 'Penis', 'Vagina', 'KG', 'KLow', '2Pat']
  frequencies = [100 for i in range(0,len(alphab))]

  pos = np.arange(len(alphab))
  width = 1.0     # gives histogram aspect to the bar diagram
  ax.set_xticks(pos + (width / 2))
  ax.set_xticklabels(alphab)

  rects = plt.bar(pos, frequencies, width, color='r')
  ani = animation.FuncAnimation(fig, animate, step, interval=10,
                              repeat=False, blit=False, fargs=(rects,))
  plt.show()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print '\nGoodbye!'

