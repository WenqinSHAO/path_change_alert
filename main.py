import time
import calendar
from fastplayback import Fastplayback
from delayAnalyzer import DelayAnalyzer
from multiprocessing import Queue, Manager
from ripe.atlas.sagan import PingResult
from bokeh.plotting import curdoc, figure
from bokeh.models import ColumnDataSource, Slider, Div, HoverTool, Range1d, LinearAxis
from bokeh.layouts import row, column
import Queue as NQ
from os.path import dirname, join
import datetime
import pytz

# TODO: process can not be joined, need a better structure of the whole program.
# in the master branch and the fastplayback brach, the boken is wrapped in a process,
# and the run func knows to end when receives the "STOP" signal
# how every there is problem pass the context is bokeh doc
# TODO: the plotting canvas figure axis range can not be be auto adjusted to have a sliding fixed size window.
# the boken ColumnDataSrouce does have a sliding window feature allowing only a fixed number of data
# it shall work when each ColumnDataSource has the same length, which is not the case there...

# utcfromtimestamp produces a datatime object without time zone info
# used in datetime_to_epoch function
epoch = datetime.datetime.utcfromtimestamp(0)
epoch = epoch.replace(tzinfo=pytz.UTC)


def string_to_epoch(str):
    """ translate an UTC time string to epoch time

    Args:
        str (string): a string describing a UTC time in format '%d/%m/%Y %H:%M:%S', french style, chic

    Returns:
        int, seconds since the epoch

    Notes:
        Can raise ValueError if the input str has wrong format
    """
    return int(calendar.timegm(time.strptime(str, '%d/%m/%Y %H:%M:%S')))


def datetime_to_string(dt):
    """ translate a python datetime object into a readable string
    Args:
        dt (datetime): a datetime object

    Returns:
        string, a formatted string for date, time, and time zone
    """
    return datetime.datetime.strftime(dt, "%Y-%m-%d %H:%M:%S %Z")


def datetime_to_epoch(dt):
    """ translate a python datetime object to seconds since epoch

    Args:
        dt (datetime): a datetime object

    Returns:
        int, seconds since epoch
    """
    return (dt-epoch).total_seconds()


def update():
    """ the periodic callback function for data visualisation with bokeh """

    # update the analysis setting from bokeh Slider inputs
    # analyze_setting is a multiprocessing.dict object, for inter-process communication
    analyze_setting['bias'] = bias.value
    analyze_setting['minlen'] = minlen.value

    # read the queue for visualization
    try:
        task = vis_q.get(False)
    except NQ.Empty:
        pass
    else:
        if task != 'STOP':
            # update baseline for change detection
            if task['type'] == 'base':
                base.stream(dict(x=task['rec']['x'], y=task['rec']['y'],
                                 time=[datetime_to_string(i) for i in task['rec']['x']]))
            # update the data standard variation
            elif task['type'] == 'std':
                pass
                #std.stream(dict(x=task['rec']['x'], y=task['rec']['y'],
                #                time=[datetime_to_string(i) for i in task['rec']['x']]))
            else:
                # for the rest of the case, in task['rec'] resides a sagan measurement object, thus treated differently
                one_mes = PingResult(task['rec'])
                new_data = dict(x=[one_mes.created], y=[one_mes.rtt_min], time=[datetime_to_string(one_mes.created)])
                # update measurements
                if task['type'] == 'mes':
                    rec.append(one_mes.rtt_min)
                    tstp.append(one_mes.created)
                    mes.stream(new_data)
                # update detected change point
                elif task['type'] == 'alert':
                    alert.stream(new_data)
                # update if a measurement loss is found
                elif task['type'] == 'loss':
                    if rec:
                        new_data['y'] = [rec[-1]]
                    else:
                        new_data['y'] = [20]
                        loss.stream(new_data)
        else:
            print 'BOKEH: received STOP signal %r.' % task

# queue where data for visualization is put
vis_q = Queue()
# queue where date for analyze (change detection) is put
analyze_q = Queue()
# dict storing detection settings share between Analyzer and Boken callback
analyze_setting = Manager().dict(bias=20, minlen=10)

# measurement query for fastplayback
start = string_to_epoch('18/10/2016 06:00:00')
end = string_to_epoch('18/10/2016 14:00:00')
#mes_list = [(1010, 11037)]
mes_list = [(1010, 27711)]

mes_worker = []

for mes in mes_list:
    param = dict(msm_id=mes[0],
                 probe_ids=[mes[1]],
                 start=start,
                 stop=end)
    # make the query, and feed data into the queue for analysis
    streamer = Fastplayback(analyze_q=analyze_q, interval=.5, query=param)
    streamer.start()
    # read data from analysis queue, analyze them, and put result in visualization queue
    analyzer = DelayAnalyzer(vis_q=vis_q, analyze_q=analyze_q, config=analyze_setting)
    analyzer.start()
    mes_worker.append((streamer, analyzer))

# bokeh data structure for streaming data updating
mes = ColumnDataSource(dict(x=[], y=[], time=[]))
alert = ColumnDataSource(dict(x=[], y=[], time=[]))
loss = ColumnDataSource(dict(x=[], y=[], time=[]))
base = ColumnDataSource(dict(x=[], y=[], time=[]))
#std = ColumnDataSource(dict(x=[], y=[], time=[]))
# local copy for measurement data, updated in bokeh call back
rec = []
tstp = []

# description text
desc = Div(text=open(join(dirname(__file__), "des.html")).read(), width=800)

# hover tool
hover = HoverTool(tooltips=[("RTT", "@y"), ("Time", "@time")])

# bohek plotting canvas config
p = figure(width=1000, height=400, x_axis_type="datetime", title="probe %d -- msm %d" % (mes_list[0][1], mes_list[0][0]),
           tools="pan, xpan, ypan, xwheel_zoom, ywheel_zoom, undo, redo, reset, save", toolbar_location="above")
p.add_tools(hover)
p.border_fill_color = "whitesmoke"
p.min_border_left = 80
p.min_border_right = 80

# plotting aesthetic for different type of data in the visualization queue
p.line(x='x', y='y', source=mes)
p.circle(x='x', y='y', source=mes, fill_color="white", size=8)
p.square(x='x', y='y', source=alert, line_color="orange", fill_color='red', size=10, line_width=3)
p.circle(x='x', y='y', source=loss, fill_color="grey", size=8, line_color='black', line_width=3)
p.line(x='x', y='y', source=base, line_color='green', line_width=3, alpha=0.5)

p.xaxis.axis_label = 'Time'
p.yaxis.axis_label = 'RTT (ms)'

# add a secondary axis for data absolute std
#p.extra_y_ranges = {"y_bis": Range1d(start=-2, end=20)}
#p.add_layout(LinearAxis(y_range_name="y_bis", axis_label="abs std (ms)"), 'right')
#p.line(x='x', y='y', source=std, line_color='grey', line_width=3, alpha=0.5, y_range_name='y_bis')


# bokeh slider tools for getting bias and data minimum length settings
bias = Slider(title="RTT bias (ms)", value=40, start=0, end=100, step=5)
minlen = Slider(title="Minimum data length", value=10, start=4, end=50, step=1)
analyze_setting['bias'] = bias.value
analyze_setting['minlen'] = minlen.value

# assemble everything
doc = curdoc()
doc.add_root(column(desc, row(bias, minlen), p))
doc.add_periodic_callback(update, 50)
doc.title = "RTT Streaming"



