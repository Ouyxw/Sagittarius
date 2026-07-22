import numpy as np
from sagittarius.viz import sample_pulse_waveform

times = np.linspace(0, 5, 100)
print('Time points:', times[:3], '...', times[-3:])

pulse_dict = {'type': 'ramp', 'start_val': 0, 'end_val': 4, 'duration': 5}
vals = sample_pulse_waveform(pulse_dict, times)
print('Values at t=0, t=2.5, t=5:', vals[0], vals[50], vals[-1])
print('Expected: 0, 2, 4')
