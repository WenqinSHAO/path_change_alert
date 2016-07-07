import time
import calendar
from fastplayback import Fastplayback
from delayAnalyzer import DelayAnalyzer
from multiprocessing import Queue, Manager
from ripe.atlas.sagan import PingResult
from bokeh.plotting import curdoc, figure
from bokeh.models import ColumnDataSource, Slider
from bokeh.layouts import row, column
import Queue as NQ

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


def update():
    analyze_setting['bais'] = bias.value
    analyze_setting['minlen'] = minlen.value
    try:
        task = vis_q.get(False)
    except NQ.Empty:
        pass
    else:
        if task != 'STOP':
            print 'BOKEH received new data.'
            if task['type'] == 'base':
                base.stream(task['rec'])
            else:
                one_mes = PingResult(task['rec'])
                new_data = dict(x=[one_mes.created], y=[one_mes.rtt_min])
                if task['type'] == 'mes':
                    rec.append(one_mes.rtt_min)
                    mes.stream(new_data)
                elif task['type'] == 'alert':
                    alert.stream(new_data)
                elif task['type'] == 'loss':
                    if rec:
                        new_data['y'] = [rec[-1]]
                    else:
                        new_data['y'] = [20]
                        loss.stream(new_data)
        else:
            print 'BOKEH received STOP signal.'

vis_q = Queue()
analyze_q = Queue()
analyze_setting = Manager().dict(bias=10, minlen=10)

start = string_to_epoch('20/01/2016 06:00:00')
end = string_to_epoch('27/01/2016 06:00:00')
mes_list = [(1010, 10772)]
mes_worker = []

for mes in mes_list:
    param = dict(msm_id=mes[0],
                 probe_ids=[mes[1]],
                 start=start,
                 stop=end)
    streamer = Fastplayback(vis_q=vis_q, analyze_q=analyze_q, interval=1, query=param)
    streamer.start()
    analyzer = DelayAnalyzer(vis_q=vis_q, analyze_q=analyze_q, config=analyze_setting)
    analyzer.start()
    mes_worker.append((streamer, analyzer))

mes = ColumnDataSource(dict(x=[], y=[]))
alert = ColumnDataSource(dict(x=[], y=[]))
loss = ColumnDataSource(dict(x=[], y=[]))
base = ColumnDataSource(dict(x=[], y=[]))
rec = []

p = figure(width=600, height=400, x_axis_type="datetime", title='Streaming demo',
           tools="xpan,xwheel_zoom,xbox_zoom,reset")
p.border_fill_color = "whitesmoke"
p.min_border_left = 80
p.line(x='x', y='y', source=mes)
p.circle(x='x', y='y', source=mes, fill_color="white", size=8)
p.square(x='x', y='y', source=alert, line_color="orange", fill_color='red', size=10, line_width=3)
p.circle(x='x', y='y', source=loss, fill_color="grey", size=8, line_color='black', line_width=3)
p.line(x='x', y='y', source=base, line_color='green', line_width=3, alpha=0.5)
p.xaxis.axis_label = 'Time'
p.yaxis.axis_label = 'RTT (ms)'

bias = Slider(title="RTT bias (ms)", value=10, start=0, end=50, step=1)
minlen = Slider(title="Minimum data length", value=10, start=4, end=50, step=1)
analyze_setting['bias'] = bias.value
analyze_setting['minlen'] = minlen.value

doc = curdoc()
doc.add_root(column(row(bias, minlen), p))
doc.add_periodic_callback(update, 500)
doc.title = "Streaming Demo"

#for st, ana in mes_worker:
#    st.join()
#    ana.join()



