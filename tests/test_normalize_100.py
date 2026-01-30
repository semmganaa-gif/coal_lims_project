# -*- coding: utf-8 -*-
"""
normalize.py модулийн 100% coverage тестүүд

normalize_raw_data болон helper функцүүдийн бүх branch-уудыг тест хийнэ.
"""
import pytest
import json


class TestNormalizeImport:
    """Модуль импорт тест"""

    def test_import_module(self):
        from app.utils import normalize
        assert normalize is not None

    def test_import_function(self):
        from app.utils.normalize import normalize_raw_data
        assert normalize_raw_data is not None

    def test_import_aliases(self):
        from app.utils.normalize import NUM_ALIASES, M1_ALIASES, M2_ALIASES, M3_ALIASES
        assert isinstance(NUM_ALIASES, list)
        assert isinstance(M1_ALIASES, list)
        assert isinstance(M2_ALIASES, list)
        assert isinstance(M3_ALIASES, list)


class TestPickFunction:
    """_pick функцийн тест"""

    def test_pick_first_match(self):
        from app.utils.normalize import _pick
        d = {"num": 1, "box_no": 2}
        result = _pick(d, ["num", "box_no"])
        assert result == 1

    def test_pick_second_match(self):
        from app.utils.normalize import _pick
        d = {"box_no": 2}
        result = _pick(d, ["num", "box_no"])
        assert result == 2

    def test_pick_no_match(self):
        from app.utils.normalize import _pick
        d = {"other": 3}
        result = _pick(d, ["num", "box_no"])
        assert result is None

    def test_pick_none_value(self):
        from app.utils.normalize import _pick
        d = {"num": None, "box_no": 2}
        result = _pick(d, ["num", "box_no"])
        assert result == 2

    def test_pick_empty_string(self):
        from app.utils.normalize import _pick
        d = {"num": "", "box_no": 2}
        result = _pick(d, ["num", "box_no"])
        assert result == 2


class TestNormParallel:
    """_norm_parallel функцийн тест"""

    def test_not_dict(self):
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel("not a dict")
        assert result == {}

    def test_empty_dict(self):
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel({})
        assert result == {}

    def test_with_num(self):
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel({"num": "A1"})
        assert result["num"] == "A1"

    def test_with_m1_m2_m3(self):
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel({
            "m1": "10.5",
            "m2": "15.3",
            "m3": "12.1"
        })
        assert result["m1"] == 10.5
        assert result["m2"] == 15.3
        assert result["m3"] == 12.1

    def test_string_to_float_conversion(self):
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel({"m1": "10.5"})
        assert isinstance(result["m1"], float)

    def test_invalid_string_not_converted(self):
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel({"m1": "abc"})
        assert result.get("m1") == "abc"

    def test_weight_alias(self):
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel({"weight": 10.5})
        assert result["m1"] == 10.5

    def test_result_alias(self):
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel({"res": 5.2})
        assert result["result"] == 5.2

    def test_num_aliases(self):
        from app.utils.normalize import _norm_parallel
        assert _norm_parallel({"box_no": "A1"})["num"] == "A1"
        assert _norm_parallel({"crucible_no": "B2"})["num"] == "B2"
        assert _norm_parallel({"bottle": "C3"})["num"] == "C3"
        assert _norm_parallel({"dish_num": "D4"})["num"] == "D4"

    def test_m1_aliases(self):
        from app.utils.normalize import _norm_parallel
        assert _norm_parallel({"m1_empty": 10})["m1"] == 10
        assert _norm_parallel({"tare": 11})["m1"] == 11
        assert _norm_parallel({"sample_weight": 12})["m1"] == 12

    def test_m2_aliases(self):
        from app.utils.normalize import _norm_parallel
        assert _norm_parallel({"m2_sample": 15})["m2"] == 15
        assert _norm_parallel({"m": 16})["m2"] == 16  # TRD

    def test_m3_aliases(self):
        from app.utils.normalize import _norm_parallel
        assert _norm_parallel({"m3_ashy": 12})["m3"] == 12
        assert _norm_parallel({"m3_dried_box": 13})["m3"] == 13
        assert _norm_parallel({"after_dry": 14})["m3"] == 14

    def test_result_aliases(self):
        from app.utils.normalize import _norm_parallel
        assert _norm_parallel({"value": 5})["result"] == 5

    def test_weight_field_added(self):
        """m1 -> weight давхар хадгалагдана"""
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel({"m1": 10.5})
        assert "weight" in result
        assert result["weight"] == 10.5


class TestNormalizeRawData:
    """normalize_raw_data функцийн тест"""

    def test_empty_dict(self):
        from app.utils.normalize import normalize_raw_data
        result = normalize_raw_data({})
        assert result["p1"] == {}
        assert result["p2"] == {}
        assert result["_schema"]["version"] == 1

    def test_json_string_input(self):
        from app.utils.normalize import normalize_raw_data
        json_str = json.dumps({"p1": {"m1": 10}})
        result = normalize_raw_data(json_str)
        assert result["p1"]["m1"] == 10

    def test_invalid_json_string(self):
        from app.utils.normalize import normalize_raw_data
        result = normalize_raw_data("not json")
        assert result["p1"] == {}

    def test_empty_string(self):
        from app.utils.normalize import normalize_raw_data
        result = normalize_raw_data("")
        assert result["p1"] == {}

    def test_string_not_json_object(self):
        from app.utils.normalize import normalize_raw_data
        result = normalize_raw_data("[1,2,3]")  # Array, not object
        assert result["p1"] == {}

    def test_with_p1_p2(self):
        from app.utils.normalize import normalize_raw_data
        raw = {
            "p1": {"m1": 10, "m2": 15, "result": 5},
            "p2": {"m1": 11, "m2": 16, "result": 5.1}
        }
        result = normalize_raw_data(raw)
        assert result["p1"]["m1"] == 10
        assert result["p2"]["m1"] == 11

    def test_parallels_list(self):
        from app.utils.normalize import normalize_raw_data
        raw = {
            "p1": {"result": 5},
            "p2": {"result": 5.1}
        }
        result = normalize_raw_data(raw)
        assert "parallels" in result
        assert len(result["parallels"]) == 2

    def test_p1_none(self):
        from app.utils.normalize import normalize_raw_data
        raw = {"p1": None}
        result = normalize_raw_data(raw)
        assert result["p1"] == {}

    def test_p2_none(self):
        from app.utils.normalize import normalize_raw_data
        raw = {"p2": None}
        result = normalize_raw_data(raw)
        assert result["p2"] == {}

    def test_diff_and_avg(self):
        from app.utils.normalize import normalize_raw_data
        raw = {"diff": 0.1, "avg": 5.05}
        result = normalize_raw_data(raw)
        assert result["diff"] == 0.1
        assert result["avg"] == 5.05

    def test_diff_empty_ignored(self):
        from app.utils.normalize import normalize_raw_data
        raw = {"diff": "", "avg": None}
        result = normalize_raw_data(raw)
        assert "diff" not in result
        assert "avg" not in result


class TestCsnNormalization:
    """CSN шинжилгээний тусгай тохиолдол"""

    def test_csn_with_v_values(self):
        from app.utils.normalize import normalize_raw_data
        raw = {"v1": 2, "v2": 2.5, "v3": 2, "v4": None, "v5": ""}
        result = normalize_raw_data(raw, analysis_code="CSN")
        assert "parallels" in result
        assert len(result["parallels"]) == 1

    def test_csn_values_converted(self):
        from app.utils.normalize import normalize_raw_data
        raw = {"v1": "2", "v2": "2.5"}
        result = normalize_raw_data(raw, analysis_code="CSN")
        assert result["parallels"][0]["v1"] == 2.0
        assert result["parallels"][0]["v2"] == 2.5

    def test_csn_invalid_value(self):
        from app.utils.normalize import normalize_raw_data
        raw = {"v1": "abc", "v2": 2.5}
        result = normalize_raw_data(raw, analysis_code="CSN")
        # "abc" хөрвүүлэгдэхгүй тул string хэвээр
        assert result["parallels"][0]["v1"] == "abc"

    def test_csn_schema_count(self):
        """CSN parallels үүссэнийг шалгах"""
        from app.utils.normalize import normalize_raw_data
        raw = {"v1": 2, "v2": 2.5, "v3": 3}
        result = normalize_raw_data(raw, analysis_code="CSN")
        # parallels нь CSN утгуудыг агуулна
        assert len(result["parallels"]) == 1
        assert "v1" in result["parallels"][0]
        assert "v2" in result["parallels"][0]
        assert "v3" in result["parallels"][0]

    def test_csn_lowercase(self):
        """Lowercase 'csn' analysis_code"""
        from app.utils.normalize import normalize_raw_data
        raw = {"v1": 2, "v2": 2.5}
        result = normalize_raw_data(raw, analysis_code="csn")
        # CSN parallels үүссэнийг шалгах
        assert "parallels" in result
        assert len(result["parallels"]) == 1


class TestCommonValueAliases:
    """A, B, C нийтлэг утгууд"""

    def test_a_alias(self):
        from app.utils.normalize import normalize_raw_data
        raw = {"A": 100}
        result = normalize_raw_data(raw)
        assert result["A"] == 100

    def test_mass_a_alias(self):
        from app.utils.normalize import normalize_raw_data
        raw = {"mass_a": 100}
        result = normalize_raw_data(raw)
        assert result["A"] == 100

    def test_b_alias(self):
        from app.utils.normalize import normalize_raw_data
        raw = {"B": 50}
        result = normalize_raw_data(raw)
        assert result["B"] == 50

    def test_c_alias(self):
        from app.utils.normalize import normalize_raw_data
        raw = {"dry_mass": 75}
        result = normalize_raw_data(raw)
        assert result["C"] == 75

    def test_string_to_numeric(self):
        from app.utils.normalize import normalize_raw_data
        raw = {"A": "100.5"}
        result = normalize_raw_data(raw)
        assert result["A"] == 100.5


class TestPreserveKeys:
    """Хадгалах талбарууд"""

    def test_fm_fields(self):
        from app.utils.normalize import normalize_raw_data
        raw = {
            "tray_g": 10,
            "before_g": 50,
            "after_g": 45,
            "loss_g": 5,
            "fm_pct": 10
        }
        result = normalize_raw_data(raw)
        assert result["tray_g"] == 10
        assert result["before_g"] == 50
        assert result["fm_pct"] == 10

    def test_cv_fields(self):
        from app.utils.normalize import normalize_raw_data
        raw = {"batch": "B001", "s_used": 0.5, "E": 10500}
        result = normalize_raw_data(raw)
        assert result["batch"] == "B001"
        assert result["s_used"] == 0.5

    def test_repeatability_fields(self):
        from app.utils.normalize import normalize_raw_data
        raw = {"repeatability": 0.05, "t_exceeded": False, "limit_used": 0.1}
        result = normalize_raw_data(raw)
        assert result["repeatability"] == 0.05
        assert result["t_exceeded"] is False

    def test_solid_fields(self):
        from app.utils.normalize import normalize_raw_data
        raw = {"solid_pct": 85, "wet_mass": 100, "formula": "custom"}
        result = normalize_raw_data(raw)
        assert result["solid_pct"] == 85

    def test_empty_preserve_key_ignored(self):
        from app.utils.normalize import normalize_raw_data
        raw = {"tray_g": "", "before_g": None}
        result = normalize_raw_data(raw)
        assert "tray_g" not in result
        assert "before_g" not in result


class TestCvTrdFields:
    """CV болон TRD тусгай талбарууд"""

    def test_cv_m_field(self):
        from app.utils.normalize import normalize_raw_data
        raw = {"p1": {"m": 0.8}, "p2": {"m": 0.82}}
        result = normalize_raw_data(raw)
        assert result["p1"]["m"] == 0.8
        assert result["p2"]["m"] == 0.82

    def test_cv_delta_t_field(self):
        from app.utils.normalize import normalize_raw_data
        raw = {"p1": {"delta_t": 2.5}, "p2": {"delta_t": 2.6}}
        result = normalize_raw_data(raw)
        assert result["p1"]["delta_t"] == 2.5
        assert result["p2"]["delta_t"] == 2.6

    def test_trd_mad_used(self):
        from app.utils.normalize import normalize_raw_data
        raw = {"mad_used": 5.5}
        result = normalize_raw_data(raw)
        assert result["mad_used"] == 5.5

    def test_trd_temp_c(self):
        from app.utils.normalize import normalize_raw_data
        raw = {"temp_c": 20}
        result = normalize_raw_data(raw)
        assert result["temp_c"] == 20

    def test_trd_kt_used(self):
        from app.utils.normalize import normalize_raw_data
        raw = {"kt_used": 0.9982}
        result = normalize_raw_data(raw)
        assert result["kt_used"] == 0.9982


class TestSchemaOutput:
    """_schema output"""

    def test_schema_version(self):
        from app.utils.normalize import normalize_raw_data
        result = normalize_raw_data({})
        assert result["_schema"]["version"] == 1

    def test_schema_parallels_count(self):
        from app.utils.normalize import normalize_raw_data
        raw = {"p1": {"result": 5}, "p2": {"result": 5.1}}
        result = normalize_raw_data(raw)
        assert result["_schema"]["parallels_count"] == 2

    def test_schema_has_parallels_true(self):
        from app.utils.normalize import normalize_raw_data
        raw = {"p1": {"result": 5}}
        result = normalize_raw_data(raw)
        assert result["_schema"]["has_parallels"] is True

    def test_schema_has_parallels_false(self):
        from app.utils.normalize import normalize_raw_data
        result = normalize_raw_data({})
        assert result["_schema"]["has_parallels"] is False


class TestPickNumeric:
    """_pick_numeric функцийн тест"""

    def test_pick_numeric_float(self):
        from app.utils.normalize import _pick_numeric
        d = {"A": 100.5}
        result = _pick_numeric(d, ["A"])
        assert result == 100.5

    def test_pick_numeric_string(self):
        from app.utils.normalize import _pick_numeric
        d = {"A": "100.5"}
        result = _pick_numeric(d, ["A"])
        assert result == 100.5

    def test_pick_numeric_invalid_string(self):
        from app.utils.normalize import _pick_numeric
        d = {"A": "abc"}
        result = _pick_numeric(d, ["A"])
        assert result == "abc"

    def test_pick_numeric_none(self):
        from app.utils.normalize import _pick_numeric
        d = {}
        result = _pick_numeric(d, ["A"])
        assert result is None
