---

## Executive Business Intelligence Module (`bi_powerbi_tableau/`)

This repository includes an executive Business Intelligence layer designed for **Asset-Liability Management Committee (ALCO)** reporting in **Power BI** and **Tableau Desktop**:

* **`bi_powerbi_tableau/datasets_estrella/Fact_ALM_Liquidez_Buckets.csv`**: Star-schema analytical table across repricing maturity buckets (`Overnight` to `>5Y`), duration gaps, $\Delta\text{NII}$, $\Delta\text{EVE}$ ($\pm 200\text{ bps}$), 99% VaR / Expected Shortfall, and Basel III Liquidity Coverage Ratio ($\text{LCR}$).
* **`bi_powerbi_tableau/powerbi/Medidas_DAX_ALM_IRRBB_VaR_LCR.dax`**: Production DAX measures for Net Repricing Gap, $\Delta\text{NII}$ / $\Delta\text{EVE}$ sensitivity, Expected Shortfall, and automated Basel III LCR compliance flags.
* **`bi_powerbi_tableau/powerbi/Tema_Ejecutivo_ALM_Riesgo.json`**: Institutional color palette and typography specification for Power BI Desktop.
* **`bi_powerbi_tableau/tableau/Tablero_ALM_Liquidez_IRRBB.twb`**: Native XML Tableau workbook pre-configured with repricing ladder, IRRBB sensitivity, and liquidity stress worksheets.
