#!/usr/bin/python

import sys
print "\n".join(sys.path)


from twython import TwythonStreamer

ckey = 'VdFYMabMVfxIWlZm7EiK81HuG'
csecret = 'od0bEKii3dDrTDsR096T0EtS80WMdpD4ncdagacbRgnqeyAJoK'
atoken = '141316512-F48JNDGbFuQNqOoEnv7PDBbe5YEKJUxJySRbAto7'
asecret = 'dQS6q0pGF7nNO6mZk0frivmvdqwSqP95DmdOIJshAEqaM'

class MyStreamer(TwythonStreamer):
    def on_success(self, data):
        if 'text' in data:
            print data['text'].encode('utf-8')
        # Want to disconnect after the first result?
        # self.disconnect()

    def on_error(self, status_code, data):
        print status_code, data

# Requires Authentication as of Twitter API v1.1
stream = MyStreamer(ckey, csecret,
                    atoken, asecret)

stream.statuses.filter(track='raptors')
#stream.user()  # Read the authenticated users home timeline (what they see on Twitter) in real-time
#stream.site(follow='twitter')