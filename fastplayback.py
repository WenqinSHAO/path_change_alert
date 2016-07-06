from ripe.atlas.cousteau import AtlasResultsRequest
from multiprocessing import Process
import time


class Fastplayback(Process):
    def __init__(self, vis_q, analyze_q, query, interval=1):
        self.id = (query['msm_id'], query['probe_ids'])
        self.vis = vis_q
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
        if self.rec:
            for mes in self.rec:
                self.analyze.put(dict(id=self.id, rec=mes))
                time.sleep(self.interval)
        self.analyze.put('STOP')
        return
