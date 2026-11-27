| row_id | mode | status | workload | atom_count | full_dim | basis_size | repeats | total_time_s | time_per_operation_s | median_batch_time_s | reference_error | reference_relative_error | max_rss | max_rss_unit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chain-n4-full_dense | full_dense | passed | matvec | 4 | 16 | 16 | 50 | 1.7192e-05 | 3.4384e-07 | 1.7163e-05 | 0 | 0 | 924648 | KiB on Linux, bytes on macOS |
| chain-n4-full_sparse | full_sparse | passed | matvec | 4 | 16 | 16 | 50 | 0.000123288 | 2.46576e-06 | 0.000123288 | 2.54762e-16 | 7.64172e-17 | 919504 | KiB on Linux, bytes on macOS |
| chain-n4-reduced_matrix_free | reduced_matrix_free | passed | matvec | 4 | 16 | 8 | 50 | 0.000433423 | 8.66846e-06 | 0.0004534 | 4.44428e-16 | 1.34722e-16 | 923732 | KiB on Linux, bytes on macOS |
| chain-n4-reduced_sparse | reduced_sparse | passed | matvec | 4 | 16 | 8 | 50 | 0.000107119 | 2.14238e-06 | 0.000120641 | 4.44428e-16 | 1.34722e-16 | 923548 | KiB on Linux, bytes on macOS |
| chain-n4-reduced_sparse_gpu_cached | reduced_sparse_gpu_cached | skipped | ode_solve | 4 | 16 | 8 | None | None | None | None | None | None | None | None |
| chain-n8-full_dense | full_dense | passed | matvec | 8 | 256 | 256 | 50 | 0.000502846 | 1.00569e-05 | 0.000497203 | 0 | 0 | 930352 | KiB on Linux, bytes on macOS |
| chain-n8-full_sparse | full_sparse | passed | matvec | 8 | 256 | 256 | 50 | 0.000205815 | 4.1163e-06 | 0.000205815 | 2.48253e-16 | 1.37841e-16 | 940956 | KiB on Linux, bytes on macOS |
| chain-n8-reduced_matrix_free | reduced_matrix_free | passed | matvec | 8 | 256 | 55 | 50 | 0.00514611 | 0.000102922 | 0.00521909 | 4.57757e-16 | 1.96125e-16 | 924876 | KiB on Linux, bytes on macOS |
| chain-n8-reduced_sparse | reduced_sparse | passed | matvec | 8 | 256 | 55 | 50 | 0.000126774 | 2.53548e-06 | 0.000126774 | 4.57757e-16 | 1.96125e-16 | 940084 | KiB on Linux, bytes on macOS |
| chain-n8-reduced_sparse_gpu_cached | reduced_sparse_gpu_cached | skipped | ode_solve | 8 | 256 | 55 | None | None | None | None | None | None | None | None |
| chain-n12-full_dense | full_dense | passed | matvec | 12 | 4096 | 4096 | 50 | 0.228889 | 0.00457778 | 0.209337 | 2.28878e-16 | 2.28878e-16 | 1013060 | KiB on Linux, bytes on macOS |
| chain-n12-full_sparse | full_sparse | passed | matvec | 12 | 4096 | 4096 | 50 | 0.00210471 | 4.20942e-05 | 0.00197795 | 2.37144e-16 | 2.37144e-16 | 1022332 | KiB on Linux, bytes on macOS |
| chain-n12-reduced_matrix_free | reduced_matrix_free | passed | matvec | 12 | 4096 | 377 | 50 | 0.0577117 | 0.00115423 | 0.0577117 | 2.48253e-16 | 2.42637e-16 | 924500 | KiB on Linux, bytes on macOS |
| chain-n12-reduced_sparse | reduced_sparse | passed | matvec | 12 | 4096 | 377 | 50 | 0.000241733 | 4.83466e-06 | 0.00022863 | 2.48253e-16 | 2.42637e-16 | 921980 | KiB on Linux, bytes on macOS |
| chain-n12-reduced_sparse_gpu_cached | reduced_sparse_gpu_cached | skipped | ode_solve | 12 | 4096 | 377 | None | None | None | None | None | None | None | None |
| chain-n16-full_dense | full_dense | skipped | matvec | 16 | 65536 | 65536 | None | None | None | None | None | None | None | None |
| chain-n16-full_sparse | full_sparse | skipped | matvec | 16 | 65536 | 65536 | None | None | None | None | None | None | None | None |
| chain-n16-reduced_matrix_free | reduced_matrix_free | passed | matvec | 16 | 65536 | 2584 | 50 | 0.581942 | 0.0116388 | 0.580886 | 1.24127e-16 | 1.24127e-16 | 938584 | KiB on Linux, bytes on macOS |
| chain-n16-reduced_sparse | reduced_sparse | passed | matvec | 16 | 65536 | 2584 | 50 | 0.00104895 | 2.09789e-05 | 0.00104895 | 1.24127e-16 | 1.24127e-16 | 967524 | KiB on Linux, bytes on macOS |
| chain-n16-reduced_sparse_gpu_cached | reduced_sparse_gpu_cached | skipped | ode_solve | 16 | 65536 | 2584 | None | None | None | None | None | None | None | None |
| chain-n20-full_dense | full_dense | skipped | matvec | 20 | 1048576 | 1048576 | None | None | None | None | None | None | None | None |
| chain-n20-full_sparse | full_sparse | skipped | matvec | 20 | 1048576 | 1048576 | None | None | None | None | None | None | None | None |
| chain-n20-reduced_matrix_free | reduced_matrix_free | passed | matvec | 20 | 1048576 | 17711 | 50 | 5.5634 | 0.111268 | 5.5017 | 8.32667e-17 | 8.32667e-17 | 964936 | KiB on Linux, bytes on macOS |
| chain-n20-reduced_sparse | reduced_sparse | passed | matvec | 20 | 1048576 | 17711 | 50 | 0.00849572 | 0.000169914 | 0.00849572 | 8.32667e-17 | 8.32667e-17 | 1394248 | KiB on Linux, bytes on macOS |
| chain-n20-reduced_sparse_gpu_cached | reduced_sparse_gpu_cached | skipped | ode_solve | 20 | 1048576 | 17711 | None | None | None | None | None | None | None | None |
