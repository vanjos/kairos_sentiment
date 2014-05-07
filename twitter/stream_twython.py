#!/usr/bin/python

import sys
print "\n".join(sys.path)


from twython import TwythonStreamer

### PUT IN YOUR TWITTER APP API KEYS ###
ckey = "YOUR CONSUMER KEY"
csecret = "YOUR CONSUMER SECRET"
atoken = "YOUR ACCESS TOKEN"
asecret = "YOUR ACCESS SECRET"

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
