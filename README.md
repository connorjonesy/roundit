# Roundit

#### Has this ever happened to you?

lorem ipsum. :)

# Have you ever crossed an intersection and felt unsafe. Yeah. Us too. 

### Welcome to roundit. We imagine a world in which intersections are removed, and in their place, roundabouts rule the world. Pedestrians can cross safely, cars are forced to slow down, drivers focus more, cyclists remain unscathed. 

[Translink's 2040 Transportation Plan](https://vancouver.ca/files/cov/transportation-2040-plan.pdf) aims to create zero traffic related fatalities, we want to aid in that effort. 

Roundabouts have been proven to significantly reduce intersection collisions around the world. They help keep every type of road user safe. 

Our goal was to identify intersections with high collision rates and help determine which of them could benefit from being redesigned as roundabouts. By making collision data more accessible, we hope to encourage safer and more informed urban planning decisions in Vancouver. 

#### Contributing Notes

### Dev environemnt

* serve the backend with uvicorn: `uvicorn main:app --reload`

* serve the frontend with vite: 

`npm install`

`npm run dev`


INGEST is run locally, not part of our deployment, ingest requirements are local only 

# requirements-ingest.txt

To Ingest that crap locally, use a virtual environment

```
python3 -m venv .venv-ingest
source .venv-ingest/bin/activate
pip install -r requirements-ingest.txt
```
# How does it work?

We ingest and update our DB in the ingest directory (Follow the respective README)

The frontend will query our web service to retrieve necessary data.

(At the moment, we have pulled in Vancouver data to live in the frontend. But we can remove this at anytime and only rely on the render postgres DB)

### PROD

* render backend (postgres db and web service)
* vercel frontend

