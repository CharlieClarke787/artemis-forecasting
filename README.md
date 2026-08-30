# Artemis Forecasting

A personal geopolitical and sanctions forecasting system that tracks predictions and scores them against reality.

Most forecasting is easy to do and hard to evaluate. Artemis was built to fix that: it logs predictions with a stated probability and rationale, scores resolved forecasts using the Brier score (the standard method used in professional forecasting), and checks calibration — whether forecasts made at, say, 70% confidence actually come true about 70% of the time. It also imports questions from [Good Judgment Open](https://www.gjopen.com/), a public forecasting tournament, so individual predictions can be benchmarked against community consensus rather than judged in isolation.

## Features

- **Forecast logging** — record predictions with probability, rationale, and forecaster name; update before resolution.
- **Scoring & calibration** — Brier score, win rate, and decile-based calibration analysis, visualised with Chart.js.
- **Good Judgment Open integration** — bulk-import live GJO questions across economics, markets, and geopolitics; batch-forecast tooling; track community consensus for direct comparison.
- **Multi-forecaster leaderboard** — compare performance across forecasters by win rate and Brier score.
- **Data export** — CSV export for external analysis; automated timestamped backups.
- **Desktop packaging** — runs as a one-click desktop app via `launcher.bat`, despite being a local web app under the hood.

## Stack

Python + SQLite backend, HTML/CSS/JavaScript frontend, Chart.js for visualisation.

## Getting started

```bash
python setup_db.py       # creates the local database
python add_forecast.py   # log a new forecast
python view_dashboard.py # generates dashboard.html from your local data
```

Open `dashboard.html` in a browser to see your results.

To pull in Good Judgment Open questions:

```bash
python import_gjo.py
python quick_forecast_gjo.py
```

## Note on this repo

`forecasts.db`, `dashboard.html`, and exported CSVs are excluded from version control (see `.gitignore`) since they contain personal forecast data. Running the scripts above will generate your own local copies. Google Drive backup (`backup_to_gdrive.py`) requires your own `credentials.json` from the [Google Cloud Console](https://console.cloud.google.com/) — this is never included in the repo and should never be committed.

## Background

Built independently, starting from a minimal command-line tool and evolving through six phases into a full-stack application with analytics, Good Judgment Open integration, and packaged desktop deployment. See the project report for the full methodology and development process.
