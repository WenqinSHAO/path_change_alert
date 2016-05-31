from ripe.atlas.cousteau import AtlasResultsRequest
from ripe.atlas.sagan import TracerouteResult
from multiprocessing import Process
import time


class PathRec(Process):
    """
    If a query is provided when initiating the obj,
    hist path records are quryied to construct the major path patterns.
    The process reads from a queue the streaming result and then:
    1/ update the path pattern structure;
    2/ detect path pattern change.
    """
    def __init__(self, mes_queue, report_queue, query={}):
        if query:
            is_success, res = AtlasResultsRequest(**query).create()
            if is_success:
                self.pattern = self.learn_pattern(res)
        else:
            self.pattern = {}
        self.mes_queue = mes_queue
        self.report_queue = report_queue
        super(PathRec, self).__init__()

    def run(self):
        while True:
            if self.mes_queue.empty():
                time.sleep(1)
            else:
                mes = self.mes_queue.get()
                if mes != 'STOP':
                    self.update(mes)
                    self.detect()
                else:
                    print '{0} received end signal.'.format(self.name)
                    self.report_queue.put('STOP')
                    return

    def detect(self):
        """given a measurement, detect if it is a change"""
        last_rec = self.pattern[-1]
        if last_rec.last_median_rtt > 100:
            self.report_queue.put(last_rec)

    def update(self, mes):
        """given a measurement, update pattern"""
        self.pattern.append(TracerouteResult(mes))

    def learn_pattern(self, mes):
        """given a historical records, learn pattern"""
        return self.trace_formatter(mes)

    @staticmethod
    def trace_formatter(res_json):
        res_list = []
        for rec in res_json:
            rec_sagan = TracerouteResult(rec)
            res_list.append(rec_sagan)
        return res_list

    @staticmethod
    def trace_formatter_old(res_json):
        """Given a json object containing multiple traceroute measurements,
        reture a list of dictionary.
        The order of elements is the same as the json obj.
        Each element of the list, a dictionary, correspond to one measurement."""
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


