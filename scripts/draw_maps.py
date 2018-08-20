import pandas as pd
import numpy as np
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



def draw_maps(cluster_data):
    available_clusters = list(set(cluster_data['cluster']))
    available_clusters.sort()
    cluster_colors = linear_palette(palette = Viridis256, n = max(available_clusters)+2)
    cluster_colors.sort()

    def make_dataset(cluster_list):
        cluster_list = np.asarray(cluster_list).astype(int)
        subset = cluster_data[cluster_data['cluster'].isin(cluster_list)]

        color_dict = {carrier: color for carrier, color in zip(
            available_clusters, cluster_colors)}

        cluster_lat = []
        cluster_lon = []
        colors = []
        clusters = []
        for cluster in cluster_list:
            sub_cluster = subset[subset['cluster'] == cluster]

            for _, row in sub_cluster.iterrows():
                colors.append(color_dict[cluster])
                clusters.append(cluster)
                pnt = transform(partial(
                        pyproj.transform,
                        pyproj.Proj(init='EPSG:4326'),
                        pyproj.Proj(init='EPSG:3857')), Point(row['lon'], row['lat']))

                cluster_lat.append(pnt.x)
                cluster_lon.append(pnt.y)
        new_src = ColumnDataSource(data  = {'cluster': clusters, 'lats': cluster_lat, 'lons': cluster_lon, 'color': colors})
        return(new_src)

    def make_plot(src):

        p = figure(x_axis_type="mercator", y_axis_type="mercator",match_aspect = True)
        p.add_tile(CARTODBPOSITRON)
        p.legend.visible = False
        circles_glyph = p.circle('lats', 'lons', color='color', size=10, source=src,
                                 legend=False)
        # Add the glyphs to the plot using the renderers attribute
        p.renderers.append(circles_glyph)

        # Hover tooltip for flight lines, assign only the line renderer
        hover_circle= HoverTool(tooltips=[('Cluster ID', '@cluster'), ('lat', '@lats'), ('lon', '@lons')],
                               line_policy='next',
                               renderers=[circles_glyph])



        # Add the hovertools to the figure

        p.add_tools(hover_circle)

        p = style(p)

        return p

    # Styling
    def style(p):

        # Title
        p.title.align = 'center'
        p.title.text_font_size = '20pt'
        p.title.text_font = 'serif'

        # Axis titles
        p.xaxis.axis_label_text_font_size = '14pt'
        p.xaxis.axis_label_text_font_style = 'bold'
        p.yaxis.axis_label_text_font_size = '14pt'
        p.yaxis.axis_label_text_font_style = 'bold'

        # Tick labels
        p.xaxis.major_label_text_font_size = '12pt'
        p.yaxis.major_label_text_font_size = '12pt'

        return p

    def update(attr, old, new):
        # Find list of carriers and make a new data set
        cluster_list = [cluster_selection.labels[i] for i in cluster_selection.active]
        new_src = make_dataset(cluster_list)

        src.data.update(new_src.data)



    # CheckboxGroup to select carriers for plotting
    cluster_selection = CheckboxGroup(labels = list(np.asarray(available_clusters).astype(str)), active=list(np.arange(-1,max(available_clusters)+1,1)))
    cluster_selection.on_change('active', update)

    # Initial carriers to plot
    initial_clusters= [cluster_selection.labels[i] for i in cluster_selection.active]
    # Initial source and plot
    src = make_dataset(initial_clusters)
    #print(src.data)
    p = make_plot(src)

    # Layout setup
    layout = row(cluster_selection, p)
    tab = Panel(child=layout, title='Cluster Map')

    return tab