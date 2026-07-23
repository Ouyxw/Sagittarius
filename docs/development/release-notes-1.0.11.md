# Sagittarius 1.0.11 Release Notes

**Status:** Published to production PyPI on 2026-07-23.

## Highlights

- Fixed Python wheel package discovery so `sagittarius` subpackages, including `sagittarius.viz`, are installed in the `sagittarius-py` wheel.
- Fixed the Julia CUDA solver world-age failure that could occur when CUDA was loaded dynamically immediately before a GPU ODE callback.
- Preserved the backend-free visualization and result-export workflow in the released wheel.

## Upgrade

Upgrade an existing environment with:

```bash
python -m pip install --upgrade "sagittarius-py==1.0.11"
sagittarius backend resolve
sagittarius doctor
```

New users can install the same version in an isolated virtual environment. The default profile is CPU-first; CUDA remains experimental and requires explicit backend setup and compatible NVIDIA hardware.

## Compatibility and Migration

The immutable `1.0.10` files remain available on PyPI, but its wheel omitted `sagittarius.viz`. Users who need visualization helpers should upgrade to `1.0.11`; no source-checkout workaround is required for the published `1.0.11` wheel.

No run-manifest, result-artifact, shared-result, doctor, or event-taxonomy schema version changed in this release.

## Release Identity and Evidence

- Production tag: [`v1.0.11`](https://github.com/Ouyxw/Sagittarius/tree/v1.0.11)
- Frozen commit: `66b2cce519a8ee88d11edc1f300e5e9b7754c10e`
- Canonical candidate: [`candidate/sagittarius-py-v1.0.11-4`](https://github.com/Ouyxw/Sagittarius/tree/candidate/sagittarius-py-v1.0.11-4)
- Canonical candidate workflow: [Phase 13 run 29989396534](https://github.com/Ouyxw/Sagittarius/actions/runs/29989396534)
- Production package: [sagittarius-py 1.0.11](https://pypi.org/project/sagittarius-py/1.0.11/)
- Complete gate, artifact, and distribution-hash record: [1.0.11 release evidence](release-evidence-1.0.11.md)
