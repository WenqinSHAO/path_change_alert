import time
from streaming import Streaming
from pathrec import PathRec

if __name__ == '__main__':
    now = time.time()
    # identify one single traceroute measurement
    msm = 5010
    prb = 24460
    query = {"msm_id": msm, "probe_ids": [prb,], "start": int(now-48*3600), "stop": int(now-24*3600)}
    path = PathRec(query)

    # playback parameter, to fake fast streaming
    plybk = {"msm": msm,
             "prb": prb,
             "startTime": int(now-24*3600),
             "speed": 100}
    print "Playback"
    result_stream = Streaming(plybk)

