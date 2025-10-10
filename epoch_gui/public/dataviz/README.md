# Informed Data Vizualisation Embed

## Running

The DataViz embed is a single html file. 

This needs to be hosted by a http server (e.g. `python -m http.server`)

### query parameters

`result` (required) - the filepath to a simulation result, relative to the http server. 

`mode` (optional) - Choose a style theme, from:

- 0: Informed Colour Theme, Dark Mode
- 1: Informed Colour Theme, Light Mode
- 2: Epoch GUI Theme, Dark Mode
- 3: Epoch GUI Theme, Light Mode

For example, `http://localhost:8000/dataviz.html?data=dataviz/example.json&mode=0` should load the example result - assuming a server running on port 8000.

## Generating Data

Elemental Power will provide results in the format `{result_id}.json`.
There will be many of these. One for each site result per portfolio per task