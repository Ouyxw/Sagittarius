import sys


def test_import_does_not_initialize_juliacall():
    sys.modules.pop("sagittarius", None)
    sys.modules.pop("juliacall", None)

    import sagittarius

    assert "juliacall" not in sys.modules
    assert sagittarius.backend_maturity()["CUDA"]["status"] == "experimental"


def test_doctor_cpu_without_backend_initialization():
    from sagittarius import doctor, version_info

    report = doctor()

    assert report["requested_backend"] == "CPU"
    assert report["available"] is True
    assert report["runtime"]["package_version"]
    assert version_info()["julia_version"] is None
