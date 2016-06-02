from multiprocessing import Process
from ripe.atlas.sagan import TracerouteResult
import Queue
import time


class Visual(Process):
    """
    Visualize the results in a queue
    """
    def __init__(self, report_queue):
        self.queue = report_queue
        super(Visual, self).__init__()

    def run(self):
        while True:
            try:
                task = self.queue.get(False)  # don't block the queue
            except Queue.Empty:
                time.sleep(5)
            else:
                if task != 'STOP':
                    trace_sagan = TracerouteResult(task)
                    print '{p.measurement_id:>12}:{p.probe_id} @ ' \
                          '{p.end_time}\n' \
                          '{p.last_median_rtt:6.2f}msec\n' \
                          '{p.ip_path}'.format(p=trace_sagan)
                else:
                    print '{0} received end signal.'.format(self.name)
                    return
