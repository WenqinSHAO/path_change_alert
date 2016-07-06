import time
import calendar
from streaming import Streaming
from fastplayback import Fastplayback
from delayAnalyzer import DelayAnalyzer
from visual import Visual
from multiprocessing import Queue


def string_to_epoch(str):
    """translate an UTC time string to epoch time

    Args:
        str (string): a string describing a UTC time in format '%d/%m/%Y %H:%M:%S', french style, chic

    Returns:
        int, seconds since the epoch

    Notes:
        Can raise ValueError if the input str has wrong format
    """
    return int(calendar.timegm(time.strptime(str, '%d/%m/%Y %H:%M:%S')))


def main():
    vis_q = Queue()
    analyze_q = Queue()

    start = string_to_epoch('20/01/2016 06:00:00')
    end = string_to_epoch('20/02/2016 06:00:00')
    mes_list = [(1010, 10772)]
    mes_worker = []

    for mes in mes_list:
        param = dict(msm_id=mes[0],
                     probe_ids=[mes[1]],
                     start=start,
                     stop=end)
        streamer = Fastplayback(vis_q=vis_q, analyze_q=analyze_q, interval=1, query=param)
        streamer.start()
        analyzer = DelayAnalyzer(vis_q=vis_q, analyze_q=analyze_q)
        analyzer.start()
        mes_worker.append((streamer, analyzer))

    reporter = Visual(vis_q=vis_q)
    reporter.start()

    for st, ana in mes_worker:
        st.join()
        ana.join()

    reporter.join()

    return

if __name__ == '__main__':
    main()

