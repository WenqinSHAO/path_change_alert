from ripe.atlas.cousteau import AtlasStream
from multiprocessing import Process


class Streaming(Process):
    """
    Given a measurement filter and duration setting,
    begins results streaming.
    By setting a start time in the past, it can play back results in the past.
    filter setting : https://atlas.ripe.net/docs/result-streaming/
    Streaming results are put into a queue.
    """

    def __init__(self, queue, second=None, param={}):
        self.duration = second
        self.param = param
        self.queue = queue
        self.stream = AtlasStream()
        super(Streaming, self).__init__()

    def run(self):
        self.stream.connect()
        self.stream.bind_channel('result', self.on_result_recieved)
        self.stream.start_stream(stream_type="result", **self.param)
        self.stream.timeout(seconds=self.duration)
        self.stream.disconnect()
        self.queue.put('STOP')
        return

    def on_result_recieved(self, *args):
        self.queue.put(args[0])
