from ripe.atlas.cousteau import AtlasStream
import pprint
pp = pp = pprint.PrettyPrinter(indent=4)

class Streaming(AtlasStream):
    '''Given a measurement filter and duration setting,
    begins results streaming.
    By setting a start time in the past, it can play back results in the past.
    filter setting : https://atlas.ripe.net/docs/result-streaming/'''

    def __init__(self, second=None, param):
        super(Streaming, self).__init__()
        self.duration = second
        self.param = param

    def run(self):
        self.connect()
        self.bind_channel('result', self.on_result_recieved)
        self.bind_channel('error', self.on_streaming_error)
        self.start_stream(stream_type="result", **self.stream_parameters)
        self.stream.timeout(seconds=self.seconds)
        self.stream.disconnect()

    def on_result_recieved(*args):
        """do somthing to the results"""
        print(args[0])
