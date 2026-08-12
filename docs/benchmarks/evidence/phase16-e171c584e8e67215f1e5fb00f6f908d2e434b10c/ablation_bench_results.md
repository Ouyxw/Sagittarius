| mode | status | backend | workload | representation | atom_count | full_dim | basis_size | repeats | duration_s | total_time_s | time_per_operation_s | reference_error | max_rss | max_rss_unit | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_dense | passed | {'requested_backend': 'CUDA'} | matvec | full dense matrix | 12 | 4096 | 4096 | 50 | None | 0.0672473 | 0.00134495 | 1.88388e+66 | 153468 | KiB on Linux, bytes on macOS |  |
| full_sparse | passed | {'requested_backend': 'CUDA'} | matvec | full sparse CSR matrix | 12 | 4096 | 4096 | 50 | None | 0.00211221 | 4.22441e-05 | 1.88388e+66 | 155888 | KiB on Linux, bytes on macOS |  |
| reduced_matrix_free | passed | {'requested_backend': 'CUDA'} | matvec | blockade-reduced matrix-free operator | 12 | 4096 | 377 | 50 | None | 0.0722425 | 0.00144485 | 0 | 155888 | KiB on Linux, bytes on macOS |  |
| reduced_sparse | passed | {'requested_backend': 'CUDA'} | matvec | blockade-reduced sparse CSR matrix | 12 | 4096 | 377 | 50 | None | 0.000244786 | 4.89572e-06 | 0 | 157684 | KiB on Linux, bytes on macOS |  |
| reduced_sparse_gpu_cached | passed | {'requested_backend': 'CUDA'} | ode_solve | blockade-reduced cached sparse matrix | 12 | 4096 | 377 | 1 | 0.2 | 31.9902 | 31.9902 |  | 3285936 | KiB on Linux, bytes on macOS |  |
