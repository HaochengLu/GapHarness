# Table 3. Registry-Guarded Post-Hoc Calibration

This is reported as post-hoc registry-boundary calibration after observing a systematic unsupported false-positive pattern.

| Split | Profiler | N | Harness Success | Cost | Oracle | Cost Delta | Excess Cost | Over | Under | Wrong | Unsupported FP |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| dev200 | LLM single | 200 | 0.92 | 3.68 | 3.62 | 0.06 | 0.46 | 0.19 | 0.08 | 0.00 | 14 |
| dev200 | registry guard | 200 | 0.97 | 4.01 | 3.62 | 0.40 | 0.47 | 0.20 | 0.03 | 0.00 | 4 |
| test800 | LLM single | 800 | 0.89 | 3.59 | 3.69 | -0.09 | 0.37 | 0.14 | 0.09 | 0.01 | 56 |
| test800 | registry guard | 800 | 0.94 | 3.98 | 3.69 | 0.30 | 0.38 | 0.15 | 0.03 | 0.01 | 12 |
