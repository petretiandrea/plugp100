from plugp100.models.power import PowerInfo


def test_power_info_missing_current_power_returns_none():
    power_info = PowerInfo({})

    assert power_info.current_power is None
