# Epoch GUI

The web-based frontend for the Elemental Power services.

## Development

Requires Node.js 18+

- install dependencies with `npm install`
- run with `npm run dev`

The Gui can then be accessed on localhost:8760


## Building

Releases are built using GitHub actions and stored in our GitHub container registry. 

To build a local copy, run `docker compose build` from within the docker subdirectory

In docker, we serve the gui on port 80.

## Tools

This GUI is built using React and TypeScript. 

- We use a combination of React Router and Zustand for state management, favouring React Router when it is possible to represent the state of a page in url parameters.

- For visual components, we generally use Material UI (MUI)
- Graphs use plotly.js


## Networking

When deployed, we serve the gui using NGINX.

Api requests prefixed with `/api/optimisation` and `/api/data` are proxied to the appropriate backend service. This is mapped through the templated `nginx.conf.template`.

In development, `vite.config.ts` replicates this behaviour.
