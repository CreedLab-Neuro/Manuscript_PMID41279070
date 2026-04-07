import pyabf
import numpy as np
from signal_processing import time_derivative

def get_epoch_features(abf, epoch):
    level = abf.sweepEpochs.levels[epoch]
    start_p = abf.sweepEpochs.p1s[epoch]
    start_t = start_p * abf.dataSecPerPoint
    end_p = abf.sweepEpochs.p2s[epoch]
    end_t = end_p * abf.dataSecPerPoint

    feature_dict = {'level' : level,
                    'start_t' : start_t,
                    'end_t' : end_t,
                    'start_p' : start_p,
                    'end_p' : end_p

                   }
    return feature_dict


def get_rising_edges(trace, crossing):
    rising_edges = np.flatnonzero((trace[:-1] < crossing) & (trace[1:] > crossing))+1
    return rising_edges

def get_falling_edges(trace, crossing):
    falling_edges = np.flatnonzero((trace[:-1] > crossing) & (trace[1:] < crossing))+1
    return falling_edges


def gaussian(x, amplitude, mean, stddev):
    return amplitude * np.exp(-((x - mean) / (2 * stddev))**2)


def test_pulse_qc_vc(abf, epoch=1):
    peak_window = 0.001
    ss_window = 0.01
    t = abf.sweepX
    i = abf.sweepY
    dt = t[1] - t[0]
    peak_window_p = int(peak_window/dt)
    ss_window_p = int(ss_window/dt)
    tp_f = get_epoch_features(abf, epoch)
    start_p = tp_f['start_p']
    end_p = tp_f['end_p']
    v_amp = tp_f['level']
    i_start = i[start_p]
    i_end = i[end_p]
    i_ss = np.mean(i[end_p - ss_window_p:end_p])
    
    if tp_f['level'] < 0:
        onset_peak = np.min(i[start_p:start_p + peak_window_p])
        offset_peak = np.max(i[end_p:end_p + peak_window_p])
    elif tp_f['level'] > 0:
        onset_peak = np.max(i[start_p:start_p + peak_window_p])
        offset_peak = np.min(i[end_p:end_p +peak_window_p])
    onset_delta = abs(onset_peak - i_start)
    offset_delta = abs(offset_peak - i_end)
    onset_avg = 0.5 * (onset_delta + offset_delta)
    ss_delta = i_ss - i_start

    
    Rs = (abs(v_amp) * 1e-3) / (onset_avg * 1e-12) / 1e6 ##in MOhm
    Ri = (v_amp * 1e-3) / (ss_delta * 1e-12) / 1e6 ##in MOhm
    ep0_i = np.nan
    ep0_var_i = np.nan
    if epoch!=0:
        tp_f0 = get_epoch_features(abf, 0)
        end_p = tp_f0['end_p']
        ep0_i = np.mean(i[:end_p])
        ep0_var_i = np.var(i[:end_p])
        end_baseline_i = np.mean(i[-end_p:])
        end_var_i = np.var(i[-end_p:])
    
    test_pulse_dict = {
        'ep0_i' : ep0_i,
        'ep0_var_i' : ep0_var_i,
        'end_base_i' : end_baseline_i,
        'end_base_var' : end_var_i,
        'tp_i_start' : i_start,
        'tp_i_end' : i_end,
        'tp_onset_peak' : onset_delta,
        'tp_offset_peak' : offset_delta,
        'tp_ss_delta' : ss_delta,
        'tp_Rs' : Rs, 
        'tp_Ri' : Ri
    }
    return test_pulse_dict

def basic_stats(arr):
    mean = np.mean(arr)
    sd = np.std(arr)
    n = len(arr)
    if mean != 0:
        cv = sd/mean
    else:
        cv = np.nan
    min_p = np.argmin(arr)
    min_val = np.min(arr)
    max_p = np.argmax(arr)
    max_val = np.max(arr)

    stats_dict = {
    'mean' : mean,
    'sd' : sd, 
    'n': n,
    'cv' : cv,
    'min_p' : min_p,
    'min_val': min_val,
    'max_p': max_p,
    'max_val': max_val
    }

    return stats_dict


def response_stats(signal, t, t_start=None, t_stop=None, baseline_start=None, baseline_stop=None, sd_factor=4, stim_t=None):
    '''t_start, t_stop are time window to analyze. 
    baseline_start, baseline_stop are time window to get baseline features. 
    sd_factor * baseline_sd determines onset threshold
    stim_t is a provided stim time to calculate latency (may not necessarily be == t_start to avoid stim artifacts)
    This does not work when t includes negative values.
    '''
    if t_start == None:
        t_start = min(t)
    if t_stop == None:
        t_stop = max(t)


    dsig_dt = time_derivative(signal, t)
    dt = t[1] - t[0]
    p_start = round(t_start/dt)
    p_stop = round(t_stop/dt)
    
    response_chunk = signal[p_start:p_stop]
    ds_chunk = dsig_dt[p_start:p_stop]

    peak_p = np.argmax(response_chunk) + p_start
    peak_sig = signal[peak_p]
    peak_t = t[peak_p]

    trough_p = np.argmin(response_chunk) + p_start
    trough_sig = signal[trough_p]
    trough_t = t[trough_p]

    dsig_peak_p = np.argmax(ds_chunk) + p_start
    peak_dsig = dsig_dt[dsig_peak_p]
    peak_dsig_t = t[dsig_peak_p]

    dsig_trough_p = np.argmin(ds_chunk) + p_start
    trough_dsig = dsig_dt[dsig_trough_p]
    trough_dsig_t = t[dsig_trough_p]

    response_stats_dict = {
    't_start': t_start,
    't_stop': t_stop,
    'peak': peak_sig,
    'peak_t': peak_t,
    'trough': trough_sig,
    'trough_t': trough_t,
    'max_slope': peak_dsig,
    'max_slope_t': peak_dsig_t,
    'min_slope': trough_dsig,
    'min_slope_t': trough_dsig_t
    }

    if stim_t != None:
        response_stats_dict['stim_t'] = stim_t

    if baseline_start != None and baseline_stop != None:
        
        ##subset baseline signal and get stats
        bl_start = round(baseline_start/dt)
        bl_stop = round(baseline_stop/dt)
        baseline_chunk = signal[bl_start:bl_stop]
        bl_stats = basic_stats(baseline_chunk)
        bl_mean = bl_stats['mean']
        bl_sd = bl_stats['sd']
        response_stats_dict['baseline_mean'] = bl_mean
        response_stats_dict['baseline_sd'] = bl_sd
        response_offset = response_chunk - bl_mean

        ##add amplitudes
        
        peak_amp = peak_sig - bl_mean
        trough_amp = trough_sig - bl_mean
        response_stats_dict['peak_amp'] = peak_amp
        response_stats_dict['trough_amp'] = trough_amp

        ##get integral using offset chunk
        integral = np.trapz(response_offset, dx=dt)
        response_stats_dict['total_integral'] = integral

        ##determine thresholds for +/- going response
        pos_thresh = bl_mean + sd_factor * bl_sd
        neg_thresh = bl_mean - sd_factor * bl_sd

        ##find crossing of thresholds
        pos_onset = (get_rising_edges(response_chunk, pos_thresh) + p_start) * dt
        neg_onset = (get_falling_edges(response_chunk, neg_thresh) + p_start) * dt
        pos_offset = (get_falling_edges(response_chunk, pos_thresh) + p_start) * dt
        neg_offset = (get_rising_edges(response_chunk, neg_thresh) + p_start) * dt

        #factors of amplitude for risetime and fwhm
        amp_factors = [0.1, 0.5, 0.9]

        rise_times = {}

        if len(neg_onset) > 0:
            #print ("negative onset detected")
            neg_on0 = neg_onset[0]
            response_stats_dict['neg_on0'] = neg_on0
            if stim_t != None:
                response_stats_dict['neg_latency'] = neg_on0 - stim_t
            
            for factor in amp_factors:
                cross_val = factor * trough_amp + bl_mean
                cross_p = get_falling_edges(response_chunk, cross_val) + p_start
                if len(cross_p) > 0:
                    cross_t = t[cross_p[0]]
                else:
                    cross_t = np.nan
                key_name = 'neg_rise_'+str(factor)
                rise_times[key_name] = cross_t
                #neg_cross_t[ix] = cross_t

            ##find rising edges at half max
            cross_val = 0.5 * trough_amp + bl_mean    
            re_halfmax = get_rising_edges(response_chunk, cross_val) + p_start
            ##if any rising eges after the trough (should be for FWHM)
            if (re_halfmax > trough_p).any():
                ##take first rising edge after the peak
                halfmax_end = re_halfmax[re_halfmax > trough_p][0]
                halfmax_end_t = t[halfmax_end]
                neg_fwhm = halfmax_end_t - rise_times['neg_rise_0.5']
                response_stats_dict['neg_fwhm'] = neg_fwhm
                response_stats_dict['neg_hm_end_t'] = halfmax_end_t
            if len(neg_offset) < 1:
                print (f"negative onset detected at {neg_on0}, but return to baseline not found before time {t_stop}")
            else:
                neg_off0 = neg_offset[0]
                response_stats_dict['neg_off0'] = neg_off0
                response_stats_dict['neg_duration'] = neg_off0 - neg_on0


        if len(pos_onset) > 0:
            #print ("positive onset_detected")
            pos_on0 = pos_onset[0]
            response_stats_dict['pos_on0'] = pos_on0
            if stim_t != None:
                response_stats_dict['pos_latency'] = pos_on0 - stim_t

            for factor in amp_factors:
                cross_val = factor * peak_amp + bl_mean
                cross_p = get_rising_edges(response_chunk, cross_val) + p_start
                if len(cross_p) > 0:
                    cross_t = t[cross_p[0]]
                else:
                    cross_t = np.nan
                key_name = 'pos_rise_'+str(factor)
                rise_times[key_name] = cross_t
                #neg_cross_t[ix] = cross_t

            ##find falling edges at half max
            cross_val = 0.5 * peak_amp + bl_mean    
            fe_halfmax = get_falling_edges(response_chunk, cross_val) + p_start
            
            ##if any rising eges after the peak (should be for FWHM)
            if (fe_halfmax > peak_p).any():
                ##take first rising edge after the peak
                halfmax_end = fe_halfmax[fe_halfmax > peak_p][0]
                halfmax_end_t = t[halfmax_end]
                pos_fwhm = halfmax_end_t - rise_times['pos_rise_0.5']
                response_stats_dict['pos_fwhm'] = pos_fwhm
                response_stats_dict['pos_hm_end_t'] = halfmax_end_t
            if len(pos_offset) < 1:
                print (f"positive onset detected at {pos_on0}, but return to baseline not found before time {t_stop}")
            else:
                pos_off0 = pos_offset[0]
                response_stats_dict['pos_off0'] = pos_off0
                response_stats_dict['pos_duration'] = pos_off0 - pos_on0
        response_stats_dict.update(rise_times)
        
        if all(key in response_stats_dict for key in ['neg_rise_0.9', 'neg_rise_0.1']):
            neg10_90_rise_t = response_stats_dict['neg_rise_0.9'] - response_stats_dict['neg_rise_0.1']
            response_stats_dict['neg10_90_rise_t'] = neg10_90_rise_t

        if all(key in response_stats_dict for key in ['pos_rise_0.9', 'pos_rise_0.1']):
            pos10_90_rise_t = response_stats_dict['pos_rise_0.9'] - response_stats_dict['pos_rise_0.1']
            response_stats_dict['pos10_90_rise_t'] = pos10_90_rise_t


    return response_stats_dict


def make_dig_train(abf):
    '''makes an array representing digital output for abf files when high logic used for trains.
    abf.sweepD does not work in these cases. Assumes all trains are digital output on and digital output off
    for all other epochs.'''
    dig_out = np.zeros(max(abf.sweepEpochs.p2s))
    for ix, ep_type in enumerate(abf.sweepEpochs.types):
        if ep_type == 'Pulse':
            pulse_w = abf.sweepEpochs.pulseWidths[ix]
            pulse_per = abf.sweepEpochs.pulsePeriods[ix]
            p1 = abf.sweepEpochs.p1s[ix]
            p2 = abf.sweepEpochs.p2s[ix]
            p = p1
            while(p < p2):
                dig_out[p:p+pulse_w] = 1
                p += pulse_per
    return dig_out