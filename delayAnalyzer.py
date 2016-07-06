from ripe.atlas.sagan import PingResult
from multiprocessing import Process
import Queue
import time
import numpy as np


class DelayAnalyzer(Process):
    def __init__(self, analyze_q, vis_q):
        self.analyze = analyze_q
        self.vis = vis_q
        self.rec = []
        super(DelayAnalyzer, self).__init__()

    def run(self):
        while True:
            try:
                mes = self.analyze.get(False)  # don't block
            except Queue.Empty:
                time.sleep(5)
            else:
                if mes != 'STOP':
                    print '{0} received mes data.'.format(self.name)
                    id_ = mes['id']
                    rtt = PingResult(mes['rec']).rtt_min
                    self.rec.append(rtt)
                    if len(self.rec) > 4:
                        last_four = self.rec[-5:-1]
                        if rtt > 1.2 * np.median(last_four):
                            print '{0} signaled an alert.'.format(self.name)
                            self.vis.put(dict(id=id_, type='alert', rec=mes['rec']))
                else:
                    print '{0} received end signal.'.format(self.name)
                    self.vis.put('STOP')
                    return
