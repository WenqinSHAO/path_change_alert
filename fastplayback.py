from ripe.atlas.cousteau import AtlasResultsRequest
from multiprocessing import Process
import time


class Fastplayback(Process):
    """ generates streaming measurement data

    while playing back measurements in the past,
    the streaming function (ripe.altals.cousteau) is not very reliable,
    and has great limit in streaming speed,
    and hence this class to accelerate the playback of past measurements.
    it query entire the data for a given period first,
    and then playback each measurement one by one according to given interval.

    Attributes:
    analyze_q (multiprocessing.Queue): where measurements is put one by one; an analysis process consumes the queue;
    query (dict): a dictionary contains query parameters
    interval (float): streaming interval between two measurements
    """
    def __init__(self, analyze_q, query, interval=1.0):
        self.id = (query['msm_id'], query['probe_ids'])
        self.analyze = analyze_q
        self.interval = interval
        self.rec = []
        is_success, results = AtlasResultsRequest(**query).create()
        if is_success:
            self.rec = results
        else:
            print "Result query failed!"

        super(Fastplayback, self).__init__()

    def run(self):
        """ if query successful, put the fetched measurements one by one into the analysis queue"""
        if self.rec:
            for mes in self.rec:
                self.analyze.put(dict(id=self.id, rec=mes))
                time.sleep(self.interval)
        self.analyze.put('STOP')
        return
