import scipy.signal as signal
from scipy.ndimage import median_filter
import numpy as np


def med_filter(s, t, time_window=0.02):
	dt = t[1] - t[0]
	p_window = round(time_window/dt)
	if p_window%2 == 0:
		p_window -= 1
	return median_filter(s, size=p_window)


def bessel_filter(s, t, freq, f_type="low"):
    dt = t[1] - t[0]
    sample_freq = 1. / dt
    filt_coeff = (freq)/(sample_freq / 2.)
    if filt_coeff < 0 or filt_coeff >= 1:
            raise ValueError("bessel coeff ({:f}) is outside of valid range [0,1); cannot filter sampling frequency {:.1f} kHz with cutoff frequency {:.1f} kHz.".format(filt_coeff, sample_freq / 1e3, filter))
    b, a = signal.bessel(4, filt_coeff, f_type)
    s_filt = signal.filtfilt(b, a, s, axis=0)
    return s_filt


def exp_deconv(sig, t, tau):
    dt = t[1] - t[0]
    deconv = sig[:-1] + (tau / dt) * (sig[1:] - sig[:-1])
    return deconv


def smooth_moving_average(data, window_size):
    """
    Smooths a 1D NumPy array using a moving average.

    Args:
        data (np.ndarray): The 1D array to smooth.
        window_size (int): The size of the moving average window.

    Returns:
        np.ndarray: The smoothed array.
    """
    box = np.ones(window_size) / window_size
    smoothed_data = np.convolve(data, box, mode='same')
    return smoothed_data


def time_derivative(sig, t):
    dsig_dt = (sig[1:] - sig[:-1]) / (t[1:] - t[:-1])
    return dsig_dt


def baseline_mode(sig, t, t_start=None, t_end=None):
    dt = t[1] - t[0]
    if t_start == None:
        t_start = t[0]
        p_start = 0
    else:
    	p_start = round(t_start/dt)
    if t_end == None:
    	t_end = t[-1]
    	p_end = len(t)
    else:
        p_end = round(t_end/dt)
    data = sig[p_start:p_end]
    y, x = np.histogram(data, bins=int((len(data)**0.5)))
    ix = np.argmax(y)
    mode = (x[ix] + x[ix+1])/2
    sig_b = sig - mode
    return sig_b

def baseline_mean(sig, t, t_start=None, t_end=None):
    dt = t[1] - t[0]
    if t_start == None:
        t_start = t[0]
        p_start = 0
    else:
        p_start = round(t_start/dt)
    if t_end == None:
        t_end = t[-1]
        p_end = len(t)
    else:
        p_end = round(t_end/dt)
    data = sig[p_start:p_end]
    mean = np.mean(data)
    sig_b = sig - mean
    return   sig_b