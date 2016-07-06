from multiprocessing import Process
from ripe.atlas.sagan import PingResult
from bokeh.plotting import curdoc, figure
from bokeh.models import ColumnDataSource
from bokeh.client import push_session
import Queue


class Visual(Process):
    """
    Visualize the results in a queue
    """
    def __init__(self, vis_q):
        self.vis = vis_q
        self.mes = ColumnDataSource(dict(x=[], y=[]))
        self.alert = ColumnDataSource(dict(x=[], y=[]))
        self.p = figure(width=1200, height=800, x_axis_type="datetime", title='Streaming demo',
                        tools="xpan,xwheel_zoom,xbox_zoom,reset")
        self.p.border_fill_color = "whitesmoke"
        self.p.min_border_left = 80
        self.p.line(x='x', y='y', source=self.mes)
        self.p.circle(x='x', y='y', source=self.mes, fill_color="white", size=8)
        self.p.square(x='x', y='y', source=self.alert, line_color="orange", fill_color='red', size=10)
        self.p.xaxis.axis_label = 'Time'
        self.p.yaxis.axis_label = 'RTT (ms)'
        self.doc = curdoc()
        self.session = push_session(self.doc)
        self.doc.add_root(self.p)
        self.doc.add_periodic_callback(self.update, 500)
        self.doc.title = "Streaming demo"
        self.session.show()
        self.session.loop_until_closed()  # if not add, nothing will show on the screen, yet if added, process can not be joined...
        super(Visual, self).__init__()

    def update(self):
        try:
            task = self.vis.get(False)
        except Queue.Empty:
            pass
        else:
            if task != 'STOP':
                print 'BOKEH received new data.'
                mes = PingResult(task['rec'])
                new_data = dict(x=[mes.created], y=[mes.rtt_min])
                if task['type'] == 'mes':
                    self.mes.stream(new_data)
                elif task['type'] == 'alert':
                    self.alert.stream(new_data)
            else:
                print 'BOKEH received STOP signal.'
                self.session.close()

