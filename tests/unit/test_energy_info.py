from plugp100.models.energy import EnergyInfo


def test_energy_info_missing_today_energy_returns_none():
    energy_info = EnergyInfo(
        {
            "today_runtime": 12,
            "month_runtime": 120,
            "month_energy": 456,
            "current_power": 78,
        }
    )

    assert energy_info.today_energy is None
    assert energy_info.month_energy == 456
    assert energy_info.current_power == 78
