from app.config.repeatability import LIMIT_RULES


def test_limit_rules_have_required_structure():
    """Every entry must define either single or bands with limit/mode."""
    assert LIMIT_RULES, "LIMIT_RULES should not be empty"
    for code, rule in LIMIT_RULES.items():
        assert isinstance(rule, dict), f"{code} rule must be dict"
        single = rule.get("single")
        bands = rule.get("bands") or rule.get("bands_detailed")
        assert single or bands, f"{code} must have single or bands"
        if single:
            assert "limit" in single and "mode" in single, f"{code} single must have limit/mode"
        if bands:
            assert isinstance(bands, list) and bands, f"{code} bands must be non-empty list"
            for b in bands:
                assert {"upper", "limit", "mode"} <= set(b.keys()), f"{code} band missing keys"
