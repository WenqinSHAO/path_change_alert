#import asyncio
#import docopt
import ipaddress
import json
import pprint
#import multiprocessing
#import redis
import time
#from collections import defaultdict
from ripe.atlas.cousteau import AtlasStream
from ripe.atlas.cousteau import AtlasResultsRequest
#from ripe.atlas.sagan import TracerouteResult
import altasTools as at
# for debug only
pp = pprint.PrettyPrinter(indent=4)

def on_result_recieved(*args):
    """do somthing to the results"""
    pp.pprint(args[0])

def stream_results(seconds=None, filters={}):
    """Set up the atlas stream for all playback results"""
    atlas_stream = AtlasStream()
    atlas_stream.connect()
    atlas_stream.bind_channel('result', on_result_recieved)
    stream_parameters = {}
    stream_parameters.update(filters)
    pp.pprint(stream_parameters)
    atlas_stream.start_stream(stream_type="result", **stream_parameters)
    atlas_stream.timeout(seconds=seconds)
    atlas_stream.disconnect()

if __name__ == '__main__':
    now = time.time()
    # identify one single traceroute measurement
    msm = 5010
    prb = 24460
    query = {"msm_id": msm, "probe_ids": [prb,], "start": int(now-25*3600), "stop": int(now-24*3600)}
    # fetch the historical records of the given traceroute
    is_success, res = AtlasResultsRequest(**query).create()
    if is_success:
       hist_path = at.traceFormatter(res)
       pattern = at.IPPathPattern(hist_path)
    # construct path pattern (id->IP path)

    '''
    # playback parameter, to fake fast streaming
    plybk = {"msm": msm,
             "prb": prb,
             "startTime": int(now-24*3600),
             "speed": 100}
    print "Playback"
    stream_results(filters=plybk)
    '''
    #now = time.time()
    #url = "https://atlas.ripe.net/api/v2/measurements/5006/results?start=%d&stop=%d&probe_ids=%d&format=json" \
    #      % (now-24*3600, now, 10772)
    #res = at.query(url)
    #f = open('offline.json', 'w')
    #f.write(res.text)
    #f.close()
