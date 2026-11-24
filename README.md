# DineDiscover

Cuisine-based restaurant discovery for Halifax. Search and filter restaurants, read category ratings (taste, service, authenticity, value), save favorites, compare up to three places side by side, and build personal Top 5 lists that roll into a community ranking.

Built for an HCI course: a polished, accessible interface on a lightweight stack (Flask + SQLite + plain HTML/CSS/JS). The UI is styled to look like shadcn/ui without React or a build step.

## Features

- Search by cuisine and neighbourhood; filter by rating, price, dietary needs and distance; sort results
- Restaurant detail pages with photos, category rating bars and reviews
- Category-based reviews with validation and confirmation before delete
- Favorites with undo
- Side-by-side comparison (up to 3) with “Best” highlights
- Personal Top 5 per cuisine (arrow buttons + drag-and-drop) and Community Top 5 (Borda scoring)
- Real sign-up / log-in with hashed passwords
- Light / dark theme, responsive layout, keyboard-accessible UI (WCAG 2.2 AA target)

## Requirements

- Python 3.10+ (developed on 3.14)
- A modern browser

## Setup

```bash
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Run

```bash
flask --app app run --debug
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). The first launch creates `instance/dinediscover.db` and loads the Halifax restaurant data automatically.

### Optional commands

```bash
# Recreate the database and reseed
flask --app app seed-db

# Or
python seed.py

# Show the component styleguide at /styleguide
set DINEDISCOVER_STYLEGUIDE=1          # Windows PowerShell: $env:DINEDISCOVER_STYLEGUIDE="1"
flask --app app run --debug
```

## Demo accounts

Password for every demo user: `dinediscover`

| Username | Notes |
|----------|--------|
| `priya`  | Has an Indian Top 5 |
| `sofia`  | Ranked several cuisines |
| `liam`   | Good for a quieter starting point |

You can also create a new account from **Sign up**.

## Restaurant data

- 48 real, independent Halifax-area restaurants, hand-picked and checked in November 2026: places like Great Wall, King of Donair, The Bicycle Thief, Buta Ramen, Cha Baa Thai and The Five Fishermen. No chains, closed places or duplicates.
- Addresses, coordinates, phones, websites and (where known) hours were cross-checked against [OpenStreetMap](https://www.openstreetmap.org/copyright) and public listings. Hours change, so call ahead.
- 8 cuisines: Indian, Italian, Japanese, Chinese, Mexican, Thai, Middle Eastern (including Halifax donair), Seafood
- Neighbourhoods: Downtown Halifax, North End, South End, West End, Dartmouth, Bedford, Clayton Park
- Distance is measured from the neighbourhood you pick (not GPS)
- Dietary tags are a best guess from menus; confirm allergies with the restaurant
- Photos are representative Unsplash images by cuisine. Member reviews and Top 5 rankings are generated sample content.
- Edit the list in `scripts/build_seed_data.py`, then run `python scripts/build_seed_data.py` and `python seed.py`. `scripts/fetch_halifax.py` pulls raw OSM data, which is handy for looking up coordinates.

## Tests

```bash
pytest
```

## Project layout

```
app.py              Flask app factory
db.py / schema.sql  SQLite helpers and schema
seed.py             Sample restaurants, users, reviews, Top 5s
constants.py        Cuisines, neighbourhoods, filters
services.py         Search, distance, Community Top 5 scoring
helpers.py          Auth helpers, CSRF, session helpers
routes/             Blueprints (auth, restaurants, reviews, me, top5)
templates/          Jinja pages + shadcn-style component macros
static/css/         Design tokens, components, layout
static/js/          Theme, UI widgets, filters, favorites, compare, Top 5
tests/              Smoke tests
```

## Accessibility notes

- Skip link, landmarks, one `h1` per page
- Visible focus rings; dialogs and sheets trap focus and restore it
- Forms use labels, `aria-invalid` / `aria-describedby`, and focused error summaries
- Star ratings are radio groups; favorite / compare use `aria-pressed`
- Toasts and filter result counts announce through live regions
- Top 5 reorder works with Move up / Move down (not only drag)
- Respects `prefers-reduced-motion`; themes meet AA contrast targets

## Out of scope

Real-time reservations, payments, live GPS and large external restaurant APIs are intentionally omitted for this course version.
