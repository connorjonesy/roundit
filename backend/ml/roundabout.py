"""Urban, all-collision CMFs verified in B.C.'s 2008 report, pp. 99–100."""

import math
from numbers import Real

CMF_SOURCE = "https://www2.gov.bc.ca/assets/gov/driving-and-transportation/transportation-infrastructure/engineering-standards-and-guidelines/traffic-engineering-and-safety/highway-safety/cmfs_for_bc_2008.pdf"
CMFS = {
    ("signalized", "single-lane"): 0.71,
    ("signalized", "multi-lane"): 0.83,
    ("stop-controlled", "one-lane"): 0.76,
    ("stop-controlled", "two-lane"): 0.89,
}


def assess_roundabout(predicted_crashes, control_type, roundabout_type):
    """Estimate all-collision effects, not physical/economic feasibility.

    Only urban conversions in Exhibits 6.2–6.3 are supported. A generic
    stop-controlled scenario is not evidence of suitability for a particular
    two-way/all-way-stop layout; all-way-stop is deliberately unsupported.
    """
    if isinstance(predicted_crashes, bool) or not isinstance(predicted_crashes, Real):
        raise ValueError("predicted_crashes must be a numeric count")
    if not math.isfinite(predicted_crashes) or predicted_crashes < 0:
        raise ValueError("predicted_crashes must be finite and non-negative")
    if not isinstance(control_type, str) or not isinstance(roundabout_type, str):
        raise ValueError("Control and roundabout types must be strings")
    pair = (control_type, roundabout_type)
    if pair not in CMFS:
        raise ValueError(f"Unsupported urban conversion: {pair}")
    cmf = CMFS[pair]
    expected_after = float(predicted_crashes) * cmf
    return {"predicted_crashes": float(predicted_crashes), "expected_after": expected_after,
            "collisions_prevented": float(predicted_crashes) - expected_after,
            "reduction_percent": (1 - cmf) * 100, "cmf": cmf,
            "cmf_source": CMF_SOURCE, "cmf_exhibit": "6.2 (p. 99)" if control_type == "signalized" else "6.3 (p. 100)"}
