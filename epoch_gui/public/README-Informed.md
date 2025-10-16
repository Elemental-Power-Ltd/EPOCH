# Informed Embed

## Running

The Informed embed is a single html file. 

This needs to be hosted by a http server (e.g. `python -m http.server`)

There are two different pages and these are determined by the query parameters.

## query parameters

### Energy Flows

Show the Energy Flow visualisation by providing a file with the `data` query parameter.

e.g. `http://localhost:8000/informed.html?data=exampleData.json`

### Site Data

Show the Input Site Data by providing a file with the `site` query parameter.

e.g. `http://localhost:8000/informed.html?site=exampleSite.json`


### Styling

`mode` (optional) - Choose a style theme, from:

- 0: Informed Colour Theme, Dark Mode
- 1: Informed Colour Theme, Light Mode
- 2: Epoch GUI Theme, Dark Mode
- 3: Epoch GUI Theme, Light Mode

For example, `http://localhost:8000/dataviz.html?data=exampleData.json&mode=0` should load the example result - assuming a server running on port 8000.

## Generating Data

Elemental Power will provide the data

- Results will be in the format `{task_id}/{portfolio_id}-{site_id}.json`.
There will be many of these. One for each site result per portfolio per task
- Sites will be in the format `{site_id}-{bundle_id}.json`
The `bundle_id` is a unique reference to a set of data. This can be found in each result response in the `hints` section.