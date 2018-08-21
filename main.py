import pandas as pd
from os.path import dirname, join
from bokeh.io import output_file, show

from bokeh.io import curdoc
from bokeh.models.widgets import Tabs

from scripts.draw_clusters import draw_clusters
from scripts.draw_maps import draw_maps

# Read in the data from the data file
kwargs  = {"sep": '\t',"names": ['lat', 'lon', 'time', 'cluster', 'prob', 'outlier'], "skiprows" :1}
cluster_data = pd.read_csv(join(dirname(__file__), 'data', '100812853.txt'), **kwargs )

kwargs2  = {"sep": '\t',"names": ['lat', 'lon', 'time', 'cluster', 'prob', 'outlier'], "nrows" :1}
tgf_data = pd.read_csv(join(dirname(__file__), 'data', '100812853.txt'), **kwargs2 )

useful_tgfs = pd.read_csv(join(dirname(__file__), 'data', 'useful_tgfs.txt'))




tab1 = draw_clusters(cluster_data)
tab2 = draw_maps(useful_tgfs)

tabs = Tabs(tabs = [tab1, tab2])
#output_file("TimeVDistance.html", title = "Time Vs. Distance Plots")
curdoc().add_root(tabs)
curdoc().title = "Clustering Map"