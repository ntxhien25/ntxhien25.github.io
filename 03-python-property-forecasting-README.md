# Real Estate Cash Flow & Property Valuation Time-Series Forecasting

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.3%2B-orange.svg?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-150458.svg?logo=pandas&logoColor=white)](https://pandas.pydata.org/)

## 1. Project Background & Business Problem

Institutional real estate asset managers and investment funds (e.g., Frasers Property, CapitaLand, Mapletree) require highly granular, statistically disciplined cash flow forecasting to value commercial portfolios and support debt refinancing decisions. 

Traditional spreadsheet DCF underwriting suffers from:
- Subjective growth heuristics (e.g., assuming flat +3% rent growth regardless of macro market cycles).
- Inability to model seasonal occupancy fluctuations and multi-lag autoregressive dependencies.
- Static sensitivity analysis that fails to account for combined cap rate expansion and income compression during interest rate hikes.

### Key Objectives
1. **Automate Time-Series Ingestion:** Build a reproducible Python pipeline ingesting monthly commercial real estate rental revenues, tenant occupancy rates, and operational expenditures.
2. **Feature Engineering:** Formulate cyclical trigonometric calendar features (`sin`/`cos`), multi-month autoregressive lags (`t-1`, `t-2`, `t-3`, `t-12`), and rolling momentum metrics (`RollingMean3`, `RollingStd3`).
3. **Walk-Forward Validation:** Prevent lookahead data leakage using `TimeSeriesSplit` cross-validation across Ridge Regression, Random Forest, and Gradient Boosting Regressors.
4. **Institutional Asset Valuation:** Translate predicted forward 12-month Net Operating Income (NOI) into capitalization rate valuations and stress-tested scenarios (Base, Bull, Bear).

---

## 2. Repository Architecture & Files

```
03-python-property-forecasting/
├── property_forecasting_pipeline.py    # Complete modular production forecasting pipeline
├── requirements.txt                    # Project dependency specification
├── projected_cashflows_12m.csv         # Generated 12-month forward forecast with 90% confidence bounds
├── model_benchmarks.csv                # 5-fold walk-forward cross-validation performance metrics
└── README.md                           # Executive documentation (this file)
```

---

## 3. Machine Learning Benchmark Results

Evaluated across 5-fold temporal walk-forward splits:

| Model Architecture | MAE ($) | RMSE ($) | MAPE (%) | Accuracy (%) | R² Score |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Gradient Boosting Regressor** | **$3,914.55** | **$5,048.04** | **3.95%** | **96.05%** | **0.4466** |
| Random Forest Regressor | $4,171.97 | $5,262.83 | 4.19% | 95.81% | 0.4251 |
| Ridge Regression (L2 Baseline) | $4,194.49 | $5,041.15 | 4.46% | 95.54% | 0.1836 |

---

## 4. Institutional Valuation Output

With a Forward 12-Month Projected Net Operating Income of **$1,331,396 USD**:

- **Base Case (5.50% Cap Rate):** **$24,207,200 USD** ($161.38 / sq.ft.)
- **Stress-Tested Bear Case (-10% NOI, +75bps Cap Rate at 6.25%):** **$19,172,102 USD** ($127.81 / sq.ft.)
- **Optimistic Bull Case (+5% NOI, -50bps Cap Rate at 5.00%):** **$27,959,316 USD** ($186.40 / sq.ft.)

---

## 5. How to Run Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Execute pipeline
python property_forecasting_pipeline.py
```
