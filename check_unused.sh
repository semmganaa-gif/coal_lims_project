#!/bin/bash

# Функц: файл дахь нэр дүрс шалгах
check_function() {
    local func_name=$1
    local file=$2
    local grep_pattern="(import.*$func_name|\b$func_name\s*\()"
    
    # app/ дахь бүх Python файлд хайх (utils папка эс)
    if grep -r "$func_name" app --include="*.py" | grep -v "app/utils/" > /dev/null 2>&1; then
        echo "0"  # Ашиглагдаж байна
    else
        echo "1"  # Ашиглагдаагүй
    fi
}

# Параметр: шалгаж байгаа функцүүдийн жагсаалт
declare -A functions_map

# parameters.py
functions_map["parameters.py"]="get_canonical_name get_parameter_details calculate_value"

# datetime.py
functions_map["datetime.py"]="now_local now_mn"

# codes.py
functions_map["codes.py"]="norm_code to_base_list aliases_of is_alias_of_base"

# conversions.py
functions_map["conversions.py"]="calculate_all_conversions"

# database.py
functions_map["database.py"]="safe_commit safe_delete safe_add"

# audit.py
functions_map["audit.py"]="log_audit get_recent_audit_logs get_user_audit_logs get_resource_audit_logs"

# qc.py
functions_map["qc.py"]="qc_to_date qc_split_family qc_is_composite qc_check_spec parse_numeric eval_qc_status split_stream_key sulfur_map_for"

# security.py
functions_map["security.py"]="escape_like_pattern is_safe_url"

# validators.py
functions_map["validators.py"]="validate_analysis_result validate_sample_id validate_analysis_code validate_equipment_id validate_save_results_batch get_csn_repeatability_limit round_to_half validate_csn_values sanitize_string"

# analysis_rules.py
functions_map["analysis_rules.py"]="determine_result_status"

# normalize.py
functions_map["normalize.py"]="normalize_raw_data _pick_numeric"

# sorting.py
functions_map["sorting.py"]="natural_sort_key custom_sample_sort_key get_client_type_priority sample_full_sort_key sort_samples sort_codes"

# settings.py
functions_map["settings.py"]="get_error_reason_labels get_setting_by_category get_setting_value update_setting get_sample_type_choices_map get_unit_abbreviations"

# shifts.py
functions_map["shifts.py"]="get_shift_info get_12h_shift_code get_quarter_code get_shift_date get_current_shift_start"

# westgard.py
functions_map["westgard.py"]="check_westgard_rules get_qc_status check_single_value"

# decorators.py
functions_map["decorators.py"]="role_required admin_required role_or_owner_required analysis_role_required"

# analysis_assignment.py
functions_map["analysis_assignment.py"]="get_gi_shift_config assign_analyses_to_sample"

# server_calculations.py
functions_map["server_calculations.py"]="verify_and_recalculate bulk_verify_results"

# analysis_aliases.py
functions_map["analysis_aliases.py"]="normalize_analysis_code get_all_aliases_for_base"

# notifications.py
functions_map["notifications.py"]="get_notification_recipients send_notification notify_qc_failure notify_sample_status_change notify_equipment_calibration_due check_and_send_equipment_notifications check_and_notify_westgard"

# repeatability_loader.py
functions_map["repeatability_loader.py"]="load_limit_rules clear_cache"

# exports.py
functions_map["exports.py"]="export_to_excel create_sample_export create_analysis_export create_audit_export send_excel_response"

# quality_helpers.py
functions_map["quality_helpers.py"]="can_edit_quality require_quality_edit calculate_status_stats generate_sequential_code parse_date parse_datetime"

# converters.py
functions_map["converters.py"]="to_float"

# Үр дүн гаргах
for file in "${!functions_map[@]}"; do
    for func in ${functions_map[$file]}; do
        result=$(check_function "$func" "$file")
        if [ "$result" = "1" ]; then
            echo "$file:$func - UNUSED"
        fi
    done
done

