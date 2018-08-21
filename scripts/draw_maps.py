import pandas as pd
import numpy as np
from os import listdir
from os.path import isfile, join
from bokeh.layouts import column, row, WidgetBox
from bokeh.palettes import Viridis256, linear_palette
from bokeh.plotting import figure
from bokeh.tile_providers import CARTODBPOSITRON
from bokeh.models import (CategoricalColorMapper, HoverTool,
						  ColumnDataSource, Panel,
						  FuncTickFormatter, SingleIntervalTicker, LinearAxis, LinearColorMapper)

from bokeh.models.widgets import (CheckboxGroup, Slider, RangeSlider,
								  Tabs, CheckboxButtonGroup,
								  TableColumn, DataTable, Select)
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

    def make_data(file):
        kwargs = {"sep": '\t', "names": ['lat', 'lon', 'time', 'cluster', 'prob', 'outlier'], "skiprows": 1}
        read_file = pd.read_csv("data/" + file, **kwargs)

        cluster_lat = []
        cluster_lon = []
        for _, row in read_file.iterrows():
            pnt = transform(partial(
                pyproj.transform,
                pyproj.Proj(init='EPSG:4326'),
                pyproj.Proj(init='EPSG:3857')), Point(row['lon'], row['lat']))
            cluster_lat.append(pnt.x)
            cluster_lon.append(pnt.y)
        new_src = ColumnDataSource(
            data={'cluster': read_file['cluster'], 'lats': cluster_lat, 'lons': cluster_lon})

        return new_src


    def callback(attrname, old, new):
        selectionIndex = table_source.selected.indices[0]
        file = onlyfiles[selectionIndex]
        new_src = make_data(file)
        src.data.update(new_src.data)
        make_plot(src)
        #print("you have selected the row nr " + str(selectionIndex), onlyfiles[selectionIndex])


    def make_plot(src):
        p = figure(x_axis_type="mercator", y_axis_type="mercator", match_aspect=True)
        p.add_tile(CARTODBPOSITRON)
        p.legend.visible = False
        circles_glyph = p.circle('lats', 'lons', size=10, source=src,
                                 legend=False)
        # Add the glyphs to the plot using the renderers attribute
        p.renderers.append(circles_glyph)

        # Hover tooltip for flight lines, assign only the line renderer
        hover_circle = HoverTool(tooltips=[('Cluster ID', '@cluster'), ('lat', '@lats'), ('lon', '@lons')],
                                 line_policy='next',
                                 renderers=[circles_glyph])

        # Add the hovertools to the figure

        p.add_tools(hover_circle)

        return p

    initial_file = onlyfiles[0]
    src = make_data(initial_file)
    p = make_plot(src)
    table_source.selected.on_change('indices', callback)


    layout = row(data_table, p)
    tab = Panel(child=layout, title='Data')

    return tab