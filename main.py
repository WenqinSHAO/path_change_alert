import time
import calendar
from fastplayback import Fastplayback
from delayAnalyzer import DelayAnalyzer
from multiprocessing import Queue, Manager
from ripe.atlas.sagan import PingResult
from bokeh.plotting import curdoc, figure
from bokeh.models import ColumnDataSource, Slider, Div, HoverTool, Range1d
from bokeh.layouts import row, column
import Queue as NQ
from os.path import dirname, join
import datetime
import pytz

epoch = datetime.datetime.utcfromtimestamp(0)
epoch = epoch.replace(tzinfo=pytz.UTC)


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


def datetime_to_string(dt):
    return datetime.datetime.strftime(dt, "%Y-%m-%d %H:%M:%S %Z")


def datetime_to_epoch(dt):
    return (dt-epoch).total_seconds()


def update():
    analyze_setting['bias'] = bias.value
    analyze_setting['minlen'] = minlen.value

    try:
        task = vis_q.get(False)
    except NQ.Empty:
        pass
    else:
        if task != 'STOP':
            if task['type'] == 'base':
                base.stream(dict(x=task['rec']['x'], y=task['rec']['y'], time=[datetime_to_string(i) for i in task['rec']['x']]))
            else:
                one_mes = PingResult(task['rec'])
                new_data = dict(x=[one_mes.created], y=[one_mes.rtt_min], time=[datetime_to_string(one_mes.created)])
                if task['type'] == 'mes':
                    rec.append(one_mes.rtt_min)
                    tstp.append(one_mes.created)
                    mes.stream(new_data)
                    #if len(tstp) <= 15:
                        #p.x_range = Range1d(datetime_to_epoch(tstp[0])*1000, datetime_to_epoch(tstp[0]+datetime.timedelta(seconds=3600*2))*1000)
                    #    p.y_range = Range1d(200, 300)
                    #else:
                        #p.x_range = Range1d(datetime_to_epoch(tstp[-15])*1000, datetime_to_epoch(tstp[0]+datetime.timedelta(seconds=3600*2))*1000)
                    #    p.y_range = Range1d(10, 20)
                elif task['type'] == 'alert':
                    alert.stream(new_data)
                elif task['type'] == 'loss':
                    if rec:
                        new_data['y'] = [rec[-1]]
                    else:
                        new_data['y'] = [20]
                        loss.stream(new_data)
        else:
            print 'BOKEH: received STOP signal.'

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

mes = ColumnDataSource(dict(x=[], y=[], time=[]))
alert = ColumnDataSource(dict(x=[], y=[], time=[]))
loss = ColumnDataSource(dict(x=[], y=[], time=[]))
base = ColumnDataSource(dict(x=[], y=[], time=[]))
rec = []
tstp = []

desc = Div(text=open(join(dirname(__file__), "des.html")).read(), width=800)

hover = HoverTool(tooltips=[("RTT", "@y"), ("Time", "@time")])

p = figure(width=600, height=400, x_axis_type="datetime", title="probe %d -- msm %d" % (mes_list[0][1], mes_list[0][0]),
           tools="xpan,xwheel_zoom,xbox_zoom,reset")
p.add_tools(hover)

p.border_fill_color = "whitesmoke"
p.min_border_left = 80
p.line(x='x', y='y', source=mes)
p.circle(x='x', y='y', source=mes, fill_color="white", size=8)
p.square(x='x', y='y', source=alert, line_color="orange", fill_color='red', size=10, line_width=3)
p.circle(x='x', y='y', source=loss, fill_color="grey", size=8, line_color='black', line_width=3)
p.line(x='x', y='y', source=base, line_color='green', line_width=3, alpha=0.5)
p.xaxis.axis_label = 'Time'
p.yaxis.axis_label = 'RTT (ms)'
#p.x_range = Range1d(string_to_epoch('20/01/2016 06:00:00')*1000, string_to_epoch('25/01/2016 06:00:00')*1000)



bias = Slider(title="RTT bias (ms)", value=10, start=0, end=50, step=1)
minlen = Slider(title="Minimum data length", value=10, start=4, end=50, step=1)
analyze_setting['bias'] = bias.value
analyze_setting['minlen'] = minlen.value

doc = curdoc()
doc.add_root(column(desc, row(bias, minlen), p))
doc.add_periodic_callback(update, 500)
doc.title = "RTT Streaming"

#for st, ana in mes_worker:
#    st.join()
#    ana.join()



