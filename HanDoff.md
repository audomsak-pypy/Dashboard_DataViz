# HANDOFF.md for Antigravity (Dashboard Agent)

**⚠️ CRITICAL RULES:** 
1. Work Phase-by-Phase. Stop and get user approval before proceeding to the next phase.
2. Read `BRD.md` and `DATA_DICTIONARY.md` strictly. 
3. **DO NOT** make causal claims. Display all disclaimers requested in BRD.

## 📍 Phase 1: Data Profiling & Validation
*   **Action:** Script to read both CSVs, check schemas, ranges, and confirm whitespace issues in Amphoe/Tambon.
*   **Output:** `profiling_log.txt`
*   **Approval Gate:** User must confirm the raw statistics.

## 📍 Phase 2: Data Model Preparation (Zero/Duplicate Prevention)
*   **Action:** 
    1. Parse Dates and Time (convert Float to HH:MM).
    2. Normalize geographic strings.
    3. Aggregate `cleaned_dataset_Wildfire.csv` by `[อำเภอ_norm, ตำบล_norm, พ.ศ.]` **BEFORE** joining.
    4. Perform OUTER JOIN with `wildfire_point.csv`.
    5. Apply Zero/NaN logic according to `DATA_DICTIONARY.md`.
*   **Output:** `data_prep.py`
*   **Test:** Assert that `sum(hotspot_count) == 8606`.
*   **Approval Gate:** User must confirm the assertion passes and view the shape of the joined dataframe.

## 📍 Phase 3: Application Foundation
*   **Action:** Setup Plotly Dash architecture, modular folders (`tabs/`, `utils/`), and load the processed data safely.
*   **Output:** `app.py`, `config.py`
*   **Approval Gate:** User inspects folder structure.

## 📍 Phase 4: Tab 1 (Hotspot Overview)
*   **Action:** Build map (LAT/LONG), Temporal charts (Month, HH:MM).
*   **Constraint:** Map must have a note: "CRS assumption: Displayed strictly on standard geographic projection. Spatial distance analysis is disabled."
*   **Approval Gate:** User reviews UI of Tab 1.

## 📍 Phase 5: Tab 2 (Durian Cultivation)
*   **Action:** Build Durian trends and ranking.
*   **Constraint:** Explicitly render Zero vs Missing data differently in UI tables/charts.
*   **Approval Gate:** User reviews UI of Tab 2.

## 📍 Phase 6: Tab 3 (Spatial & Temporal Comparison)
*   **Action:** Implement Mann-Whitney U test (via `scipy.stats.mannwhitneyu`) comparing `hotspot_count` between Tambon groups (`durian_area > 0` vs `durian_area == 0`).
*   **Constraint:** Must display sample sizes, test statistic, p-value, and effect size. Must display the explicit causal disclaimer defined in BRD Section 5.
*   **Approval Gate:** User reviews UI and statistical readout.

## 📍 Phase 7: Final Tests & Docs
*   **Action:** Verify cross-filtering, generate `README.md`, `requirements.txt`, and `.gitignore`.