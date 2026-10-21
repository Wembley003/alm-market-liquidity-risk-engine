import numpy as np
from src.alm_engine import ALMMarketLiquidityEngine, BalanceSheetBucket


def test_irrbb_sensitivity_direction():
    engine = ALMMarketLiquidityEngine(random_seed=42)
    buckets = [
        BalanceSheetBucket("0-3M", 0.125, 5000.0, 3000.0, 0.12, 0.12),
        BalanceSheetBucket("1-3Y", 2.000, 4000.0, 2500.0, 1.90, 1.40),
    ]
    res = engine.evaluate_irrbb(buckets, parallel_shock_bps=200.0)
    # Positive short-term gap => positive Delta NII under +200 bps rate hike
    assert res["total_delta_nii_mxn"] > 0
    # Longer asset duration than liability duration => negative Delta EVE under rate hike
    assert res["total_delta_eve_mxn"] < 0


def test_var_and_expected_shortfall_coherence():
    engine = ALMMarketLiquidityEngine(random_seed=123)
    returns = engine.rng.normal(0.0, 0.012, 500)
    res = engine.compute_var_and_es(returns, portfolio_value_mxn=1000000.0, confidence_level=0.99)
    # Expected Shortfall (CVaR) is coherent and strictly >= VaR at the same confidence level
    assert res["parametric_es_mxn"] >= res["parametric_var_mxn"]
    assert res["historical_es_mxn"] >= res["historical_var_mxn"]


def test_kupiec_backtest_basel_zones():
    engine = ALMMarketLiquidityEngine()
    pnl = np.full(250, 100.0)
    pnl[:2] = -500.0  # 2 exceptions in 250 days => GREEN zone
    res_green = engine.kupiec_pof_backtest(pnl, np.full(250, 300.0), confidence_level=0.99)
    assert res_green["exceptions"] == 2
    assert res_green["basel_traffic_light_zone"] == "GREEN"
    assert not res_green["reject_null_5pct"]


def test_lcr_regulatory_caps():
    engine = ALMMarketLiquidityEngine()
    res = engine.evaluate_lcr_liquidity(
        hqla_level1_mxn=1200.0,
        hqla_level2a_mxn=400.0,
        gross_stress_outflows_30d_mxn=1400.0,
        contractual_inflows_30d_mxn=300.0,
    )
    assert res["lcr_percentage"] > 100.0
    assert res["regulatory_compliant_100pct"] is True
