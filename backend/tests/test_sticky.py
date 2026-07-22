from app.core.calc.sticky import resolve_sticky_series


def test_flat_carry_forward_and_override_cascade():
    # 2026: 2.5% explicit. 2028: 3.0% explicit override. Horizon 2026-2031.
    explicit = {2026: 0.025, 2028: 0.03}
    resolved = resolve_sticky_series(explicit, 2026, 2031, mode="flat")

    assert resolved[2026] == (0.025, True, 2026)
    assert resolved[2027] == (0.025, False, 2026)
    assert resolved[2028] == (0.03, True, 2028)
    assert resolved[2029] == (0.03, False, 2028)
    assert resolved[2030] == (0.03, False, 2028)
    assert resolved[2031] == (0.03, False, 2028)


def test_flat_no_explicit_value_yet_is_none():
    resolved = resolve_sticky_series({}, 2026, 2028, mode="flat")
    assert resolved[2026].value is None
    assert resolved[2026].is_explicit is False
    assert resolved[2028].value is None


def test_growth_mode_compounds_using_resolved_growth_rate():
    contributions = {2026: 50_000.0}
    growth_rates = {2026: 0.0, 2027: 0.02, 2028: 0.02}
    resolved = resolve_sticky_series(
        contributions, 2026, 2028, mode="growth", growth_rate_by_year=growth_rates
    )
    assert resolved[2026].value == 50_000.0
    assert resolved[2026].is_explicit is True
    assert round(resolved[2027].value, 2) == 51_000.0
    assert resolved[2027].is_explicit is False
    assert resolved[2027].source_year == 2026
    assert round(resolved[2028].value, 2) == 52_020.0


def test_growth_mode_override_resets_anchor():
    contributions = {2026: 50_000.0, 2028: 60_000.0}
    growth_rates = {2027: 0.02, 2029: 0.05}
    resolved = resolve_sticky_series(
        contributions, 2026, 2029, mode="growth", growth_rate_by_year=growth_rates
    )
    assert resolved[2028] == (60_000.0, True, 2028)
    assert round(resolved[2029].value, 2) == 63_000.0
    assert resolved[2029].source_year == 2028
