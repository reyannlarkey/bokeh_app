### contents of app.py

from bokeh.client import push_session
from bokeh.embed import server_document, autoload_static
from bokeh.plotting import figure, curdoc
from bokeh.resources import CDN

plot = figure()
plot.circle([1,2], [3,4])

doc = curdoc()
doc.add_root(plot)
tag = server_document(url = 'http://localhost:5006/serverTest') # or whatever the location of the server process is.
print(tag)