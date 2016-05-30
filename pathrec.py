from ripe.atlas.cousteau import AtlasResultsRequest


class PathRec(object):
    def __init__(self, query):
        if query:
            is_success, res = AtlasResultsRequest(**query).create()
            if is_success:
                self.pattern = self.learnpattern(res)
        else:
            self.pattern = {}

    def update(self):
        '''given a measurement, update pattern'''

    def learnpattern(self):
        '''given a historical records, learn pattern'''


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


