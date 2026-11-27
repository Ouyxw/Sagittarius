| row_id | mode | status | workload | atom_count | full_dim | basis_size | repeats | total_time_s | time_per_operation_s | median_batch_time_s | reference_error | reference_relative_error | max_rss | max_rss_unit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chain-n4-reduced_sparse_gpu_cached | reduced_sparse_gpu_cached | passed | ode_solve | 4 | 16 | 8 | 1 | 0.391586 | 0.391586 | 0.391586 | None | None | 2049572 | KiB on Linux, bytes on macOS |
| chain-n8-reduced_sparse_gpu_cached | reduced_sparse_gpu_cached | passed | ode_solve | 8 | 256 | 55 | 1 | 0.422898 | 0.422898 | 0.455271 | None | None | 2013156 | KiB on Linux, bytes on macOS |
| chain-n12-reduced_sparse_gpu_cached | reduced_sparse_gpu_cached | passed | ode_solve | 12 | 4096 | 377 | 1 | 0.566215 | 0.566215 | 0.566215 | None | None | 2000000 | KiB on Linux, bytes on macOS |
| chain-n16-reduced_sparse_gpu_cached | reduced_sparse_gpu_cached | passed | ode_solve | 16 | 65536 | 2584 | 1 | 0.542897 | 0.542897 | 0.554233 | None | None | 2105064 | KiB on Linux, bytes on macOS |
| chain-n20-reduced_sparse_gpu_cached | reduced_sparse_gpu_cached | passed | ode_solve | 20 | 1048576 | 17711 | 1 | 1.73345 | 1.73345 | 1.74093 | None | None | 2472764 | KiB on Linux, bytes on macOS |
