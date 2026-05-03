# FOURSIGHT Dashboard

This repository contains the authority dashboard developed by Team FOURSIGHT for the Mass Evacuation challenge in [Geospatial Challenge Camp 2026](https://challenge-camp.geoportti.fi/en/latest/)

Our team solution is **Game-based Participatory Data Collection for Evacuation Planning**. The overall solution has two connected parts:

1. A game for citizens
2. A dashboard for authorities built on the data collected from the game

This repository is for the **dashboard** part of the solution.

Please check the deployed dashboard [HERE](https://gcc2026-foursight-dashboard.streamlit.app/) in Streamlit with the password: `2026`.

Note: The data used in this dashboard is fake data only for demonstration.

## Project Purpose

The dashboard helps authorities explore and interpret behavioral data collected through the  game. It is designed to support emergency planning by showing how players respond to evacuation-related decisions, how those responses relate to behavioral dimensions, and how patterns vary across locations and respondent groups.

## What The Dashboard Includes

The Streamlit dashboard provides several views for authority users:

1. Personality overview of respondents
2. Player profile information, including demographics, municipality, household characteristics, and evacuation experience
3. Question-by-question response patterns with authority-focused interpretation
4. Behavioral insights across dimensions, including comparison and correlation views



## Repository Structure

Key files in this repository:

1. `dashboard.py` - main Streamlit dashboard application
2. `municipality_population_and_coords.py` - municipality metadata used in map and rate visualizations
3. `requirements.txt` - Python dependencies
4. `data/final/` - final dashboard input data

## Requirements

The project currently depends on:

1. `streamlit`
2. `pandas`
3. `plotly`
4. `matplotlib`
5. `wordcloud`

## How To Run Locally

1. Create and activate a Python environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the dashboard:

```bash
streamlit run dashboard.py
```

4. Open the local Streamlit URL shown in the terminal.


## Team

Team FOURSIGHT

Geospatial Challenge Camp 2026
