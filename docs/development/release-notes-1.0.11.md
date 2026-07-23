# Sagittarius 1.0.11 Release Notes

**Status:** Candidate prepared and verified; not yet published to PyPI.

## Fixed

- Fixed Python wheel package discovery to include `sagittarius` subpackages automatically.
- The `sagittarius.viz` visualization package is now included in the `sagittarius-py` wheel.

## Impact on `1.0.10`

The production `sagittarius-py==1.0.10` wheel omits `sagittarius.viz` even though the source tree and Python minimal example document the visualization API.

```python
from sagittarius.viz import plot_register
```

raises `ModuleNotFoundError` after installing the 1.0.10 wheel from PyPI.

The immutable 1.0.10 PyPI distributions are not replaced. This packaging defect is corrected by the forthcoming 1.0.11 distribution.

## Candidate Verification

- Freeze commit: `883252060e14e2306c5b7fa90f3ce9bd1533da5e`
- Candidate tag: `candidate/sagittarius-py-v1.0.11-1`
- Canonical candidate artifact: [Phase 13 run 29982489803](https://github.com/Ouyxw/Sagittarius/actions/runs/29982489803) — success.
- The release artifact regression test verifies that every `sagittarius/viz/*.py` source module is present in the wheel, and an isolated wheel-install smoke imports `sagittarius.viz` from `site-packages`.

## Upgrade

After 1.0.11 is published to production PyPI, install the fixed package with:

```bash
python -m pip install --upgrade "sagittarius-py==1.0.11"
```

Until then, 1.0.10 users requiring visualization helpers should use the documented source-checkout workflow rather than treating a local wheel build as production release evidence.
