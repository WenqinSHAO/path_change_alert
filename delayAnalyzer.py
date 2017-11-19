import math
from ripe.atlas.sagan import PingResult
from multiprocessing import Process
import Queue
import numpy as np
from rpy2.robjects.packages import importr
from rpy2.robjects.vectors import IntVector
changepoint = importr('changepoint')

# length for maximum data length for change detection
# TODO: need justification
MAX_LEN = 50



class DelayAnalyzer(Process):
    """ the process that does the data analyze, i.e. change detection

    following type of data is generated for visualization:
    mes: min RTT of a ping measurement
    loss: if min RTT is -1, all the 3 ping is regarded as lost
    alert: a change points detected
    base: baseline subtracted from data when each time performing change detection
    std: the absolute std of the data segment considered in change detection

    Attributes:
        analyze_q (multiprocessing.Queue): from where measurement data is read
        vis_q (multiprocessing.Queue): where analysis results are put for visualization
        config (multiprocessing.Manager.dict): a dict shared across processes storing configurations for analysis
    """

    def __init__(self, analyze_q, vis_q, config):
        self.analyze = analyze_q
        self.vis = vis_q
        self.config = config
        self.rec_raw = []  # the entire sagan measurement object
        self.rec_rtt = []  # only the min RTT value
        self.bias = 10
        self.minlen = 10
        super(DelayAnalyzer, self).__init__()

    def run(self):
        while True:
            # notify when analysis configuration is changed
            # TODO: the parameters need further justification
            if self.bias != self.config['bias'] or self.minlen != self.config['minlen']:
                print "{0}: Analysis setting updated!".format(self.name)
                self.bias = self.config['bias']
                self.minlen = self.config['minlen']
            try:
                mes = self.analyze.get(False)  # don't block
            except Queue.Empty:
                pass
            else:
                if mes != 'STOP':
                    id_ = mes['id']
                    mes_obj = PingResult(mes['rec'])
                    tstp_dt = mes_obj.created
                    rtt = mes_obj.rtt_min
                    if rtt > 0:
                        # update local records of valid measurements
                        self.rec_rtt.append(rtt)
                        self.rec_raw.append(mes['rec'])
                        # put valid measurements to the visualization queue
                        self.vis.put(dict(id=id_, type='mes', rec=mes['rec']))
                    else:
                        # notify lost measurements
                        self.vis.put(dict(id=id_, type='loss', rec=mes['rec']))
                    # only perform change detection when the data length is enough
                    if len(self.rec_raw) >= self.minlen:
                        # Poisson model only take integer
                        data = [int(round(i)) for i in self.rec_rtt]
                        data_len = len(data)
                        adj = 0
                        # in the case that local stored data length exceed maximum length
                        # only the lasted ones are considered
                        if data_len > MAX_LEN:
                            data = data[-MAX_LEN:]
                            adj = data_len - MAX_LEN

                        # calculated the absolute value of std regardless last three measurements
                        # where changes may reside
                        # TODO: need justification, why last three ignored
                        #data_std = np.abs(np.std(data[1:-3]))
                        data_std = np.abs(np.std(data))
                        # calculated the baseline need to be subtracted
                        # the choice of baseline
                        # TODO: need justification, why this baseline
                        data_ref = np.max(np.min(data)-math.pow(data_std, 1.5), 0)
                        data = [i-data_ref+self.bias for i in data]

                        # queuing the baseline and std
                        self.vis.put(dict(id=id, type='base', rec=dict(x=[tstp_dt], y=[data_ref - self.bias])))
                        self.vis.put(dict(id=id, type='std', rec=dict(x=[tstp_dt], y=[data_std])))

                        # turn the data into the R style vector
                        data = IntVector(data)
                        # perform changepoint analysis with the R package, using Poisson model, bayesian approach
                        cpt = changepoint.cpts(changepoint.cpt_meanvar(data, test_stat='Poisson', method='PELT'))
                        if cpt:
                            print '{0}: signaled an alert.'.format(self.name)
                            # only consider the first detected changepoint
                            # as in general there should only be one in the data
                            cpt_idx = cpt[0] + adj
                            self.vis.put(dict(id=id_, type='alert', rec=self.rec_raw[cpt_idx]))

                            # update the local measurement records
                            # let the new segment for future detection starting from the changepoint (inclusive)
                            self.rec_raw = self.rec_raw[cpt_idx:]
                            self.rec_rtt = self.rec_rtt[cpt_idx:]
                else:
                    # the playback stop signal trigger the analysis stop signal. a chain of stop signal.
                    self.vis.put('STOP')
                    return
