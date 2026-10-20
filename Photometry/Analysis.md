# Photometry Analysis

Fiber photometry analysis for the two behavioural paradigms in this repository.
Every notebook pulls its data **directly from this repo** and writes its outputs back
out for you to commit — there is no local or Drive state anywhere in the chain, so
anyone with the repo can reproduce a figure from raw data.

- [Pavlovian](#pavlovian) — three notebooks, raw → figure
- [Variable Tone](#variable-tone) — four notebooks, raw → figures
- [Event codes](#event-codes)

---

## Pavlovian

Raw acquisition files → merged per-animal CSVs → analysis pickle → figure. Same shape as
Variable Tone: every notebook reads from this repo and writes outputs for you to commit.

```text
   Bonsai/Scaled_Renamed        RWD/RWD_Fluorescence
   tracking + TTL               410 / 470 nm
        └──────────────┬──────────────┘
                       │   1. Preprocessing
                       ▼
              RWD/Processed Data      48 merged CSVs
                       │
                       │   2. Analysis
                       ▼
              pav_pub_data.pkl ──┐
                                 │   3. Figure      ◄── Behavior/pav_behavior_per_trial.csv
                                 ▼
                          Figure 1 (SVG + PNG)
```

### Notebooks

| Step | Notebook | Reads | Writes |
|------|----------|-------|--------|
| 1 | [**Preprocessing**](https://colab.research.google.com/drive/1-DjXWbCYx7AxyE4_9BKa4vdXBUBT9yQx?usp=sharing) | [`Bonsai/Scaled_Renamed`](Pavlovian/Bonsai/Scaled_Renamed), [`RWD/RWD_Fluorescence`](Pavlovian/RWD/RWD_Fluorescence) | 48 merged CSVs + per-session QC |
| 2 | [**Analysis**](https://colab.research.google.com/drive/1bpzP9aYUnirTiRwpQl5VR-klx7WhiyMm?usp=sharing) | [`RWD/Processed Data`](Pavlovian/RWD/Processed%20Data) | [`pav_pub_data.pkl`](Pavlovian/pav_pub_data.pkl) |
| 3 | [**Figure**](https://colab.research.google.com/drive/1R8JB0hxT-1PHMupiwLCWLLPNETQpjgtU?usp=sharing) | `pav_pub_data.pkl`, [`Behavior/pav_behavior_per_trial.csv`](Pavlovian/Behavior/pav_behavior_per_trial.csv) | Figure 1 (SVG + PNG) |

Each notebook resolves `main` to a commit SHA on startup and fetches everything by SHA, so
a run is pinned to one version of the data and prints which one it used.

### 1. Preprocessing

Six stages, batched over all 48 sessions (24 animals × 2 recordings):

| Stage | What it does |
|-------|--------------|
| **A** | Clean Bonsai — de-duplicate CombineLatest frames, recompute speed, carry the hand-curated trial flags |
| **B** | Photometry — double-exponential debleach → motion correction against the 410 nm channel → 25th-percentile z-score (`Corrected_Fluorescence_Z_25`) |
| **C** | RWD events — `ToneStart` / `PelletGrab`, carried through when the raw file already has them, otherwise parsed from the `Events` pulse widths |
| **D** | Align the Bonsai clock to the RWD clock, then interpolate tracking onto the photometry time base |
| **E** | Position normalization — FED located from the `PelletGrab` centroid, pixels scaled to cm |
| **F** | Batch, QC figure per session, verify against the committed data, save |

Output is one CSV per session in [`Pavlovian/RWD/Processed Data`](Pavlovian/RWD/Processed%20Data),
alongside [`preprocessing_qc.csv`](Pavlovian/RWD/Processed%20Data/preprocessing_qc.csv) —
one row per session with the alignment quality, FED fit and event counts.

### 2. Analysis

Per-trial behavioural metrics (retrieval latency, percentage collected, mean speed, peak
and mean DA), event-locked PSTHs for cue and pellet retrieval, per-trial traces for the
heatmaps, and the baseline → trained learning contrasts. No FIR kernels: the Pavlovian
task has only two events, so there is nothing to deconvolve.

DA measurement windows, relative to each event:

| Event | Window | Why |
|-------|--------|-----|
| Cue | 0 to +5 s | spans the whole 5 s tone |
| PelletGrab | −2 to +1 s | retrieval DA peaks *before* the grab, so a forward-only window would miss it |

### 3. Figure

Rebuilds the figure from the pickle plus the behaviour CSV. Panels A, B, E and F are left
blank for schematics; C and D are the training behaviour; G and H are the early and late
recordings, each with a tone-onset and a pellet-retrieval heatmap over its PSTH. Group
comparisons (Welch's *t* on peak z and AUC) are computed from exactly the traces that are
plotted and printed on the panels.

### Training behaviour (panels C and D)

The three training days are **not** in this repo. The cleaned Bonsai files are ~2.8 GB
across 105 CSVs, and they are huge only because every row repeats the event timestamps —
a 625,798-row file holds 111 tone events. Panels C and D need the events, not the traces,
so the events are extracted once and only the ~1.8 MB result is committed:

| | |
|---|---|
| **Source** (Box, not in this repo) | `Open Field Pavlov/Bonsai Data/Cleaned_Data/FED metrics only` (OFP, 75 files) and `.../Cleaned_Data/Cleaned/FED metrics only` (OFP2, 30 files) |
| **Script** | [`Behavior/pav_behavior_summary.py`](Pavlovian/Behavior/pav_behavior_summary.py) — run `python pav_behavior_summary.py [out_dir]` against the Box paths above |
| **Output** | [`Behavior/pav_behavior_per_trial.csv`](Pavlovian/Behavior/pav_behavior_per_trial.csv) (15,393 rows, one per tone) and [`Behavior/pav_behavior_per_session.csv`](Pavlovian/Behavior/pav_behavior_per_session.csv) (105 rows) |

Trial logic follows the original analysis: each grab claims the most recent preceding,
not-yet-used tone; latency is measured from tone onset; success means latency < 10 s.

Panel D plots the **mean latency of successful trials, from tone onset**, which is what the
published figure did. Including the misses turns the first pellet bin into a multi-minute
value and blows the axis out.

### Cohort

**Photometry:** 24 animals, 8 per group (SHAM, SNI, SK3), two sessions each — session 01
early (baseline), session 02 late (trained).

**Training behaviour:** 35 animals — 14 SHAM, 13 SNI, 8 SK3 — across both cohorts, three
days each.

---

## Variable Tone

Raw acquisition files → merged per-animal CSVs → analysis pickle → figures.

```text
   Bonsai/Raw            RWD/RWD_Fluorescence
   tracking + TTL        410 / 470 nm
        └──────────┬──────────┘
                   │   1. Preprocessing
                   ▼
        RWD/RWD_Processed     24 merged CSVs
                   │
                   │   2. Analysis
                   ▼
         vt_pub_data.pkl
                   │
         ┌─────────┴─────────┐
         │ 3. Figure         │ 4. SK3 rescue figure
         ▼                   ▼
  SHAM vs SNI          SK3 vs historical
  12-panel figure      12-panel figure
```

### Notebooks

| Step | Notebook | Reads | Writes |
|------|----------|-------|--------|
| 1 | [**Preprocessing**](https://colab.research.google.com/drive/1VWboBgWQ1i9vQLCMjrElaLfEonZ896y-?usp=sharing) | [`Bonsai/Raw`](VariableTone/Bonsai/Raw), [`RWD/RWD_Fluorescence`](VariableTone/RWD/RWD_Fluorescence) | 24 merged CSVs + per-animal QC |
| 2 | [**Analysis**](https://colab.research.google.com/drive/1dTUPblPC8lWDuNEe6kqzNxnXUstPhl2o?usp=sharing) | [`RWD/RWD_Processed`](VariableTone/RWD/RWD_Processed) | `vt_pub_data.pkl` |
| 3 | [**Figure**](https://colab.research.google.com/drive/1bp6p1-VJN1DZ1PGikX77Njoj6FRj9fv-?usp=sharing) | `vt_pub_data.pkl` | Figure 1 — SHAM vs SNI (SVG + PNG) |
| 4 | [**SK3 rescue figure**](https://colab.research.google.com/drive/1dwTDNIyNu8lvPMfgooru6MX_JYueDY-6?usp=sharing) | `vt_pub_data.pkl` | Figure 2 — SK3 rescue (SVG + PNG) |

Each notebook resolves `main` to a commit SHA on startup and fetches everything by SHA,
so a run is pinned to one version of the data and prints which one it used.

### 1. Preprocessing

Six stages, batched over all 24 animals:

| Stage | What it does |
|-------|--------------|
| **A** | Clean Bonsai from raw — scale tracking, parse TTL pulses into behavioural events |
| **B** | Photometry — double-exponential debleach → motion correction against the 410 nm channel → 25th-percentile z-score (`Corrected_Fluorescence_Z_25`) |
| **C** | RWD events — tone onsets by duration, `Dispense_RWD`, `Retrieval_RWD` |
| **D** | Align the Bonsai clock to the RWD clock, then interpolate tracking onto the photometry time base |
| **E** | Position normalization — FED located from the retrieval centroid, pixels scaled to cm, coordinates rotated to the cage axes |
| **F** | Batch, QC figure per animal, verify against the previous data version, save |

Output is one CSV per animal (30 columns) in
[`VariableTone/RWD/RWD_Processed`](VariableTone/RWD/RWD_Processed), covering processed
photometry, RWD events, Bonsai tracking, speed, and distance from the FED.

> Position normalization computes `DistFromFED` as the distance to the FED estimated from
> where the animal actually retrieves pellets, rather than a fixed coordinate. The
> pre-normalization value is preserved as `DistFromFED_orig` so re-running is idempotent.

### 2. Analysis

Per-trial behavioural metrics (retrieval latency, mean speed, distance at tone end,
peak and mean DA), event-locked PSTHs for cue / dispense / retrieval, the per-trial
traces the figure needs, and **FIR kernel deconvolution**.

The FIR design is 91 lags × 9 events at 15 Hz, which is rank-deficient given 5–17 events
per duration, so kernels are fit with ridge regularization (λ = 1.0).

### 3. Figure

Rebuilds the 12-panel publication figure (**Figure 1**, SHAM vs SNI) from the pickle alone
— no CSVs, so it runs in seconds. Panel A picks up `vt_schematic.png` from the repo if
present.

### 4. SK3 rescue figure

**Figure 2.** Same 12-panel layout, with SK3 added as the new cohort. SHAM and SNI are drawn
**dotted and semi-transparent** to mark them as historical data rather than animals collected
alongside SK3:

| | lines | boxes |
|---|---|---|
| SHAM, SNI (historical) | dotted, alpha 0.55 | dashed edge, alpha 0.28 |
| SK3 (new cohort) | solid, full opacity | solid edge, alpha 0.55 |

The heatmap panels stack all three groups, panel K shows SK3's dispense kernels and panel L
overlays both historical groups. Statistics compare **SNI vs SK3** — the rescue contrast —
rather than SHAM vs SNI.

Reads the same pickle as Figure 1, so both figures are always built from one analysis run.

### Cohort

24 animals, 8 per group (SHAM, SNI, SK3), recorded at 15 Hz, with 5 s / 10 s / 20 s tones.
One animal (F19) has no Bonsai recording and is handled as photometry-only throughout.

---

## Event codes

TTL pulse width encodes the event type. Variable Tone classifies three codes:

| Nominal pulse | Accepted window | Event |
|---------------|-----------------|-------|
| 100 ms | 50–150 ms | Tone onset |
| 500 ms | 400–700 ms | Pellet dispense |
| 1000 ms | 900–1200 ms | Pellet retrieval (grab) |

Anything outside these windows is classified `Unknown` and dropped.

> **The same pulse width means different things across the two paradigms.** Pavlovian is
> parsed two-way on a 300 ms threshold — tone below, pellet grab above — so a 500 ms pulse
> is a *grab* there, but a *dispense* in Variable Tone. Check which paradigm you are
> reading before interpreting a pulse.

**Pavlovian raw files use three different encodings**, depending on when they were recorded:

| Encoding | Sessions | How events are marked |
|----------|----------|-----------------------|
| Pulse count | F2, F3, M2 session 01 (070225) | every pulse ≈100 ms; a single pulse is a tone, a pair 200 ms apart is a grab, and a sub-sample blip ~5.8 s after the tone is the dispense |
| Pulse width | most sessions, `Events` column | 100 ms tone, 500 ms grab (sampling as 467 or 533 ms at 15 Hz) |
| `Name` / `State` | newer exports | separate columns instead of an `Events` string; same width rule |


The earliest Variable Tone cohort (C57, IDs below 5) has no separate dispense signal in
Bonsai, so dispense-width pulses from those animals are treated as retrievals and the
dispense time is reconstructed from tone offset during analysis.

All Pavlovian data used 5 s tones. Variable Tone uses 5 s, 10 s, and 20 s.
