"""Single parameter set for the DSS.

X and N are locked in SPEC section 1. The other numbers are team conventions
for the simple Phase 5 policies. The Streamlit page can override them.
"""

RANDOM_STATE = 42

# Locked 15/10/2026. X is a percent of GMV, N is a seller count.
X = 10.0
N = 40
MIN_ORDERS = 5

# P2 tiers. A seller at or above theta_3 is tier 3.
THETA_1 = 0.20
THETA_2 = 0.35
THETA_3 = 0.50
TIER_GAP_2 = 0.15
TIER_GAP_3 = 0.30
THETA_HI = 0.70

# Assumed intervention effect by tier. Not measured.
E1 = 0.25
E2 = 0.50
E3 = 0.75
E_P1 = 0.50

# P1 fixed KPI thresholds. Not measured.
LATE_SHIP_THRESHOLD = 0.15
AVG_REVIEW_THRESHOLD = 3.5

R = 0.5
S = 1.0
BISECTION_TOL = 1e-4
