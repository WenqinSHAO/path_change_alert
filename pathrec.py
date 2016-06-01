from ripe.atlas.cousteau import AtlasResultsRequest
from ripe.atlas.sagan import TracerouteResult
from multiprocessing import Process
import time
from util import learn_pattern


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
                self.pattern = learn_pattern(res)
        else:
            self.pattern = []
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




