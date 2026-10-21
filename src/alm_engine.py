"""
Asset-Liability Management (ALM), Market Risk (VaR/ES) & Liquidity Stress Engine.
Aligned with Basel III (IRRBB, LCR) and CNBV regulatory standards for Mexican Banking.
Author: Wembley Emmanuel Ibarra Tepato
"""
import numpy as np
import pandas as pd
from scipy import stats
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class BalanceSheetBucket:
    bucket_name: str
    midpoint_years: float
    rate_sensitive_assets_mxn: float
    rate_sensitive_liabilities_mxn: float
    effective_duration_assets: float
    effective_duration_liabilities: float


class ALMMarketLiquidityEngine:
    """
    Quantitative engine for Balance Sheet Risk (IRRBB), Market Risk (VaR / Expected Shortfall
    with Kupiec POF Backtesting), and Liquidity Risk (LCR & Survival Horizon).
    """

    def __init__(self, random_seed: int = 42):
        self.rng = np.random.default_rng(random_seed)

    def evaluate_irrbb(
        self,
        buckets: List[BalanceSheetBucket],
        parallel_shock_bps: float = 200.0,
        base_discount_rate: float = 0.1050,
    ) -> Dict[str, object]:
        """
        Computes Interest Rate Risk in the Banking Book (IRRBB):
        - Repricing Gap per time bucket
        - Net Interest Income sensitivity (Delta NII) over a 1-year horizon
        - Economic Value of Equity sensitivity (Delta EVE) via duration approximation
        """
        shock_decimal = parallel_shock_bps / 10000.0
        rows = []
        total_delta_nii = 0.0
        total_delta_eve = 0.0
        total_rsa = 0.0
        total_rsl = 0.0

        for b in buckets:
            gap = b.rate_sensitive_assets_mxn - b.rate_sensitive_liabilities_mxn
            # Delta NII impacts cashflows repricing within 1 year
            time_weight_1y = max(0.0, 1.0 - b.midpoint_years)
            delta_nii = gap * shock_decimal * time_weight_1y

            # Modified duration approximation for Delta EVE
            mod_dur_a = b.effective_duration_assets / (1.0 + base_discount_rate)
            mod_dur_l = b.effective_duration_liabilities / (1.0 + base_discount_rate)
            delta_pv_a = -b.rate_sensitive_assets_mxn * mod_dur_a * shock_decimal
            delta_pv_l = -b.rate_sensitive_liabilities_mxn * mod_dur_l * shock_decimal
            delta_eve = delta_pv_a - delta_pv_l

            total_delta_nii += delta_nii
            total_delta_eve += delta_eve
            total_rsa += b.rate_sensitive_assets_mxn
            total_rsl += b.rate_sensitive_liabilities_mxn

            rows.append({
                "bucket": b.bucket_name,
                "midpoint_years": b.midpoint_years,
                "rsa_mxn": round(b.rate_sensitive_assets_mxn, 2),
                "rsl_mxn": round(b.rate_sensitive_liabilities_mxn, 2),
                "repricing_gap_mxn": round(gap, 2),
                "delta_nii_mxn": round(delta_nii, 2),
                "delta_eve_mxn": round(delta_eve, 2),
            })

        equity_base = max(total_rsa - total_rsl, 1.0)
        eve_pct_equity = (total_delta_eve / equity_base) * 100.0
        basel_outlier_flag = abs(eve_pct_equity) > 15.0  # Basel III 15% Tier 1 threshold

        return {
            "parallel_shock_bps": parallel_shock_bps,
            "total_rsa_mxn": round(total_rsa, 2),
            "total_rsl_mxn": round(total_rsl, 2),
            "net_repricing_gap_mxn": round(total_rsa - total_rsl, 2),
            "total_delta_nii_mxn": round(total_delta_nii, 2),
            "total_delta_eve_mxn": round(total_delta_eve, 2),
            "delta_eve_pct_of_equity": round(eve_pct_equity, 2),
            "basel_iii_outlier_alert": bool(basel_outlier_flag),
            "bucket_breakdown": rows,
        }

    def compute_var_and_es(
        self,
        returns: np.ndarray,
        portfolio_value_mxn: float,
        confidence_level: float = 0.99,
        mc_simulations: int = 20000,
    ) -> Dict[str, float]:
        """
        Computes 1-day Market Risk Value at Risk (VaR) and Expected Shortfall (CVaR)
        using Parametric (Variance-Covariance), Historical, and Monte Carlo methods.
        """
        alpha = 1.0 - confidence_level
        mu = float(np.mean(returns))
        sigma = float(np.std(returns, ddof=1))

        # 1. Parametric Normal VaR & ES
        z_alpha = stats.norm.ppf(alpha)
        var_parametric_pct = -(mu + z_alpha * sigma)
        es_parametric_pct = -mu + sigma * (stats.norm.pdf(z_alpha) / alpha)

        # 2. Historical Simulation VaR & ES
        q_hist = float(np.quantile(returns, alpha))
        var_historical_pct = -q_hist
        tail_losses = returns[returns <= q_hist]
        es_historical_pct = -float(np.mean(tail_losses)) if len(tail_losses) > 0 else var_historical_pct

        # 3. Monte Carlo Simulation
        sim_returns = self.rng.normal(loc=mu, scale=sigma, size=mc_simulations)
        q_mc = float(np.quantile(sim_returns, alpha))
        var_mc_pct = -q_mc
        es_mc_pct = -float(np.mean(sim_returns[sim_returns <= q_mc]))

        return {
            "confidence_level": confidence_level,
            "parametric_var_mxn": round(var_parametric_pct * portfolio_value_mxn, 2),
            "parametric_es_mxn": round(es_parametric_pct * portfolio_value_mxn, 2),
            "historical_var_mxn": round(var_historical_pct * portfolio_value_mxn, 2),
            "historical_es_mxn": round(es_historical_pct * portfolio_value_mxn, 2),
            "monte_carlo_var_mxn": round(var_mc_pct * portfolio_value_mxn, 2),
            "monte_carlo_es_mxn": round(es_mc_pct * portfolio_value_mxn, 2),
        }

    @staticmethod
    def kupiec_pof_backtest(
        realized_pnl: np.ndarray,
        var_threshold_mxn: np.ndarray,
        confidence_level: float = 0.99,
    ) -> Dict[str, object]:
        """
        Executes Kupiec's Proportion of Failures (POF) Likelihood Ratio test
        and classifies the model under the Basel Traffic Light framework (250-day basis).
        """
        n_obs = len(realized_pnl)
        exceptions = int(np.sum(realized_pnl < -np.abs(var_threshold_mxn)))
        p = 1.0 - confidence_level
        p_hat = exceptions / n_obs if n_obs > 0 else 0.0

        if exceptions == 0:
            lr_pof = -2.0 * n_obs * np.log(1.0 - p)
        elif exceptions == n_obs:
            lr_pof = -2.0 * n_obs * np.log(p)
        else:
            ll_null = (n_obs - exceptions) * np.log(1.0 - p) + exceptions * np.log(p)
            ll_alt = (n_obs - exceptions) * np.log(1.0 - p_hat) + exceptions * np.log(p_hat)
            lr_pof = float(-2.0 * (ll_null - ll_alt))

        p_value = float(1.0 - stats.chi2.cdf(lr_pof, df=1))

        # Basel Traffic Light scaling to 250 trading days
        scaled_exceptions = exceptions * (250.0 / max(n_obs, 1))
        if scaled_exceptions <= 4:
            basel_zone = "GREEN"
        elif scaled_exceptions <= 9:
            basel_zone = "YELLOW"
        else:
            basel_zone = "RED"

        return {
            "observations": n_obs,
            "exceptions": exceptions,
            "expected_exceptions": round(n_obs * p, 2),
            "lr_pof_statistic": round(lr_pof, 4),
            "p_value": round(p_value, 4),
            "reject_null_5pct": bool(p_value < 0.05),
            "basel_traffic_light_zone": basel_zone,
        }

    @staticmethod
    def evaluate_lcr_liquidity(
        hqla_level1_mxn: float,
        hqla_level2a_mxn: float,
        gross_stress_outflows_30d_mxn: float,
        contractual_inflows_30d_mxn: float,
    ) -> Dict[str, object]:
        """
        Computes Basel III Liquidity Coverage Ratio (LCR):
        - Applies 15% regulatory haircut to Level 2A assets and 40% cap
        - Caps inflows at 75% of total stressed cash outflows
        """
        adjusted_l2a = hqla_level2a_mxn * 0.85
        # Level 2 cap at 40% of total HQLA => L2 <= (2/3) * L1
        capped_l2a = min(adjusted_l2a, (2.0 / 3.0) * hqla_level1_mxn)
        total_hqla = hqla_level1_mxn + capped_l2a

        capped_inflows = min(contractual_inflows_30d_mxn, 0.75 * gross_stress_outflows_30d_mxn)
        net_outflows_30d = max(gross_stress_outflows_30d_mxn - capped_inflows, 1.0)
        lcr_pct = (total_hqla / net_outflows_30d) * 100.0
        daily_net_burn = net_outflows_30d / 30.0
        survival_days = total_hqla / daily_net_burn if daily_net_burn > 0 else 999.0

        return {
            "total_hqla_mxn": round(total_hqla, 2),
            "net_cash_outflows_30d_mxn": round(net_outflows_30d, 2),
            "lcr_percentage": round(lcr_pct, 2),
            "regulatory_compliant_100pct": bool(lcr_pct >= 100.0),
            "stressed_survival_horizon_days": round(survival_days, 1),
        }


if __name__ == "__main__":
    engine = ALMMarketLiquidityEngine(random_seed=42)
    sample_buckets = [
        BalanceSheetBucket("0-3M (TIIE 28d / Vista)", 0.125, 4500e6, 5200e6, 0.12, 0.10),
        BalanceSheetBucket("3-6M", 0.375, 3200e6, 2800e6, 0.35, 0.35),
        BalanceSheetBucket("6-12M", 0.750, 2900e6, 2100e6, 0.70, 0.68),
        BalanceSheetBucket("1-3Y (Cartera Comercial USD/MXN)", 2.000, 6800e6, 4900e6, 1.85, 1.70),
        BalanceSheetBucket("3-5Y (Fomento / Largo Plazo)", 4.000, 5100e6, 3800e6, 3.55, 3.20),
    ]
    irrbb_res = engine.evaluate_irrbb(sample_buckets, parallel_shock_bps=200.0)
    returns = engine.rng.normal(0.0003, 0.0115, 250)
    var_res = engine.compute_var_and_es(returns, portfolio_value_mxn=22500e6)
    pnl = returns * 22500e6
    backtest_res = engine.kupiec_pof_backtest(pnl, np.full(250, var_res["parametric_var_mxn"]))
    lcr_res = engine.evaluate_lcr_liquidity(3200e6, 950e6, 3600e6, 800e6)
    print(json.dumps({"IRRBB": irrbb_res, "Market_VaR_ES": var_res, "Kupiec": backtest_res, "LCR": lcr_res}, indent=2))
