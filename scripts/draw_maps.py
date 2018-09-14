import pandas as pd
import numpy as np
from os import listdir
from os.path import isfile, join
from bokeh.layouts import column, row, WidgetBox
from bokeh.palettes import Viridis256, linear_palette
from bokeh.plotting import figure
from bokeh.tile_providers import CARTODBPOSITRON
from bokeh.models.annotations import Title
from bokeh.models import (CategoricalColorMapper, HoverTool,
						  ColumnDataSource, Panel,
						  FuncTickFormatter, SingleIntervalTicker, LinearAxis, LinearColorMapper, LassoSelectTool)

from bokeh.models.widgets import (CheckboxGroup, Slider, RangeSlider,
								  Tabs, CheckboxButtonGroup,
								  TableColumn, DataTable, TextInput, Select)
import pyproj
from functools import partial
from shapely.geometry import Point
from shapely.ops import transform

from bokeh.models.renderers import GlyphRenderer
count = 0
def draw_maps(tgfs):

    onlyfiles = [f for f in listdir('data') if isfile(join('data', f)) and f != "useful_tgfs.txt"]
    onlyfiles.sort()
    table_source = ColumnDataSource(data  = {'TGF_ID': onlyfiles})

    columns = [
        TableColumn(field="TGF_ID", title="TGF ID")
    ]
    data_table = DataTable(source=table_source, columns=columns, width=200, height=500)

    def make_data(file, prob_thresh = 0.9):
        kwargs = {"sep": '\t', "names": ['lat', 'lon', 'time', 'cluster', 'prob', 'outlier'], "skiprows": 1}
        read_file = pd.read_csv("data/" + file, **kwargs)

        kwargs2 = {"sep": '\t', "names": ['lat', 'lon', 'time', 'cluster', 'prob', 'outlier'], "nrows": 1}
        tgf  = pd.read_csv("data/"+file, **kwargs2)

        tgf_lat = []
        tgf_lon = []
        tgfpnt = transform(partial(
                pyproj.transform,
                pyproj.Proj(init='EPSG:4326'),
                pyproj.Proj(init='EPSG:3857')), Point(tgf['lon'], tgf['lat']))
        tgf_lat.append(tgfpnt.x)
        tgf_lon.append(tgfpnt.y)
        tgf_time = tgf['time']
        tgf_src = ColumnDataSource(data = {'cluster': tgf['cluster'], 'lats': tgf_lat, 'lons':tgf_lon, 'times': tgf_time})

        cluster_colors = linear_palette(palette=Viridis256, n=len(set(read_file['cluster'])))
        read_file = read_file[read_file['prob']>=prob_thresh]
        cluster_lat = []
        cluster_lon = []

        colors = []
        for _, row in read_file.iterrows():
            pnt = transform(partial(
                pyproj.transform,
                pyproj.Proj(init='EPSG:4326'),
                pyproj.Proj(init='EPSG:3857')), Point(row['lon'], row['lat']))
            cluster_lat.append(pnt.x)
            cluster_lon.append(pnt.y)
            colors.append(cluster_colors[int(row['cluster'])])


        new_src = ColumnDataSource(
            data={'cluster': read_file['cluster'], 'lats': cluster_lat, 'lons': cluster_lon, 'colors': colors, 'times': read_file['time']})

        return new_src, tgf_src, file


    def callback(attrname, old, new):
        selectionIndex = table_source.selected.indices[0]
        file = onlyfiles[selectionIndex]

        new_src, tgf_src, new_name= make_data(file, prob_thresh=float(slider.value))
        src.data.update(new_src.data)
        tgf.data.update(tgf_src.data)
        make_plot(src,tgf, title = new_name)
        p.title.text = new_name




    def make_plot(src,tgf,title = ""):
        Npt = len(src.data['times'])
        global count
        count = len(src.data['times'])
        p = figure(x_axis_type="mercator", y_axis_type="mercator", match_aspect=True,
                   tools="pan, wheel_zoom,reset, save,lasso_select,box_select", active_drag="lasso_select", plot_width = 500, plot_height = 500)


        p.add_tile(CARTODBPOSITRON)
        p.legend.visible = False
        circles_glyph = p.circle('lats', 'lons', color = 'colors', size=5, source=src, legend=False, hover_fill_alpha=0.5)
        tgf_glyph = p.diamond_cross('lats', 'lons', size = 20, color = 'red', source = tgf, legend = False, hover_fill_alpha=0.1)

        # Add the glyphs to the plot using the renderers attribute
        p.renderers.append(circles_glyph)
        p.renderers.append(tgf_glyph)
        # Hover tooltip for flight lines, assign only the line renderer
        hover_circle = HoverTool(tooltips=[('Cluster ID', '@cluster'), ('Time', '@times')],
                                 line_policy='next',
                                 renderers=[circles_glyph])


        fig2 = figure(title="simple line example", x_axis_label='x', y_axis_label='y', x_axis_type = "log", plot_width = 500, plot_height = 500)
        new_dts = ColumnDataSource(data = {'dts':[]})
        bins = []
        print(len(fig2.renderers))
        def make_histogram(attrname, old, new):
            fig2.renderers = fig2.renderers[0:5]
                # fig2.renderers.pop(-1)

            #print("indicies are: ", np.array(old['1d']['indices']))
            inds = np.array(new['1d']['indices'])


            if count == 0:
                c = 0
            else:
                c = count - Npt
            print(src.data['times'][inds+c+1])
            #hhist1, _ = np.histogram(src['lats'][inds], bins=100)
            #selectionIndex = src.data['lats']
            ts = []

            ts = src.data['times'][inds+c+1]
            dts = np.diff(ts)
            hist,bins = np.histogram(dts, bins = np.logspace(0,2.778, 50))
            # new_data = ColumnDataSource(data={'dts': hist})
            # new_dts.data.update(new_data.data)
            line = fig2.line(bins[0:-1], hist)
            circ = fig2.circle(bins[0:-1], hist)
            fig2.renderers.append(line)
            fig2.renderers.append(circ)

        circles_glyph.data_source.on_change('selected', make_histogram)


        # print(cluster_colors)
        # Add the hovertools to the figure

        p.add_tools(hover_circle)
        p = style(p, title)
        return p, fig2



    def style(p, name = ""):

        # Title
        p.title.align = 'center'
        p.title.text_font_size = '20pt'
        p.title.text_font = 'arial'

        # Axis titles
        p.xaxis.axis_label_text_font_size = '14pt'
        p.xaxis.axis_label_text_font_style = 'bold'
        p.yaxis.axis_label_text_font_size = '14pt'
        p.yaxis.axis_label_text_font_style = 'bold'

        # Tick labels
        p.xaxis.major_label_text_font_size = '12pt'
        p.yaxis.major_label_text_font_size = '12pt'


        return p

    initial_file = onlyfiles[0]
    src, tgf, name = make_data(initial_file)
    p, fig2 = make_plot(src,tgf,name)
    p.title.text  = name

    #src.data_source.on_change('selected', make_histogram)


    slider = TextInput(value = "0.0", title = "Probability Thresh.")

    table_source.selected.on_change('indices', callback)
    slider.on_change('value', callback)


    layout = row(column(data_table, slider), p,fig2)
    tab = Panel(child=layout, title='Data')
    p.select(LassoSelectTool).select_every_mousemove = False
    return tab