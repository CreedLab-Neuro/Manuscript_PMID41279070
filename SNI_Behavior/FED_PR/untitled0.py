# -*- coding: utf-8 -*-
"""
Created on Mon Feb 23 09:32:19 2026

@author: meagh
"""


import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pyabf


# ---------------------------
# Spike detection (dV/dt based)
# ---------------------------
def detect_spikes_dvdt(
    t_s,
    v_mV,
    window=(0.1, 2.15),
    dvdt_thresh_mV_per_ms=10.0,
    refractory_ms=2.0,
    peak_search_ms=2.0,
):
    """
    Detect spikes using a dV/dt threshold. Returns:
      spike_times_s (np.array), spike_indices (np.array of int indices into v_mV/t_s)

    Logic:
      1) compute dV/dt (mV/ms)
      2) find rising crossings above threshold within window
      3) enforce refractory period
      4) refine each detection to the local peak shortly after crossing
    """
    t0, t1 = window
    dt_s = float(np.median(np.diff(t_s)))
    if not np.isfinite(dt_s) or dt_s <= 0:
        return np.array([]), np.array([], dtype=int)

    # Window indices
    win_mask = (t_s >= t0) & (t_s <= t1)
    win_idx = np.where(win_mask)[0]
    if win_idx.size < 5:
        return np.array([]), np.array([], dtype=int)

    # dV/dt in mV/ms
    dvdt_mV_per_ms = np.gradient(v_mV, dt_s) / 1000.0

    dvdt_win = dvdt_mV_per_ms[win_idx]
    above = dvdt_win > dvdt_thresh_mV_per_ms

    # Rising edges: False -> True
    rising = np.where((~above[:-1]) & (above[1:]))[0] + 1
    if rising.size == 0:
        return np.array([]), np.array([], dtype=int)

    # Refractory enforcement
    refractory_samples = max(1, int(round((refractory_ms / 1000.0) / dt_s)))
    kept = []
    last = -10**12
    for r in rising:
        if r - last >= refractory_samples:
            kept.append(r)
            last = r
    kept = np.array(kept, dtype=int)

    # Refine to local peak after threshold crossing
    peak_search_samples = max(1, int(round((peak_search_ms / 1000.0) / dt_s)))
    spike_indices = []
    for r in kept:
        g = win_idx[r]  # global index in the sweep arrays
        end = min(len(v_mV) - 1, g + peak_search_samples)
        peak_i = g + int(np.argmax(v_mV[g : end + 1]))
        spike_indices.append(peak_i)

    spike_indices = np.array(spike_indices, dtype=int)
    spike_times_s = t_s[spike_indices]

    # Keep only those still inside the time window after peak refinement
    keep = (spike_times_s >= t0) & (spike_times_s <= t1)
    return spike_times_s[keep], spike_indices[keep]


def step_amplitude_from_command(cmd_waveform):
    """
    Extract the non-zero step level from the command waveform (abf.sweepC).
    If only 0 is present, returns 0.
    If multiple non-zero values exist, returns the one with largest absolute value.
    """
    vals = np.unique(np.round(cmd_waveform, 6))
    nonzero = vals[np.abs(vals) > 1e-9]
    if nonzero.size == 0:
        return 0.0
    return float(nonzero[np.argmax(np.abs(nonzero))])


# ---------------------------
# NEW: Multi-panel plot
# ---------------------------
def plot_multi_panel_sweeps(
    abf,
    window=(0.1, 2.15),
    dvdt_thresh_mV_per_ms=10.0,
    refractory_ms=2.0,
    voltage_channel=0,
    exclude_first_n=2,
    n_panels=12,
    nrows=3,
    ncols=4,
):
    """
    Plots sweeps in a grid, excluding the first N sweeps.
    Default: 12 sweeps in a 3x4 arrangement, excluding first 2 sweeps.
    Each panel shows detected spikes and the analysis window shading.
    """
    sweeps_to_plot = abf.sweepList[exclude_first_n : exclude_first_n + n_panels]

    fig, axes = plt.subplots(nrows, ncols, figsize=(14, 8), sharex=True, sharey=True)
    axes = np.array(axes).flatten()

    for ax, sweep in zip(axes, sweeps_to_plot):
        abf.setSweep(sweep, channel=voltage_channel)

        t = abf.sweepX
        v = abf.sweepY
        cmd = abf.sweepC
        step_amp = step_amplitude_from_command(cmd)

        spike_times, spike_idx = detect_spikes_dvdt(
            t,
            v,
            window=window,
            dvdt_thresh_mV_per_ms=dvdt_thresh_mV_per_ms,
            refractory_ms=refractory_ms,
        )

        ax.plot(t, v, linewidth=0.8)

        if spike_idx.size > 0:
            ax.scatter(t[spike_idx], v[spike_idx], s=1, zorder=3, c='red')

        t0, t1 = window
        ax.axvspan(t0, t1, alpha=0.10)

        # Title shows current step amplitude; include sweep index too if you want:
        ax.set_title(f"Step {step_amp:g} (sweep {sweep})", fontsize=9)

    # Turn off any unused axes (if fewer than n_panels exist)
    for ax in axes[len(sweeps_to_plot) :]:
        ax.axis("off")

    fig.suptitle("All sweeps (first 2 excluded) — spike dots = detected spikes", fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()


# ---------------------------
# Main routine
# ---------------------------
def analyze_abf(
    abf_path,
    window=(0.1, 2.15),
    dvdt_thresh_mV_per_ms=10.0,
    refractory_ms=2.0,
    voltage_channel=0,
    out_csv_path=None,
    make_multipanel=True,
):
    abf = pyabf.ABF(abf_path)

    results = []
    first_spiking_sweep = None
    first_spike_idx = None
    first_spike_times = None
    first_step_amp = None

    for sweep in abf.sweepList:
        abf.setSweep(sweep, channel=voltage_channel)

        t = abf.sweepX
        v = abf.sweepY
        cmd = abf.sweepC

        step_amp = step_amplitude_from_command(cmd)

        spike_times, spike_idx = detect_spikes_dvdt(
            t,
            v,
            window=window,
            dvdt_thresh_mV_per_ms=dvdt_thresh_mV_per_ms,
            refractory_ms=refractory_ms,
        )

        results.append((step_amp, int(len(spike_times))))

        if first_spiking_sweep is None and spike_times.size > 0:
            first_spiking_sweep = sweep
            first_spike_idx = spike_idx
            first_spike_times = spike_times
            first_step_amp = step_amp

    # Save CSV
    df = pd.DataFrame(results, columns=["CurrentStep", "SpikeCount"])
    if out_csv_path is None:
        base, _ = os.path.splitext(abf_path)
        out_csv_path = base + "_spike_counts.csv"
    df.to_csv(out_csv_path, index=False)
    print(f"Saved CSV: {out_csv_path}")

    # Plot first spiking step (single sweep)
    if first_spiking_sweep is None:
        print("No spikes detected in any sweep with the current criteria.")
        # Even if no spikes, you may still want the multi-panel plot:
        if make_multipanel:
            plot_multi_panel_sweeps(
                abf,
                window=window,
                dvdt_thresh_mV_per_ms=dvdt_thresh_mV_per_ms,
                refractory_ms=refractory_ms,
                voltage_channel=voltage_channel,
                exclude_first_n=2,
                n_panels=12,
                nrows=3,
                ncols=4,
            )
        return df

    abf.setSweep(first_spiking_sweep, channel=voltage_channel)
    t = abf.sweepX
    v = abf.sweepY

    plt.figure(figsize=(10, 4))
    plt.plot(t, v, linewidth=1)
    plt.scatter(t[first_spike_idx], v[first_spike_idx], s=15, zorder=3, c = "red")

    t0, t1 = window
    plt.axvspan(t0, t1, alpha=0.15)

    plt.xlabel("Time (s)")
    plt.ylabel("Voltage (mV)")
    plt.title(
        f"First spiking step: {first_step_amp:g} (sweep {first_spiking_sweep}) | "
        f"spikes in window = {len(first_spike_times)} | dV/dt > {dvdt_thresh_mV_per_ms} mV/ms"
    )
    plt.tight_layout()
    plt.show()

    print(f"First spiking sweep: {first_spiking_sweep}")
    print(f"First spiking step amplitude: {first_step_amp:g}")
    print(f"Spike count in {window[0]}–{window[1]} s: {len(first_spike_times)}")

    # ---------------------------
    # THIS IS WHERE YOU CALL IT
    # ---------------------------
    if make_multipanel:
        plot_multi_panel_sweeps(
            abf,
            window=window,
            dvdt_thresh_mV_per_ms=dvdt_thresh_mV_per_ms,
            refractory_ms=refractory_ms,
            voltage_channel=voltage_channel,
            exclude_first_n=2,   # exclude first 2 sweeps
            n_panels=12,         # plot 12 sweeps total
            nrows=3,
            ncols=4,
        )

    return df


# ---------------------------
# EDIT THIS PATH AND RUN
# ---------------------------
if __name__ == "__main__":
    abf_file = r"C:\Users\meagh\Box\CreedLabBoxDrive\Collabs\Pena_Sedt7_VTA\2026RevisionExpts\IO\SR\260212_10LF_2026_02_12_0063.abf"  # <-- change this
    analyze_abf(
        abf_file,
        window=(0.1, 2.15),
        dvdt_thresh_mV_per_ms=10.0,
        refractory_ms=2.0,
        voltage_channel=0,
        make_multipanel=True,  # multi-panel plot on/off
    )