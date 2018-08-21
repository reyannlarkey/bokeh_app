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
						  FuncTickFormatter, SingleIntervalTicker, LinearAxis, LinearColorMapper)

from bokeh.models.widgets import (CheckboxGroup, Slider, RangeSlider,
								  Tabs, CheckboxButtonGroup,
								  TableColumn, DataTable, TextInput, Select)
import pyproj
from functools import partial
from shapely.geometry import Point
from shapely.ops import transform



def draw_maps(tgfs):

    onlyfiles = [f for f in listdir('data') if isfile(join('data', f)) and f != "useful_tgfs.txt"]
    table_source = ColumnDataSource(data  = {'TGF_ID': onlyfiles})

    columns = [
        TableColumn(field="TGF_ID", title="TGF ID")
    ]
    data_table = DataTable(source=table_source, columns=columns, width=400, height=280)

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
        tgf_src = ColumnDataSource(data = {'cluster': tgf['cluster'], 'lats': tgf_lat, 'lons':tgf_lon})

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
            data={'cluster': read_file['cluster'], 'lats': cluster_lat, 'lons': cluster_lon, 'colors': colors})

        return new_src, tgf_src, file


    def callback(attrname, old, new):
        selectionIndex = table_source.selected.indices[0]
        file = onlyfiles[selectionIndex]

        new_src, tgf_src, new_name= make_data(file, prob_thresh=float(slider.value))
        src.data.update(new_src.data)
        tgf.data.update(tgf_src.data)
        make_plot(src,tgf, title = new_name)
        p.title.text = new_name
        #print("you have selected the row nr " + str(selectionIndex), onlyfiles[selectionIndex])

    # def slider_callback(attr, old, new):
    #     new_src, new_name = make_data(file)
    #     src.data.update(new_src.data)
    #     make_plot(src, title=new_name)
    #     p.title.text = new_name

    def make_plot(src,tgf,title = ""):

        p = figure(x_axis_type="mercator", y_axis_type="mercator", match_aspect=True)
        p.add_tile(CARTODBPOSITRON)
        p.legend.visible = False
        circles_glyph = p.circle('lats', 'lons', color = 'colors', size=5, source=src, legend=False)
        tgf_glyph = p.diamond_cross('lats', 'lons', size = 20, color = 'red', source = tgf, legend = False)

        # Add the glyphs to the plot using the renderers attribute
        p.renderers.append(circles_glyph)
        p.renderers.append(tgf_glyph)
        # Hover tooltip for flight lines, assign only the line renderer
        hover_circle = HoverTool(tooltips=[('Cluster ID', '@cluster')],
                                 line_policy='next',
                                 renderers=[circles_glyph])


        # print(cluster_colors)
        # Add the hovertools to the figure

        p.add_tools(hover_circle)
        p = style(p, title)
        return p

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
    p = make_plot(src,tgf,name)
    p.title.text  = name


    slider = TextInput(value = "0.0", title = "Probability Thresh.")
    #slider = Slider(start=0, end=1.0, value=0.0, step=.01, title="Probability Thresh")
    table_source.selected.on_change('indices', callback)
    slider.on_change('value', callback)

    layout = row(column(data_table, slider), p)
    tab = Panel(child=layout, title='Data')

    return tab