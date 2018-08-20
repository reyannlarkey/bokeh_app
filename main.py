import pandas as pd
from os.path import dirname, join
from bokeh.io import output_file, show

from bokeh.io import curdoc
from bokeh.models.widgets import Tabs

from scripts.draw_clusters import draw_clusters

# Read in the data from the data file
kwargs  = {"sep": '\t',"names": ['lat', 'lon', 'time', 'cluster', 'prob', 'outlier'], "skiprows" :1}
cluster_data = pd.read_csv(join(dirname(__file__), 'data', '100812853.txt'), **kwargs )

kwargs2  = {"sep": '\t',"names": ['lat', 'lon', 'time', 'cluster', 'prob', 'outlier'], "nrows" :1}
tgf_data = pd.read_csv(join(dirname(__file__), 'data', '100812853.txt'), **kwargs2 )

tab1 = draw_clusters(cluster_data)

tabs = Tabs(tabs = [tab1])
#output_file("TimeVDistance.html", title = "Time Vs. Distance Plots")
curdoc().add_root(tabs)