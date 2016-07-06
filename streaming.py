from ripe.atlas.cousteau import AtlasStream
from multiprocessing import Process


class Streaming(Process):
    """Wraps AtlasStream in a process.

    Given a measurement filter and duration setting,
    begins results streaming.
    By setting a start time in the past, it can play back results in the past.
    filter setting : https://atlas.ripe.net/docs/result-streaming/
    Streaming results are put into a queue.

    Attributes:
        duration (int): how long the streaming shall last, if None, it will last forever.
        param (dict): the filters for streaming.
        queue (multiprocessing.Queue): the queue to which streaming results are written.
        stream (ripe.atlas.cousteau.AtlasStream): the stuff does the real streaming job.
    """

    def __init__(self, vis_q, analyze_q, second=None, param={}):
        """
        Args:
            duration (int): how long the streaming shall last, if None, it will last forever.
            param (dict): the filters for streaming.
            queue (multiprocessing.Queue): the queue to which streaming results are written.
        """
        self.duration = second
        self.param = param
        self.id = (param['msm'], param['prb'])
        self.vis = vis_q
        self.analyze = analyze_q
        self.stream = AtlasStream()
        super(Streaming, self).__init__()

    def run(self):
        """What should be doing when the process is started.
        """
        self.stream.connect()
        self.stream.bind_channel('result', self.on_result_recieved)
        self.stream.start_stream(stream_type="result", **self.param)
        self.stream.timeout(seconds=self.duration)
        self.stream.disconnect()
        self.analyze.put('STOP')
        return

    def on_result_recieved(self, *args):
        """Put the received streaming result to queue.

        Args:
            *args: args[0] contains the right json object as per RIPE documentation.
        """
        print '{0} received streaming data.'.format(self.name)
        self.vis.put(dict(id=self.id, type='mes', rec=args[0]))
        self.analyze.put(dict(id=self.id, rec=args[0]))
