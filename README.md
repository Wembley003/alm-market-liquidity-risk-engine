# ALM, Market & Liquidity Risk Engine (IRRBB · VaR/ES · LCR)

**Author:** Wembley Emmanuel Ibarra Tepato ([github.com/Wembley003](https://github.com/Wembley003))  
**Focus:** Balance Sheet Risk (ALM / IRRBB), Market Risk (VaR & Expected Shortfall), and Basel III / CNBV Liquidity Stress Testing.

## Overview
Quantitative engine in Python designed to model **Balance Sheet Risk (Riesgo de Balance / ALM)**, **Market Risk**, and **Liquidity Coverage (LCR)** for development and commercial banking institutions under **Basel III** and **CNBV (Disposiciones de Carácter General Aplicables a las Instituciones de Crédito - CUB)** guidelines.

### Key Capabilities
1. **Interest Rate Risk in the Banking Book (IRRBB / ALM)**:
   - Repricing Gap analysis across maturity buckets (`0-3M`, `3-6M`, `6-12M`, `1-3Y`, `3-5Y`).
   - Net Interest Income sensitivity ($\Delta 	ext{NII}$) over a 12-month horizon under parallel interest rate shocks ($\pm 200	ext{ bps}$ in TIIE / SOFR).
   - Economic Value of Equity sensitivity ($\Delta 	ext{EVE}$) using modified duration and Basel III 15% Tier-1 outlier alerting.
2. **Market & FX Risk (VaR vs. Expected Shortfall / CVaR)**:
   - Simultaneous estimation of 99% 1-day Value at Risk and Expected Shortfall across **Parametric (Variance-Covariance)**, **Historical Simulation**, and **Monte Carlo** methods.
3. **Regulatory Model Validation (Kupiec POF Backtesting)**:
   - Likelihood Ratio test ($LR_{	ext{POF}} \sim \chi^2_1$) for exception frequency validation and automatic classification into the **Basel Traffic Light Zones** (*Green, Yellow, Red*).
4. **Liquidity Risk (Basel III LCR & Survival Horizon)**:
   - High-Quality Liquid Assets (HQLA) calculation with Level 2A haircuts (15%) and concentration caps (40%), plus 75% inflow caps and stressed survival days.

## Reproducibility
```bash
pip install -r requirements.txt
python -m src.alm_engine
pytest -v
```
