from ripe.atlas.sagan import PingResult
from multiprocessing import Process
import Queue
import time
import numpy as np
from rpy2.robjects.packages import importr
from rpy2.robjects.vectors import IntVector
changepoint = importr('changepoint')


class DelayAnalyzer(Process):
    def __init__(self, analyze_q, vis_q, config):
        self.analyze = analyze_q
        self.vis = vis_q
        self.config = config
        self.rec_raw = []
        self.rec_rtt = []
        self.baseline = 9999
        self.bias = 10
        self.minlen = 10
        super(DelayAnalyzer, self).__init__()

    def run(self):
        while True:
            if self.bias != self.config['bias'] or self.minlen != self.config['minlen']:
                print "{0}: Analysis setting updated!".format(self.name)
                self.bias = self.config['bias']
                self.minlen = self.config['minlen']
            try:
                mes = self.analyze.get(False)  # don't block
            except Queue.Empty:
                time.sleep(.1)
            else:
                if mes != 'STOP':
                    id_ = mes['id']
                    mes_obj = PingResult(mes['rec'])
                    tstp_dt = mes_obj.created
                    rtt = mes_obj.rtt_min
                    if rtt > 0:
                        self.rec_rtt.append(rtt)
                        self.rec_raw.append(mes['rec'])
                        self.vis.put(dict(id=id_, type='mes', rec=mes['rec']))
                    else:
                        self.vis.put(dict(id=id_, type='loss', rec=mes['rec']))
                    if len(self.rec_raw) >= self.minlen:
                        data = [int(round(i)) for i in self.rec_rtt]
                        data_min = min(np.min(data), self.baseline)
                        self.baseline = data_min
                        data = [i-data_min+self.bias for i in data]
                        self.vis.put(dict(id=id, type='base', rec=dict(x=[tstp_dt], y=[data_min-self.bias])))
                        data = IntVector(data)
                        cpt = changepoint.cpts(changepoint.cpt_meanvar(data, test_stat='Poisson', method='PELT'))
                        if cpt:
                            print '{0}: signaled an alert.'.format(self.name)
                            self.vis.put(dict(id=id_, type='alert', rec=self.rec_raw[cpt[0]+1]))
                            self.rec_raw = self.rec_raw[cpt[0]+1:]
                            self.rec_rtt = self.rec_rtt[cpt[0]+1:]
                else:
                    #print '{0} received end signal.'.format(self.name)
                    self.vis.put('STOP')
                    return
