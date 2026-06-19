"""
verify_models.py — Smoke-test that every model artifact loads under the
pinned dependency stack (scikit-learn 1.3.2, tensorflow 2.15.1, xgboost 2.0.3).

Run from the repo root (where the model files live):
    python scripts/verify_models.py

Exits 0 if every artifact loads and both prediction helpers return without
error; exits 1 on the first failure.

NOTE: This script is NOT run during the write-pins phase (plan 002) because
the host has no Python 3.11 / TF 2.15 environment. It is deferred to the
render build (plan 010) which has the correct stack.
"""
import sys
import os

# Ensure repo root is on the path so Dragon.py, logreg.py, ite.py are importable.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)


def ok(name):
    print(f"OK: {name}")


def fail(name, exc):
    print(f"FAIL: {name}: {exc}")
    sys.exit(1)


# ---------------------------------------------------------------------------
# 1. joblib artifacts used by logreg.py
# ---------------------------------------------------------------------------
try:
    import joblib
    loaded_model = joblib.load(os.path.join(REPO_ROOT, "LogReg.pkl"))
    ok("LogReg.pkl")
except Exception as e:
    fail("LogReg.pkl", e)

try:
    std = joblib.load(os.path.join(REPO_ROOT, "std101.pkl"))
    ok("std101.pkl")
except Exception as e:
    fail("std101.pkl", e)

try:
    ebm = joblib.load(os.path.join(REPO_ROOT, "ebm_all.pkl"))
    ok("ebm_all.pkl")
except Exception as e:
    fail("ebm_all.pkl", e)

# ---------------------------------------------------------------------------
# 2. XGBoost model used by logreg.py
# ---------------------------------------------------------------------------
try:
    from xgboost import XGBClassifier
    xgb = XGBClassifier()
    xgb.load_model(os.path.join(REPO_ROOT, "xgb_allstroke.json"))
    ok("xgb_allstroke.json")
except Exception as e:
    fail("xgb_allstroke.json", e)

# ---------------------------------------------------------------------------
# 3. ITE scaler used by ite.py
# ---------------------------------------------------------------------------
try:
    ite_scaler = joblib.load(os.path.join(REPO_ROOT, "ite_scaler.joblib"))
    ok("ite_scaler.joblib")
except Exception as e:
    fail("ite_scaler.joblib", e)

# ---------------------------------------------------------------------------
# 4. DragonNet .h5 models used by ite.py — mirrors ite.py:11-25 exactly
# ---------------------------------------------------------------------------
try:
    from tensorflow.keras.models import load_model
    from Dragon import EpsilonLayer, Base_Loss, TarReg_Loss

    _custom_objects = {
        "EpsilonLayer": EpsilonLayer,
        "TarReg_Loss": TarReg_Loss,
        "regression_loss": Base_Loss.regression_loss,
        "treatment_acc": Base_Loss.treatment_acc,
    }

    modelU = load_model(
        os.path.join(REPO_ROOT, "dragonnet_pl_975.h5"),
        custom_objects=_custom_objects,
    )
    ok("dragonnet_pl_975.h5")
except Exception as e:
    fail("dragonnet_pl_975.h5", e)

try:
    modelL = load_model(
        os.path.join(REPO_ROOT, "dragonnet_pl_025.h5"),
        custom_objects=_custom_objects,
    )
    ok("dragonnet_pl_025.h5")
except Exception as e:
    fail("dragonnet_pl_025.h5", e)

try:
    modelM = load_model(
        os.path.join(REPO_ROOT, "dragonnet_pl_mn.h5"),
        custom_objects=_custom_objects,
    )
    ok("dragonnet_pl_mn.h5")
except Exception as e:
    fail("dragonnet_pl_mn.h5", e)

# ---------------------------------------------------------------------------
# 5. Dummy prediction through logreg_function (mirrors logreg.py call site)
#    Fields: age, AF, DLP, HT, DM, isMale, SBP, BMIcalc, Statin,
#            antiCoag, antiDLP, antiDM, antiHT, antiPL, Cr, HDL, LDL, PG, TG
# ---------------------------------------------------------------------------
try:
    from logreg import logreg_function

    logreg_input = {
        "age": 65,
        "AF": 0,
        "DLP": 1,
        "HT": 1,
        "DM": 0,
        "isMale": 1,
        "SBP": 130,
        "BMIcalc": 25.0,
        "Statin": 0,
        "antiCoag": 0,
        "antiDLP": 0,
        "antiDM": 0,
        "antiHT": 0,
        "antiPL": 0,
        "Cr": 0.9,
        "HDL": 55.0,
        "LDL": 110.0,
        "PG": 95.0,
        "TG": 150.0,
    }
    result_logreg = logreg_function(logreg_input)
    ok(f"logreg_function (result={result_logreg})")
except Exception as e:
    fail("logreg_function", e)

# ---------------------------------------------------------------------------
# 6. Dummy prediction through ite_function (mirrors ite.py call site)
#    Columns: DLP, HT, AF, age, DM, BMIcalc, GFR, antiPL
# ---------------------------------------------------------------------------
try:
    from ite import ite_function

    ite_input = {
        "DLP": 1,
        "HT": 1,
        "AF": 0,
        "age": 65,
        "DM": 0,
        "BMIcalc": 25.0,
        "GFR": 80.0,
        "antiPL": 0,
    }
    result_ite = ite_function(ite_input)
    ok(f"ite_function (result={result_ite})")
except Exception as e:
    fail("ite_function", e)

# ---------------------------------------------------------------------------
print("All checks passed.")
sys.exit(0)
