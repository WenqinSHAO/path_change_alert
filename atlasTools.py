import json
import requests
requests.packages.urllib3.disable_warnings()
import time
import calendar
import matplotlib.dates as mdates
import numpy as np
from ripe.atlas.cousteau import AtlasStream
from ripe.atlas.cousteau import AtlasResultsRequest
from ripe.atlas.sagan import TracerouteResult

def query(url):
    #params = {"key": key}
    headers = {"Accept": "application/json"}
    results = requests.get(url=url, headers=headers)
    if results.status_code == 200:
        return results
    else:
        return False


def queryID(pb_id):
    url = "https://atlas.ripe.net/api/v1/probe/?id__in=%d" % int(pb_id)
    return query(url)


def readPingJSON(file):
    at_raw = json.load(open(file, 'r'))
    at_prob_rtt = {}
    for mes in at_raw:
        prob_id = mes['prb_id']
        if prob_id not in at_prob_rtt:
            at_prob_rtt[prob_id] = {'src_ip': mes['from'],
                                    'time_md': [],
                                    'avg': [],
                                    'min':[],
                                    'max':[],
                                    'loss':[],
                                    'time_epc':[]}
        epoch_time = mes['timestamp']
        at_prob_rtt[prob_id]['time_epc'].append(epoch_time)
        utc_string = time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(epoch_time))
        mdate_time = mdates.strpdate2num('%Y-%m-%d %H:%M:%S')(utc_string)
        at_prob_rtt[prob_id]['time_md'].append(mdate_time)
        at_prob_rtt[prob_id]['min'].append(float(round(mes['min'])))
        at_prob_rtt[prob_id]['avg'].append(float(round(mes['avg'])))
        at_prob_rtt[prob_id]['max'].append(float(round(mes['max'])))
        if mes['sent'] == 0:
            at_prob_rtt[prob_id]['loss'].append(100)
        else:
            at_prob_rtt[prob_id]['loss'].append((1-float(mes['rcvd'])/mes['sent'])*100)
    return at_prob_rtt


def readTraceJSON(file):
    at_raw = json.load(open(file, 'r'))
    at_prob_rtt = {}
    for mes in at_raw:
        prob_id = mes['prb_id']
        if prob_id not in at_prob_rtt:
            at_prob_rtt[prob_id] = {'time_md':[],
                                    'time_epc':[],
                                    'min':[],
                                    'avg':[],
                                    'max':[],
                                    'ip_path':[],
                                    'paris_id':[]}
        epoch_time = mes['timestamp']
        at_prob_rtt[prob_id]['time_epc'].append(epoch_time)
        utc_string = time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(epoch_time))
        mdate_time = mdates.strpdate2num('%Y-%m-%d %H:%M:%S')(utc_string)
        at_prob_rtt[prob_id]['time_md'].append(mdate_time)
        at_prob_rtt[prob_id]['paris_id'].append(mes['paris_id'])
        min_ = []
        avg_ = []
        max_ = []
        path_ =[]
        for hop in mes['result']:
            res_rtt = []
            hop_ip = ''
            if 'result' in hop:
                for try_ in hop['result']:
                    if ('rtt' in try_) and ('err' not in try_):
                        res_rtt.append(try_['rtt'])
                        hop_ip = try_['from']
                if res_rtt:
                    min_.append(np.min(res_rtt))
                    avg_.append(np.mean(res_rtt))
                    max_.append(np.max(res_rtt))
                    path_.append(hop_ip)
                else:
                    min_.append(-1)
                    avg_.append(-1)
                    max_.append(-1)
                    path_.append('*')
            else:
                min_.append(-1)
                avg_.append(-1)
                max_.append(-1)
                path_.append('*')
        at_prob_rtt[prob_id]['min'].append(min_)
        at_prob_rtt[prob_id]['avg'].append(avg_)
        at_prob_rtt[prob_id]['max'].append(max_)
        at_prob_rtt[prob_id]['ip_path'].append(path_)
    return at_prob_rtt

# TODO: think about using ripe.atlas.sagan, maybe it's an overkill
def traceFormatter(res_json):
    '''Given a json object containing multiple traceroute measurements,
    reture a list of dictionary.
    The order of elements is the same as the json obj.
    Each element of the list, a dictionary, correspond to one measurement.'''
    # suppose there is only one unique tuple of msm and prb id in json obj
    res_list = []
    for rec in res_json:
        rec_dict = {'endtime': rec['endtime'],
                    'paris_id': rec['paris_id']}
        path=[]
        if 'result' in rec.keys() and rec['result']:
            for hop in rec['result']:
                if not 'result' in hop.keys():
                    path.append('*')
                else:
                    hop_s = set()
                    for trail in hop['result']:
                        if 'from' in trail.keys():
                            if trail['from'] != '*':
                                hop_s.add(trail['from'])
                    if hop_s: # only valid IP in hop_s
                        if len(hop_s) > 1:
                            print "ALERT: different hops observed in one trace meas."
                            pp.pprint(rec)
                        # in the case more than one possible hop are observed, an arbitray one is considered
                        # TODO: handle multiple different IPs in one hop
                        path.append(hop_s.pop())
                    else:
                        path.append('*')
        rec_dict['ip_path'] = path
        res_list.append(rec_dict)
    return res_list

def IPPathPattern(res_list):
    '''Given a list of IP paths,
    output forwarding patterns that span more than 16 measurements'''
    subLen = 16
    # hashing
    paris_id = []
    ip_path = []
    for rec in res_list:
        paris_id.append(rec['paris_id'])
        ip_path.append(hash(str(rec['ip_path'])))
    # segment
    tLen = len(paris_id)
    seg = [subLen-1,]


    # adjust
    # split
