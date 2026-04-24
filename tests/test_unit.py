"""
Unit tests for deterministic logic in logic_engine.py.
No API calls — runs fast on every CI pass.
"""

import pytest
from logic_engine import derive_sop_flags, apply_sop_rules, determine_overall_status


# ── Helpers ───────────────────────────────────────────────────────────────────

def _blank_facts(**overrides):
    """Minimal facts dict with all nullable fields set to None."""
    base = {
        "dental_last_visit_within_6_months": None,
        "dental_pending_work": None,
        "active_smoker": None,
        "smoking_quit_within_3_months": None,
        "has_pt_history": None,
        "hba1c_value": None,
        "daily_opioid_use": None,
        "opioid_duration_months": None,
        "recent_egd_within_3_months": None,
        "has_registered_dietician": None,
        "prior_weight_loss_surgery": None,
    }
    base.update(overrides)
    return base


def _all_clear_flags():
    return {
        "dental_clearance_needed": False,
        "active_smoker": False,
        "no_pt_history": False,
        "hba1c_elevated": False,
        "daily_opioid_over_3_months": False,
        "prior_weight_loss_surgery": False,
        "no_recent_egd": False,
        "no_registered_dietician": False,
    }


# ── GEN-001: Dental clearance ─────────────────────────────────────────────────

class TestDentalClearance:
    def test_recent_visit_no_pending_no_flag(self):
        flags = derive_sop_flags(_blank_facts(dental_last_visit_within_6_months=True, dental_pending_work=False))
        assert flags["dental_clearance_needed"] is False

    def test_no_visit_triggers(self):
        flags = derive_sop_flags(_blank_facts(dental_last_visit_within_6_months=False, dental_pending_work=False))
        assert flags["dental_clearance_needed"] is True

    def test_pending_work_triggers_even_with_recent_visit(self):
        # Pending crown overrides a recent visit — both Raymond and Trevor cases
        flags = derive_sop_flags(_blank_facts(dental_last_visit_within_6_months=True, dental_pending_work=True))
        assert flags["dental_clearance_needed"] is True

    def test_upcoming_cleaning_not_pending_work(self):
        # Patricia: "cleaning next week" — that's not pending dental work
        flags = derive_sop_flags(_blank_facts(dental_last_visit_within_6_months=True, dental_pending_work=False))
        assert flags["dental_clearance_needed"] is False

    def test_both_null_no_flag(self):
        flags = derive_sop_flags(_blank_facts())
        assert flags["dental_clearance_needed"] is False


# ── JNT-001: Smoking ──────────────────────────────────────────────────────────

class TestSmoking:
    def test_active_smoker_triggers(self):
        flags = derive_sop_flags(_blank_facts(active_smoker=True, smoking_quit_within_3_months=False))
        assert flags["active_smoker"] is True

    def test_quit_within_3_months_triggers(self):
        # Denise: quit 6 weeks ago — still inside the 3-month window
        flags = derive_sop_flags(_blank_facts(active_smoker=False, smoking_quit_within_3_months=True))
        assert flags["active_smoker"] is True

    def test_quit_long_ago_no_flag(self):
        # Dorothy: quit in 1987 — well past 3 months
        flags = derive_sop_flags(_blank_facts(active_smoker=False, smoking_quit_within_3_months=False))
        assert flags["active_smoker"] is False

    def test_never_smoked_no_flag(self):
        flags = derive_sop_flags(_blank_facts(active_smoker=False, smoking_quit_within_3_months=None))
        assert flags["active_smoker"] is False

    def test_null_smoking_no_flag(self):
        flags = derive_sop_flags(_blank_facts())
        assert flags["active_smoker"] is False


# ── JNT-002: Physical therapy ─────────────────────────────────────────────────

class TestPhysicalTherapy:
    def test_has_pt_false_triggers(self):
        flags = derive_sop_flags(_blank_facts(has_pt_history=False))
        assert flags["no_pt_history"] is True

    def test_has_pt_true_no_flag(self):
        flags = derive_sop_flags(_blank_facts(has_pt_history=True))
        assert flags["no_pt_history"] is False

    def test_null_pt_does_not_trigger(self):
        # Null means unknown — should NOT be treated as "no PT" and block the case
        flags = derive_sop_flags(_blank_facts(has_pt_history=None))
        assert flags["no_pt_history"] is False


# ── JNT-003: HbA1c ───────────────────────────────────────────────────────────

class TestHbA1c:
    def test_below_threshold_no_flag(self):
        # James: 6.8
        flags = derive_sop_flags(_blank_facts(hba1c_value=6.8))
        assert flags["hba1c_elevated"] is False

    def test_exactly_7_not_elevated(self):
        # Patricia: 7.0 — rule is strictly > 7.0, boundary must NOT fire
        flags = derive_sop_flags(_blank_facts(hba1c_value=7.0))
        assert flags["hba1c_elevated"] is False

    def test_above_threshold_triggers(self):
        flags = derive_sop_flags(_blank_facts(hba1c_value=7.1))
        assert flags["hba1c_elevated"] is True

    def test_high_value_triggers(self):
        # Gerald: 8.2
        flags = derive_sop_flags(_blank_facts(hba1c_value=8.2))
        assert flags["hba1c_elevated"] is True

    def test_null_no_flag(self):
        flags = derive_sop_flags(_blank_facts(hba1c_value=None))
        assert flags["hba1c_elevated"] is False


# ── JNT-004: Opioids ─────────────────────────────────────────────────────────

class TestOpioids:
    def test_daily_under_3_months_no_flag(self):
        flags = derive_sop_flags(_blank_facts(daily_opioid_use=True, opioid_duration_months=2))
        assert flags["daily_opioid_over_3_months"] is False

    def test_daily_exactly_3_months_no_flag(self):
        # Raymond: exactly 3 months — rule is strictly > 3, boundary must NOT fire
        flags = derive_sop_flags(_blank_facts(daily_opioid_use=True, opioid_duration_months=3.0))
        assert flags["daily_opioid_over_3_months"] is False

    def test_daily_over_3_months_triggers(self):
        flags = derive_sop_flags(_blank_facts(daily_opioid_use=True, opioid_duration_months=3.1))
        assert flags["daily_opioid_over_3_months"] is True

    def test_daily_2_years_triggers(self):
        # Gerald / Bob: 24 months daily
        flags = derive_sop_flags(_blank_facts(daily_opioid_use=True, opioid_duration_months=24))
        assert flags["daily_opioid_over_3_months"] is True

    def test_not_daily_no_flag(self):
        # Patricia: tramadol twice a week — not daily
        flags = derive_sop_flags(_blank_facts(daily_opioid_use=False, opioid_duration_months=6))
        assert flags["daily_opioid_over_3_months"] is False

    def test_null_use_no_flag(self):
        flags = derive_sop_flags(_blank_facts(daily_opioid_use=None, opioid_duration_months=None))
        assert flags["daily_opioid_over_3_months"] is False


# ── BAR-001/002/003: Bariatric flags ─────────────────────────────────────────

class TestBariatricFlags:
    def test_prior_surgery_triggers(self):
        flags = derive_sop_flags(_blank_facts(prior_weight_loss_surgery=True))
        assert flags["prior_weight_loss_surgery"] is True

    def test_no_prior_surgery_no_flag(self):
        flags = derive_sop_flags(_blank_facts(prior_weight_loss_surgery=False))
        assert flags["prior_weight_loss_surgery"] is False

    def test_no_recent_egd_triggers(self):
        flags = derive_sop_flags(_blank_facts(recent_egd_within_3_months=False))
        assert flags["no_recent_egd"] is True

    def test_recent_egd_5_weeks_no_flag(self):
        # Marcus / Camille: EGD 5-6 weeks ago — within 3 months
        flags = derive_sop_flags(_blank_facts(recent_egd_within_3_months=True))
        assert flags["no_recent_egd"] is False

    def test_no_rd_triggers(self):
        flags = derive_sop_flags(_blank_facts(has_registered_dietician=False))
        assert flags["no_registered_dietician"] is True

    def test_has_rd_no_flag(self):
        # Marcus: Sandra Okonkwo, RD — valid credential
        flags = derive_sop_flags(_blank_facts(has_registered_dietician=True))
        assert flags["no_registered_dietician"] is False


# ── apply_sop_rules ───────────────────────────────────────────────────────────

class TestApplySopRules:
    def test_no_flags_no_rules_fired(self):
        assert apply_sop_rules(_all_clear_flags(), "Joint") == []

    def test_joint_rules_dont_fire_for_bariatric(self):
        flags = {**_all_clear_flags(), "active_smoker": True, "no_pt_history": True}
        rule_ids = [r["rule_id"] for r in apply_sop_rules(flags, "Bariatric")]
        assert "JNT-001" not in rule_ids
        assert "JNT-002" not in rule_ids

    def test_bariatric_rules_dont_fire_for_joint(self):
        flags = {**_all_clear_flags(), "prior_weight_loss_surgery": True, "no_recent_egd": True, "no_registered_dietician": True}
        rule_ids = [r["rule_id"] for r in apply_sop_rules(flags, "Joint")]
        assert "BAR-001" not in rule_ids
        assert "BAR-002" not in rule_ids
        assert "BAR-003" not in rule_ids

    def test_gen001_fires_for_joint(self):
        flags = {**_all_clear_flags(), "dental_clearance_needed": True}
        rule_ids = [r["rule_id"] for r in apply_sop_rules(flags, "Joint")]
        assert "GEN-001" in rule_ids

    def test_gen001_fires_for_bariatric(self):
        flags = {**_all_clear_flags(), "dental_clearance_needed": True}
        rule_ids = [r["rule_id"] for r in apply_sop_rules(flags, "Bariatric")]
        assert "GEN-001" in rule_ids

    def test_results_sorted_by_severity(self):
        flags = {
            **_all_clear_flags(),
            "active_smoker": True,              # Deferred — priority 2
            "daily_opioid_over_3_months": True, # High Complexity — priority 1
            "no_pt_history": True,              # Ineligible — priority 0
        }
        result = apply_sop_rules(flags, "Joint")
        statuses = [r["case_status"] for r in result]
        assert statuses[0] == "Ineligible"
        assert statuses[1] == "High Complexity"
        assert statuses[2] == "Deferred"

    def test_all_joint_flags_returns_five_rules(self):
        flags = {
            **_all_clear_flags(),
            "dental_clearance_needed": True,
            "active_smoker": True,
            "no_pt_history": True,
            "hba1c_elevated": True,
            "daily_opioid_over_3_months": True,
        }
        result = apply_sop_rules(flags, "Joint")
        assert len(result) == 5

    def test_all_bariatric_flags_returns_four_rules(self):
        flags = {
            **_all_clear_flags(),
            "dental_clearance_needed": True,
            "prior_weight_loss_surgery": True,
            "no_recent_egd": True,
            "no_registered_dietician": True,
        }
        result = apply_sop_rules(flags, "Bariatric")
        assert len(result) == 4


# ── determine_overall_status ──────────────────────────────────────────────────

class TestOverallStatus:
    def test_no_rules_is_clear(self):
        assert determine_overall_status([]) == "Clear"

    def test_single_rule_returns_its_status(self):
        assert determine_overall_status([{"case_status": "Deferred"}]) == "Deferred"

    def test_ineligible_beats_all_others(self):
        rules = [
            {"case_status": "Deferred"},
            {"case_status": "Ineligible"},
            {"case_status": "Review"},
            {"case_status": "Hold"},
        ]
        assert determine_overall_status(rules) == "Ineligible"

    def test_high_complexity_beats_deferred(self):
        rules = [{"case_status": "Deferred"}, {"case_status": "High Complexity"}]
        assert determine_overall_status(rules) == "High Complexity"

    def test_revision_case_beats_review(self):
        rules = [{"case_status": "Revision Case"}, {"case_status": "Review"}]
        assert determine_overall_status(rules) == "Revision Case"

    def test_action_required_beats_hold(self):
        rules = [{"case_status": "Hold"}, {"case_status": "Action Required"}]
        assert determine_overall_status(rules) == "Action Required"

    def test_gerald_scenario_ineligible(self):
        # All 5 flags fire — Ineligible must win
        rules = [
            {"case_status": "Ineligible"},
            {"case_status": "High Complexity"},
            {"case_status": "Deferred"},
            {"case_status": "Review"},
            {"case_status": "Action Required"},
        ]
        assert determine_overall_status(rules) == "Ineligible"
