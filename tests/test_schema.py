from app.config.analysis_schema import get_analysis_schema


def test_schema_defaults():
    schema = get_analysis_schema(None)
    cols = [c["key"] for c in schema["parallels"]["columns"]]
    assert cols[:4] == ["num", "m1", "m2", "m3"]


def test_schema_mt_mad_vad_share_columns():
    for code in ["MT", "Mad", "Aad", "Vad"]:
        schema = get_analysis_schema(code)
        cols = [c["key"] for c in schema["parallels"]["columns"]]
        assert cols[:4] == ["num", "m1", "m2", "m3"]
        assert "result" in cols


def test_schema_csn_variable_columns():
    schema = get_analysis_schema("CSN")
    cols = [c["key"] for c in schema["parallels"]["columns"]]
    # CSN нь v1..v5 гэсэн 5 багана
    assert cols == ["v1", "v2", "v3", "v4", "v5"]
