# HANDOFF — Dashboard Redesign (continues from Phase 8)

> This file is the **main work spec** for Codex. Work through the stages in order and **stop and wait for the user at every 🛑 STOP**.
> The standing project rules are in `AGENTS.md`. Read both files. If they conflict, follow `AGENTS.md`.

---

## 0. How to use this file (for Codex)

1. Read `AGENTS.md` and this file completely before changing any code.
2. Work one stage at a time, in order. **Do not skip a stage and do not start the next stage on your own.**
3. When a checklist item is done, change `- [ ]` to `- [x]` **in this file**, and add a line to the Progress Log at the bottom, so the next session knows where the work stopped.
4. At the end of each stage: run the app, check every acceptance criterion, make a separate `git commit`, send the report in the format of section 6, then stop and wait.
5. If something is ambiguous or contradicts the real data, report it to the user. Do not guess and fix it silently.

---

## 1. Current status

- Project: Kanchanaburi Wildfire & Durian Cultivation Observatory (Plotly Dash, single page).
- Phases 1–7 are done. Phase 8A is partly done (per your earlier root-cause report: `app.py` is a partially corrected version, and `README.md` still contains an obsolete 8,129 figure).
- Working environment: **`.venv_phase8`** (the original `.venv` points to a removed Python).
- Problems seen in the earlier dashboard screenshot:
  - the hotspot gauge showed 8,610 (should be 8,606)
  - the durian gauge showed 13,730 rai while the header showed 8,129 rai for BE 2568, and the gauge maximum was hard-coded
  - the year input boxes beside the range slider were empty white boxes
  - the forest-type treemap had only 2 blocks
  - the comparison chart had only 8 tambon-years in the "no durian" group

## 2. Goal

Turn the dashboard from "showing data" into **"answering 4 questions that this data can really answer"**, and make it more attractive using HTML/CSS.

| # | Question | Already exists | To add |
|---|---|---|---|
| 1 | When do fires occur? | monthly chart, hourly list | Year × month heatmap |
| 2 | Where do fires occur? | map, donut, forest share | Top 10 tambons, chart by responsible station, density map |
| 3 | Which durian tambons are in high-hotspot areas? | durian table, 2-bar comparison | Quadrant scatter, "watch-list" table, 3-group comparison |
| 4 | What are the trends? | durian area line, BE 2561–2568 | Dual-axis chart against yearly hotspots |

Every section must have **one dynamic answer sentence** (in Thai) computed from the currently filtered data.

---

## 3. Facts to verify from the real data (do not trust this list without checking)

- The correct total hotspot count is **8,606** (assertion in `data_prep.py`).
- The old header said hotspot data covers **BE 2566–2568**, while durian data covers **BE 2561–2568**. Check the real year ranges in the data, and design every cross-year chart so it handles non-overlapping year ranges.
- CE year = BE year − 543.
- `hotspot_events` columns: `LAT`, `LONG`, `date_parsed`, `month`, `hour_of_day`, `CONFEDENCE` (values: nominal, low, high; keep this spelling), `ประเภทป่าอนุรักษ์`, `สถานีฯที่รับผิดชอบ`, `อำเภอ_norm`, `ตำบล_norm`.
- `joined_table` columns: `อำเภอ_norm`, `ตำบล_norm`, `พ.ศ.`, `durian_area_rai`.
- **Hypothesis to prove or disprove:** the 13,730 figure may come from duplicated rows in `joined_table`, or from tambon names repeated across districts. Every group-by and join must use the key **(`อำเภอ_norm`, `ตำบล_norm`)**.
- A tambon with durian but no hotspots counts as 0 hotspots (not Missing).

---

## Stage 0 — Safety snapshot

**Goal:** be able to roll back if something breaks.

- [x] Run `git status` and `git log -n 5` and report the state
- [ ] If there is no repository, tell the user first. Do not run `git init` yourself
- [x] Commit a snapshot of the current state (message: `snapshot: before redesign`)
- [x] Confirm the app runs with `.venv_phase8` and returns HTTP 200

**Acceptance:** a snapshot commit exists and the app runs.

---

## Stage A — Fix number integrity (Phase 8A)

**Goal:** every number on the screen agrees and can be verified.

- [ ] Create one KPI calculation function (single source of truth), for example `compute_kpis(filter_state)`. The header, gauges, donut center and Key Insights must all call it
- [ ] Remove hard-coded values (`8606`, `8500`, `8,129` and similar) from layout and callbacks. Use `EXPECTED_TOTAL_HOTSPOTS` from `config.py` only inside assertions
- [ ] **Report the real root cause** of 8,610 and 13,730 with evidence (number of duplicate rows, duplicated keys, and so on) **before** fixing
- [ ] Compute gauge maxima from the data (for example tambon-level max or a high percentile) and show the meaning of the three color bands to the user
- [ ] Add an integrity check at app start (assert) and at filter time: with no filter, header = gauge = data total. If they differ, show a clearly visible warning bar
- [ ] In the planted-vs-not-planted comparison chart, show `n=` for each group, and report whether tambons without durian are missing from the data entirely
- [ ] Fix `README.md` so every figure matches the real data

**Acceptance (verifiable):**
- No filter: hotspot total on the header = gauge = 8,606; durian area for BE 2568 on the header = gauge
- One tambon selected: gauge, table and KPI values equal the values computed directly from the DataFrame
- No hard-coded KPI numbers remain in `app.py` (verify with grep and attach the result)

🛑 **STOP:** report the root causes and verification results, then wait for the user's approval.

---

## Stage B — HTML/CSS design system and new layout

**Goal:** an attractive, readable page organized into 4 sections, one per question.

- [ ] Move the CSS embedded in `app.index_string` into `assets/style.css` (Dash loads `assets/` automatically). Keep the existing theme variables: deep navy background, fire orange `#EA580C`, amber `#F59E0B`, durian green `#84CC16`, fonts Sarabun/Inter
- [ ] Use CSS Grid for the layout and make it responsive for narrow screens
- [ ] Create a reusable card helper for every chart: card header, accent line colored per section, subtle hover effect, `dcc.Loading`
- [ ] Build 4 sections. Each has: a number badge, a Thai question title, a section accent color, and one dynamic Thai answer sentence (handle the empty-data case)
- [ ] Top of page: header with a KPI strip (hotspots, durian area, selected area) including a year-over-year delta **only when the previous year exists in the data**; an auto-generated Key Insights bar with 3 sentences; a sticky filter bar; and the disclaimer as an amber bar that is prominent but compact
- [ ] Fix the two year input boxes beside the slider (empty white boxes) so they are readable in the dark theme
- [ ] Chart font size at least 12 px
- [ ] Replace the forest-type treemap (2 blocks) with a horizontal bar chart that is clickable and filters the forest type
- [ ] Balance the heights of the left and right columns (no leftover empty space)
- [ ] Keep existing component `id`s as much as possible. If one changes, update every callback that references it

**Key Insights (format examples):** the peak month and its share, the top tambon and its count, the peak time window and its share. Every sentence is computed from the currently filtered data.

**Acceptance:**
- Opening `http://127.0.0.1:8050/` shows no error in the console or log
- All existing cross-filters still work (map click, table, donut, forest bar, month bar, Reset button)
- The disclaimer is visible without scrolling

🛑 **STOP:** let the user look at the real page in the browser first.

---

## Stage C — Sections 1 and 2 (when / where)

- [ ] **Year × month heatmap** of hotspot counts (only years that have real data). Clicking a cell filters year and month
- [ ] **Top 10 tambons by hotspot count**, horizontal bar. Clicking a bar filters the tambon (use the district + tambon key)
- [ ] **Hotspot count by `สถานีฯที่รับผิดชอบ`** (responsible station; BRD Section C). Clickable if feasible
- [ ] **Map toggle**: point scatter ↔ density heatmap (`px.density_map` or equivalent) using the same filters
- [ ] Keep the existing monthly chart and hourly list. Add a note under the time window: hours with many hotspots may reflect satellite overpass times, not the actual time the fires started

**Acceptance:** clicking each new chart changes the map, the table, the KPIs and the Key Insights as expected; the Reset button clears everything.

🛑 **STOP**

---

## Stage D — Section 3 (which durian tambons are in high-hotspot areas)

- [ ] **Quadrant scatter:** 1 point = 1 tambon
  - X axis = durian area (rai) of the latest year inside the selected year range
  - Y axis = hotspot count inside the selected year range
  - Split lines at the medians of tambons with durian area > 0 (show the values used)
  - The four quadrant labels use neutral wording, for example "more durian · more hotspots" (written in Thai). **Never use words meaning risk, affected, impacted or cause**
  - Clicking a point filters the tambon
- [ ] **"Watch-list" table:** tambons in the upper-right quadrant, ranked by the combined rank of the two measures. Columns: tambon, district, durian area (rai), hotspot count. Clicking a row filters the page. **Do not create any ratio between hotspots and durian area**
- [ ] Replace the old 2-bar comparison with **3 groups** (no durian / low durian / high durian, split by quartile of durian area among tambons with area > 0). Show the mean hotspots per tambon with `n=` and a dynamic explanation
- [ ] Place the Thai disclaimer beneath the chart and table of this section
- [ ] The existing durian table still shows 0.0 rai (🟡) and Missing (⬜) as clearly different states

**Acceptance:** the number of points in the quadrant = the real number of tambons passing the filter; the sum of hotspots over all quadrant points = the total hotspot KPI for the same filter; clicking a point or row filters the whole page.

🛑 **STOP**

---

## Stage E — Section 4 (trends)

- [ ] Dual-axis yearly chart: durian area as a line (left axis) and hotspot count as bars (right axis)
- [ ] Show only years that have real data for each series. **Never plot a year without data as zero**
- [ ] Add an on-chart note stating which years overlap (BE and CE)
- [ ] The explanatory text must not suggest the two series cause each other, and the disclaimer must appear near the chart
- [ ] The chart responds to the tambon and district filters

**Acceptance:** values in the chart match the table and KPIs for the same year.

🛑 **STOP**

---

## Stage F — Project cleanup (propose first, do not delete on your own)

Propose the list and **wait for the user's approval item by item**:

- [ ] `dash_server`, `dash_server.err` (server logs)
- [ ] The `tabs/` folder (verify with grep that nothing imports it)
- [ ] The old broken `.venv` (keep `.venv_phase8`)
- [ ] `scipy` in `requirements.txt` (no longer used) and unused imports in `app.py` (`make_subplots`, `load_hotspot_agg`, `get_filter_options`, and so on; re-check after the changes)
- [ ] Move `BRD.md`, `HanDoff.md`, `Update BRD.md`, `Update HanDoff.md`, `Handoff_Phase8.md`, `image.png`, `profiling_log.txt` into `docs/`
- [ ] Update `.gitignore`: `.venv*/`, `__pycache__/`, `dash_server*`, `*.err`
- [ ] Update `README.md` (file structure, how to run, what was added)

🛑 **STOP:** work finished.

---

## 6. Report format after every stage

```
Stage: <name>
Files changed: <list>
What was done: <short, at most 5 lines>
What was verified: <each acceptance criterion pass/fail with brief evidence>
Commit: <hash + message>
Decisions needed from the user: <if any>
```

---

## 7. Progress Log (updated by Codex)

| Stage | Status | Commit | Notes |
|---|---|---|---|
| 0 | ✅ complete | snapshot: before redesign | Dashboard verified at HTTP 200 on localhost. |
| A | ⬜ not started | | |
| B | ⬜ not started | | |
| C | ⬜ not started | | |
| D | ⬜ not started | | |
| E | ⬜ not started | | |
| F | ⬜ not started | | |
