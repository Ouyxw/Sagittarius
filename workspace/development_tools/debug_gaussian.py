import numpy as np
from sagittarius.viz import sample_pulse_waveform

times = np.linspace(0, 5, 100)
pulse_dict = {'type': 'gaussian', 'amplitude': 3.0, 'sigma': 1.0, 'duration': 5.0, 'mu': 2.5}

vals = sample_pulse_waveform(pulse_dict, times)
print('Values at t=0, 1, 2, 2.5, 3, 4, 5:')
for i in [0, 20, 40, 50, 60, 80, 99]:
    print(f'  t={times[i]:.2f}: {vals[i]:.4f}')

peak_idx = np.argmax(vals)
peak_time = 5.0 * peak_idx / 99
print(f'\nPeak index: {peak_idx}')
print(f'Peak time: {peak_time:.2f}')
print(f'Expected: 2.5')
print(f'Difference: {abs(peak_time - 2.5):.2f}')
