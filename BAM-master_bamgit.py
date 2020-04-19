from math import pi
import bokeh
from bokeh.palettes import Category20c, Spectral
from bokeh.transform import cumsum
import calendar
import datetime as DT
from datetime import datetime, date
import numpy as np
import pandas as pd
import holoviews as hv
from bokeh.plotting import show, figure, curdoc, output_file
from bokeh.models.tools import PanTool, SaveTool
from bokeh.io import output_file, show, curdoc
from bokeh.layouts import layout, widgetbox, column, row
from bokeh.models import ColumnDataSource, HoverTool, BoxZoomTool, ResetTool, PanTool, WheelZoomTool, SaveTool, LassoSelectTool
from bokeh.models import CustomJS, ColumnDataSource, Slider, DateRangeSlider, DatetimeTickFormatter
from bokeh.models.widgets import Slider, Select, TextInput, Div, DataTable, DateFormatter, TableColumn, Panel, Tabs, Toggle
from bokeh.io import output_file, show
from bokeh.models.widgets import RadioButtonGroup, Button
from bokeh.models.widgets.inputs import DatePicker
from bokeh.models.glyphs import MultiLine
import matplotlib.pyplot as plt


dfst = pd.read_csv('signals-2018-09-20.csv')
dfst.data_date = dfst.data_date.apply(lambda x:datetime.strptime(x, "%m/%d/%Y"))
aap = dfst[dfst.ticker == 'AAP']
tickers = list(dfst.ticker.unique())
source = ColumnDataSource(data=dict(x = [], t = [], s = [], ema20 = [], ema100 = [], pos = [], stlr = []))
plot = figure(plot_width=748, plot_height=405, tools = 'wheel_zoom,box_zoom,reset,save', x_axis_type="datetime", 
              title = "Signal Analysis")
plot_position = figure(plot_width=748, plot_height=225, tools = 'wheel_zoom,box_zoom,reset,save', x_axis_type="datetime", 
              title = "Trading Position")
plot_stlr = figure(plot_width=748, plot_height=630, tools = 'wheel_zoom,box_zoom,reset,save', x_axis_type="datetime",
                   title = "Cummulative Total Relative Return")
options = Select(title="Ticker", options=tickers, value="AAP")
date_from = DatePicker(title="From Date", min_date=np.min(aap.data_date), max_date=np.max(aap.data_date), value=DT.date(2015,3,20))
date_to = DatePicker(title="To Date", min_date=np.min(aap.data_date), max_date=np.max(aap.data_date), value=DT.date(2016,3,20))

##Ploting Signal
l1 = plot.line(x = 'x', y = 's', line_width = 3, source=source, color = "#3CB371", legend = "Signal")
plot.line(x = 'x', y = 'ema20', line_width = 3, source=source, color = '#FF8C00', legend = "EMA20")
plot.line(x = 'x', y = 'ema100', line_width = 3, source=source, color = "#3232FF", legend = "EMA100")
hover = HoverTool(renderers=[l1],
                  tooltips=[('Date','@x{%a %d %B}'),
                           ("Signal","@s"),
                           ("EMA20","@ema20"),
                           ("EMA100","@ema100")],
                  formatters={'x': 'datetime'}, mode='vline')

plot.add_tools(hover)
plot.legend.location = "top_left"
plot.legend.orientation = "horizontal"
plot.toolbar.logo = None
plot.xgrid.visible = False
plot.xaxis.formatter=DatetimeTickFormatter(days=["%d %b"])
plot.legend.label_text_font_size = '10px'



#Ploting Trading Position
plot_position.line(x = 'x', y = 'pos', line_width = 3, source=source, color = "#3CB371")
hover_pos = HoverTool(tooltips=[('Date','@x{%a %d %B}'),
                               ("Trading Position", "@pos")],
                  formatters={'x': 'datetime'}, mode='vline')
plot_position.add_tools(hover_pos)
plot_position.toolbar.logo = None
plot_position.xgrid.visible = False
plot_position.xaxis.formatter=DatetimeTickFormatter(days=["%d %b"])


#Ploting strategy Returns
plot_stlr.line(x = 'x', y = 'stlr', line_width = 3, source=source, color = "#3CB371")
hover_stlr = HoverTool(tooltips=[('Date','@x{%a %d %B}'),
                               ("Strategy Total Returns", "@stlr")],
                  formatters={'x': 'datetime'}, mode='vline')
plot_stlr.add_tools(hover_stlr)
plot_stlr.toolbar.logo = None
plot_stlr.xgrid.visible = False
plot_stlr.xaxis.formatter=DatetimeTickFormatter(days=["%d %b"])

def select_sessions():
    from_date = date_from.value
    to_date = date_to.value
    custom = pd.date_range(from_date, to_date)
    custom = pd.Series(custom)
    custom = custom.apply(lambda x:x.date())
    temp = dfst[
        (dfst['ticker'] == options.value)
    ]
    temp['data_date'] = temp['data_date']
    temp_ema20 = temp['signal'].ewm(span = 20).mean()
    temp_ema100 = temp['signal'].ewm(span = 100).mean()
    temp['EMA20'] = temp_ema20
    temp['EMA100'] = temp_ema100
    temp_ema = temp[['ticker', 'data_date', 'signal', 'EMA20', 'EMA100']]
    tpr = temp_ema['signal'] - temp_ema100
    tp = tpr.apply(np.sign) * 1/63
    tpf = tp.shift(1)
    temp_ema['Trading Position'] = tpf
    aret = temp_ema['signal'].diff()
    strat_rt = tpf * aret
    strat_rt = strat_rt.cumsum() * 100
    temp_ema['Strategy Total Returns'] = strat_rt
    selected = temp_ema[
        temp_ema['data_date'].isin(custom)
    ]
    return selected
def update():
    df = select_sessions()
    plot.xaxis.axis_label = 'Date' 
    plot.yaxis.axis_label = 'Signal for ' + str(options.value)
    plot_position.xaxis.axis_label = 'Date' 
    plot_position.yaxis.axis_label = 'Trading Position'
    plot_stlr.xaxis.axis_label = 'Date' 
    plot_stlr.yaxis.axis_label = 'Total Relative Return (%)'
    source.data = dict(
        x=df['data_date'],
        t=df['ticker'],
        s=df['signal'],
        ema20=df['EMA20'],
        ema100=df['EMA100'],
        pos=df['Trading Position'],
        stlr=df['Strategy Total Returns']
    )

controls = [options, date_from, date_to]
for control in controls:
    control.on_change('value', lambda attr, old, new: update())
    
div1 = Div(text = """<html>
   <head>
      <style type="text/css">
         body {
            padding: 0in; 
         }
         .square {
         position: relative;
            background-color: #0B4478;
            width: 1500px;
            height: 80px;
            border: 0px;
         }
         .square p{
          font-size:30pt;
          margin: 0;
          background: #0B4478;
          position: relative;
          top: 20%;
          left: -30%;
          text-align: center;
          margin:auto;
          padding:0;
          height:5%;
          font-family:Helvetica;
          color:white;
      width:65%;
      transform: translate(50%, 50%)   
         }
      </style>
   </head>
   <body>
      <div class="square">
      <p>Balyasny Asset Management Analytics Dashboard</p></div>
   </body>
</html>""")
inputs = row(*controls)
layout = column(children = [div1, inputs, row([column([plot, plot_position]), plot_stlr])], sizing_mode="fixed")
curdoc().add_root(layout)
curdoc().title = "BAM Analytics Application"