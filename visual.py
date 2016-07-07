from multiprocessing import Process
from ripe.atlas.sagan import PingResult
from bokeh.plotting import curdoc, figure
from bokeh.models import ColumnDataSource, Slider
from bokeh.layouts import row, column
from bokeh.client import push_session
import Queue


class Visual(Process):
    """
    Visualize the results in a queue
    """
    def __init__(self, vis_q, config):
        self.vis = vis_q
        self.mes = ColumnDataSource(dict(x=[], y=[]))
        self.alert = ColumnDataSource(dict(x=[], y=[]))
        self.loss = ColumnDataSource(dict(x=[], y=[]))
        self.base = ColumnDataSource(dict(x=[], y=[]))
        self.rec = []
        self.p = figure(width=600, height=400, x_axis_type="datetime", title='Streaming demo',
                        tools="xpan,xwheel_zoom,xbox_zoom,reset")
        self.p.border_fill_color = "whitesmoke"
        self.p.min_border_left = 80
        self.p.line(x='x', y='y', source=self.mes)
        self.p.circle(x='x', y='y', source=self.mes, fill_color="white", size=8)
        self.p.square(x='x', y='y', source=self.alert, line_color="orange", fill_color='red', size=10, line_width=3)
        self.p.circle(x='x', y='y', source=self.loss, fill_color="grey", size=8, line_color='black', line_width=3)
        self.p.line(x='x', y='y', source=self.base, line_color='green', line_width=3, alpha=0.5)
        self.p.xaxis.axis_label = 'Time'
        self.p.yaxis.axis_label = 'RTT (ms)'
        self.bias = Slider(title="RTT bias (ms)", value=10, start=0, end=50, step=1)
        self.minlen = Slider(title="Minimum data length", value=10, start=4, end=50, step=1)
        self.config = config
        self.config['bias'] = self.bias.value
        self.config['minlen'] = self.minlen.value
        self.doc = curdoc()
        self.session = push_session(self.doc)
        self.doc.add_root(column(row(self.bias, self.minlen), self.p))
        self.doc.add_periodic_callback(self.update, 500)
        self.doc.title = "Streaming demo"
        self.session.show()
        self.session.loop_until_closed()  # if not add, nothing will show on the screen, yet if added, process can not be joined...
        super(Visual, self).__init__()

    def update(self):
        self.config['bias'] = self.bias.value
        self.config['minlen'] = self.minlen.value
        try:
            task = self.vis.get(False)
        except Queue.Empty:
            pass
        else:
            if task != 'STOP':
                print 'BOKEH received new data.'
                if task['type'] == 'base':
                    self.base.stream(task['rec'])
                else:
                    mes = PingResult(task['rec'])
                    new_data = dict(x=[mes.created], y=[mes.rtt_min])
                    if task['type'] == 'mes':
                        self.rec.append(mes.rtt_min)
                        self.mes.stream(new_data)
                    elif task['type'] == 'alert':
                        self.alert.stream(new_data)
                    elif task['type'] == 'loss':
                        if self.rec:
                            new_data['y'] = [self.rec[-1]]
                        else:
                            new_data['y'] = [20]
                        self.loss.stream(new_data)
            else:
                print 'BOKEH received STOP signal.'
                self.session.close()

