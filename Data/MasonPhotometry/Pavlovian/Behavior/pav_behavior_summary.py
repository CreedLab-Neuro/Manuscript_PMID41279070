"""
pav_behavior_summary.py — condense the Pavlovian 3-day training behaviour into two
small CSVs that can live in the GitHub repo.

    python pav_behavior_summary.py [out_dir]

Why: the cleaned Bonsai behaviour is 1.7 GB ("FED metrics only") to 8.0 GB
("Behavior_only_data") because every row repeats the event timestamps. A single
625,798-row file contains only 111 tone events. Panels C and D of the Pavlovian figure
need the events, not the traces, so this extracts them once and writes ~8k rows.

Trial logic is taken verbatim from
  Open Field Pavlov/Code/Python/Old/Behavioral Plotting and Stats.py
so the output reproduces the published panels:
  * each grab is matched to the most recent PRECEDING, NOT-YET-USED tone
  * latency = grab - tone ONSET  (the figure subtracts 5 s to show it from tone end)
  * success = latency < 10 s;  delayed = >= 10 s;  no_pellet = tone never matched
"""
import os
import re
import sys
import glob
import numpy as np
import pandas as pd

_BASE = (r"C:\Users\masba\Box\Kravitz Lab Box Drive\Mason\Open Field Pavlov"
         r"\Bonsai Data\Cleaned_Data")
# The two cohorts sit in different folders: OFP (75 files) in the top-level
# "FED metrics only", OFP2 (30 files) in "Cleaned\FED metrics only". Reading only
# the first silently loses 4 Sham, 3 SNI and 3 SK3 mice.
SRC = [os.path.join(_BASE, "FED metrics only"),
       os.path.join(_BASE, "Cleaned", "FED metrics only")]

SUCCESS_THRESH_S = 10.0                       # success if latency < this
TONE_DUR_S       = 5.0                        # every Pavlovian tone was 5 s
GRAB_CANDIDATES  = ["Pellet_Grab", "Pellet Grab", "Grab", "PelletGrab"]

# SK3_OFP_F32_09_23_25_01_2025-09-23T10_51_31_cleaned.csv
# Sham_OFP2_M01_11_12_25_01_2025-11-12T16_56_47_cleaned.csv
NAME_RE = re.compile(r'^(?P<group>SK3|SNI|Sham|SHAM)?_?(?P<cohort>OFP2|OFP)_'
                     r'(?P<animal>[MF]\d+)_'
                     r'(?P<date>\d{2}_\d{2}_\d{2})_(?P<day>\d{2})_', re.I)


def parse_name(fname):
    """-> dict(group, cohort, animal, animal_id, date, day) or None.

    `animal` keeps its zero padding, which is the ONLY thing separating the two
    cohorts' IDs (OFP2's M01 is not OFP's M1), and `animal_id` prefixes the cohort
    so the two can never be merged downstream.
    """
    m = NAME_RE.match(os.path.basename(fname))
    if not m:
        return None
    g = (m.group('group') or '').upper()
    cohort = m.group('cohort').upper()
    return {'group': {'SHAM': 'SHAM', 'SNI': 'SNI', 'SK3': 'SK3'}.get(g, g or '?'),
            'cohort': cohort,
            'animal': m.group('animal'),
            'animal_id': f"{cohort}_{m.group('animal')}",
            'date': m.group('date'),
            'day': int(m.group('day'))}


def event_times(df, col, ts):
    """Event timestamps from `col`, handling BOTH encodings found in the Box data.

    "FED metrics only" stores Tone/Grab as BINARY 0/1 flags, with the time in the
    TimeStamp column. "Behavior_only_data" stores the event TIMESTAMPS directly,
    repeated down every row. Reading the first as if it were the second yields two
    "events" per file (the values 0 and 1), which is silently wrong -- so detect it.
    """
    v = pd.to_numeric(df[col], errors='coerce')
    u = np.unique(v.dropna().values)
    is_binary = len(u) <= 3 and set(np.round(u, 6)).issubset({0.0, 1.0})
    if is_binary:
        if ts is None:
            return []
        return sorted(float(x) for x in ts[(v.values == 1) & np.isfinite(ts)])
    return sorted(float(x) for x in u)


def match_trials(tone_times, grab_times):
    """Each grab claims the most recent preceding tone that is not already taken.

    Verbatim from the original script -- it is deliberately grab-driven, so a tone
    with no grab simply stays unmatched rather than being paired with a later grab.
    """
    matched, used = [], set()
    for g in grab_times:
        cands = [t for t in tone_times if t < g and t not in used]
        if cands:
            t = cands[-1]
            matched.append((t, g))
            used.add(t)
    return matched


def main(out_dir):
    files = sorted(f for d in SRC for f in glob.glob(os.path.join(d, '*.csv')))
    print(f"{len(files)} files in\n  " + "\n  ".join(SRC) + "\n")
    trial_rows, sess_rows, skipped = [], [], []

    for i, f in enumerate(files, 1):
        meta = parse_name(f)
        if not meta:
            skipped.append((os.path.basename(f), 'unparsed name')); continue
        # only the event columns -- the traces are what make these files huge.
        # Box Drive keeps some files as cloud-only placeholders, which raise OSError
        # on read; record those instead of aborting the whole run.
        try:
            head = pd.read_csv(f, nrows=0)
            gcol = next((c for c in GRAB_CANDIDATES if c in head.columns), None)
            if 'Tone' not in head.columns or gcol is None:
                skipped.append((os.path.basename(f), 'missing Tone/Grab column')); continue
            cols = [c for c in ('TimeStamp', 'Tone', gcol) if c in head.columns]
            d = pd.read_csv(f, usecols=cols, low_memory=False)
            ts = (pd.to_numeric(d['TimeStamp'], errors='coerce').values
                  if 'TimeStamp' in d.columns else None)
        except Exception as e:
            skipped.append((os.path.basename(f), f'{type(e).__name__}: {e}')); continue

        tone = event_times(d, 'Tone', ts)
        grab = event_times(d, gcol, ts)
        matched = match_trials(tone, grab)
        lat = {t: g - t for t, g in matched}

        for n, t in enumerate(tone, 1):
            L = lat.get(t, np.nan)
            trial_rows.append({
                **meta, 'trial_number': n,
                'tone_time_s': float(t),
                'tone_end_s': float(t) + TONE_DUR_S,
                'grab_time_s': float(t + L) if np.isfinite(L) else np.nan,
                'latency_from_tone_onset_s': float(L) if np.isfinite(L) else np.nan,
                'latency_from_tone_end_s': float(L - TONE_DUR_S) if np.isfinite(L) else np.nan,
                'outcome': ('no_pellet' if not np.isfinite(L)
                            else ('success' if L < SUCCESS_THRESH_S else 'delayed')),
            })

        lats = list(lat.values())
        n_succ = sum(1 for L in lats if L < SUCCESS_THRESH_S)
        sess_rows.append({
            **meta,
            'n_tones': len(tone), 'n_grabs': len(grab), 'n_matched': len(matched),
            'n_success': n_succ,
            'n_delayed': sum(1 for L in lats if L >= SUCCESS_THRESH_S),
            'n_no_pellet': len(tone) - len(matched),
            'success_pct': (100.0 * n_succ / len(tone)) if tone else np.nan,
            'latency_median_from_tone_onset_s': float(np.median(lats)) if lats else np.nan,
            'latency_median_from_tone_end_s': (float(np.median(lats)) - TONE_DUR_S) if lats else np.nan,
            'latency_mean_from_tone_onset_s': float(np.mean(lats)) if lats else np.nan,
            'source_file': os.path.basename(f),
        })
        if i % 10 == 0 or i == len(files):
            print(f"  {i}/{len(files)}")

    trials = pd.DataFrame(trial_rows).sort_values(['group','animal_id','day','trial_number'])
    sess   = pd.DataFrame(sess_rows).sort_values(['group','animal_id','day'])
    os.makedirs(out_dir, exist_ok=True)
    p1 = os.path.join(out_dir, 'pav_behavior_per_trial.csv')
    p2 = os.path.join(out_dir, 'pav_behavior_per_session.csv')
    trials.to_csv(p1, index=False); sess.to_csv(p2, index=False)

    print(f"\nskipped (unparsed name or missing columns): {len(skipped)} {skipped[:3]}")
    print(f"\n  {os.path.basename(p1):32s} {len(trials):6d} rows  {os.path.getsize(p1)/1024:8.1f} KB")
    print(f"  {os.path.basename(p2):32s} {len(sess):6d} rows  {os.path.getsize(p2)/1024:8.1f} KB")
    print("\n=== coverage (animals per group x day) ===")
    print(sess.pivot_table(index='group', columns='day', values='animal_id', aggfunc='nunique').to_string())
    print("\n=== success rate by group x day (mean of per-session %) ===")
    print(sess.pivot_table(index='group', columns='day', values='success_pct').round(1).to_string())
    print("\n=== median latency from tone end (s) ===")
    print(sess.pivot_table(index='group', columns='day',
                           values='latency_median_from_tone_end_s').round(2).to_string())
    return trials, sess


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'pav_behavior_out')
    main(out)
