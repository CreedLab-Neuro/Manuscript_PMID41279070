# Photometry Analysis

Fiber photometry analysis for the two behavioural paradigms in this repository.
Every notebook pulls its data **directly from this repo** and writes its outputs back
out for you to commit — there is no local or Drive state anywhere in the chain, so
anyone with the repo can reproduce a figure from raw data.

- [Pavlovian](#pavlovian) — earlier paradigm
- [Variable Tone](#variable-tone) — current pipeline, three notebooks, raw → figure
- [Event codes](#event-codes)

---

## Pavlovian

Notebooks: [**photometry preprocessing**](https://colab.research.google.com/drive/11lXbswpBkk24Ruhv_2vUWffnuOfMujLK?usp=sharing)
· [**Bonsai tracking**](https://colab.research.google.com/drive/1tAPc8rVkvDPrhrxhfAtPZRv-_8C28qM1?usp=sharing)

### Photometry

Source data: [`Pavlovian/RWD/RWD_Fluorescence`](Pavlovian/RWD/RWD_Fluorescence)

1. Pre-process for QC, motion correction, and z-score of the full trace — stored in `Processed_df`
2. Parse the `Events` column of each fluorescence file into new `Processed_df` columns of
   0s and 1s for `ToneStart`, `ToneEnd`, and `PelletGrab`

### Bonsai tracking

Source data: [`Pavlovian/Bonsai`](Pavlovian/Bonsai)

3. Import and synchronize the Bonsai tracking X/Y data and event timestamps
4. Align initially on the first `ToneStart`
5. Identify Bonsai events and plot two strip plots — RWD tones and Bonsai tones — and use
   these to design an alignment strategy
6. Import X, Y, and events into `Processed_df` as `Bonsai_X`, `Bonsai_Y`, `Bonsai_ToneStart`
7. Check RWD-to-Bonsai tone alignment, quantify the differences, and see whether the trace
   can be scrunched to improve it
8. Scale `Bonsai_X` and `Bonsai_Y` to the box (18 cm × 36 cm)
9. Derive speed and `Distance_from_FED` from `Bonsai_X` and `Bonsai_Y`

### Goal

One file per mouse containing processed photometry, RWD events, Bonsai
tracking / speed / distance-to-FED, and Bonsai events — the last being largely redundant
with the RWD events, but retained so the synchronization error can be examined directly.

---

## Variable Tone

Raw acquisition files → merged per-animal CSVs → analysis pickle → publication figure.

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
                   │   3. Figure
                   ▼
      12-panel figure         SVG + PNG
```

### Notebooks

| Step | Notebook | Reads | Writes |
|------|----------|-------|--------|
| 1 | [**Preprocessing**](https://colab.research.google.com/drive/1VWboBgWQ1i9vQLCMjrElaLfEonZ896y-?usp=sharing) | [`Bonsai/Raw`](VariableTone/Bonsai/Raw), [`RWD/RWD_Fluorescence`](VariableTone/RWD/RWD_Fluorescence) | 24 merged CSVs + per-animal QC |
| 2 | [**Analysis**](https://colab.research.google.com/drive/1dTUPblPC8lWDuNEe6kqzNxnXUstPhl2o?usp=sharing) | [`RWD/RWD_Processed`](VariableTone/RWD/RWD_Processed) | `vt_pub_data.pkl` |
| 3 | [**Figure**](https://colab.research.google.com/drive/1d0uuePVV1OtxuQRkpwYnTe65zk35k1V5?usp=sharing) | `vt_pub_data.pkl` | 12-panel figure (SVG + PNG) |

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

Rebuilds the 12-panel publication figure from the pickle alone — no CSVs, so it runs in
seconds. Panel A picks up `vt_schematic.png` from the repo if present.

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

The earliest Variable Tone cohort (C57, IDs below 5) has no separate dispense signal in
Bonsai, so dispense-width pulses from those animals are treated as retrievals and the
dispense time is reconstructed from tone offset during analysis.

All Pavlovian data used 5 s tones. Variable Tone uses 5 s, 10 s, and 20 s.
