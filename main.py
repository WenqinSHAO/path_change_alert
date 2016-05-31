import time
from streaming import Streaming
from pathrec import PathRec
from visual import Visual
from multiprocessing import Queue


def main():
    now = time.time()
    mes_list = [(5010, 24460)]
    mes_worker = []
    rep_q = Queue()

    for mes in mes_list:
        mes_q = Queue()
        param = {"msm": mes[0],
                 "prb": mes[1],
                 "startTime": int(now - 24 * 3600),
                 "speed": 100}
        streamer = Streaming(queue=mes_q, param=param)
        streamer.start()
        query = {"msm_id": mes[0],
                 "probe_ids": [mes[1]],
                 "start": int(now-48*3600),
                 "stop": int(now-24*3600)}
        analyzer = PathRec(mes_queue=mes_q, report_queue=rep_q, query=query)
        analyzer.start()
        mes_worker.append((streamer, analyzer))

    reporter = Visual(report_queue=rep_q)
    reporter.start()

    for st, ana in mes_worker:
        st.join()
        ana.join()

    reporter.join()

    return

if __name__ == '__main__':
    main()

