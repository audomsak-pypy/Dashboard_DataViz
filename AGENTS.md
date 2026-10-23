# AGENTS.md — Standing Rules for This Project

Kanchanaburi Wildfire & Durian Cultivation Observatory.
A single-page Plotly Dash dashboard that shows hotspot (wildfire) data in protected forests next to durian cultivation area, by tambon (sub-district), in Kanchanaburi Province, Thailand.

Read this file at the start of every session. If anything here conflicts with an older instruction, follow this file, unless the user gives a new explicit instruction in the current chat.

## Current task

Follow **`HANDOFF_Redesign.md`**, stage by stage (0 → A → B → C → D → E → F).
- Work on **one stage at a time** and **stop and wait for the user at every 🛑 STOP**. Never start the next stage on your own.
- After finishing a stage, update the checklist and the Progress Log in `HANDOFF_Redesign.md`.
- If you have not been told to start, read that file, summarize the plan briefly, and ask which stage to begin with.

## Running the project

- Use the environment `.venv_phase8`. The original `.venv` is broken because it points to a removed Python interpreter.
- Run the app: `.\.venv_phase8\Scripts\python app.py`, then open `http://127.0.0.1:8050/`
- Regenerate parquet data: `.\.venv_phase8\Scripts\python data_prep.py`
- The user's operating system is Windows (PowerShell).

## Files you need to know

- `app.py` — all layout and callbacks (single page)
- `config.py` — constants, theme colors, disclaimer text (`CAUSAL_DISCLAIMER`), `EXPECTED_TOTAL_HOTSPOTS`
- `data_prep.py` — builds the parquet files and runs the assertions
- `utils/data_loader.py` — data loading functions
- `data/` — raw CSV files and transformed parquet files
- `assets/` — CSS/JS that Dash loads automatically (created in Stage B)
- Reference figure: the correct total hotspot count is **8,606**

## Language

- The **dashboard UI text is in Thai** (titles, labels, dynamic sentences, disclaimer).
- Everything else is in **English**: code, comments, commit messages, and reports to the user.
- Thai column names such as `อำเภอ_norm` and `ตำบล_norm` are identifiers. Do not rename or translate them.
- Do not retype or reword the Thai disclaimer. Reuse `CAUSAL_DISCLAIMER` from `config.py` exactly.

## Hard rules (never violate)

**Structure and behavior**
- Single page only. **No multi-tab or multi-page layout.**
- Every chart must respond to the existing global cross-filter. Every chart marked "clickable" must filter the whole page when clicked.
- Keep existing component `id`s wherever possible. If you rename one, update every callback that references it.
- Always group and join by the key **(`อำเภอ_norm`, `ตำบล_norm`)**, because tambon names can repeat across districts.
- Every KPI must come from one shared calculation function. Never hard-code KPI numbers (for example 8606, 8500, 8129) in layout or figure code. The constant from `config.py` may be used only inside assertions.

**Data**
- Do not edit raw files in `data/`.
- If new derived data is needed, produce it through `data_prep.py` and keep the assertion `sum(hotspot_count) == 8,606` both before and after any JOIN.
- A tambon that has durian but no hotspots has **0 hotspots**, not Missing.
- Tables and charts must show **0.0 rai (🟡)** and **Missing (⬜)** as clearly different states. Never fill Missing with 0.
- Show only years that actually have data. Never plot a year without data as zero.

**Analysis and wording**
- No Mann-Whitney U and no other inferential statistics. Use means or counts plus a plain-language explanation.
- No spatial-distance analysis between hotspots and durian plots (CRS limitation). Keep the CRS note on the map.
- Never write text, including auto-generated text, that implies durian causes fire or fire damages durian. Do not use words equivalent to "risk", "affected", "impacted" or "cause" when comparing durian with fire. Use neutral wording such as "both high" or "co-located in the same tambon".
- The Thai disclaimer must always be clearly visible on screen and must appear next to every chart or table that compares durian with hotspots. Its meaning: the comparison uses administrative boundaries, it does not mean fires occurred inside cultivated plots, and causality cannot be concluded.

**Safety of the work**
- **Never delete or move any file or folder without asking the user first.** Propose a list and wait for approval.
- Make one `git commit` per stage before starting the next stage.
- Do not install extra packages without telling the user. If one is necessary, explain why and add it to `requirements.txt`.

## Working style

- Keep reports short and to the point, using the format in section 6 of `HANDOFF_Redesign.md`.
- If you find something that contradicts the real data or is ambiguous, report it instead of guessing.
- After every code change, run the app, confirm HTTP 200, and check the log for callback errors.
- Test at least these states: no filter, one tambon selected, one district selected, narrowed year range, and a filter that returns zero rows (it must render gracefully with no traceback).
