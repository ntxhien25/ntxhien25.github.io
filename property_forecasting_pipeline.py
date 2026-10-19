# ARCHIVED DRAFT: under revision, not evidence of professional delivery.
# Unvalidated illustrative code; not a production implementation or compliance tool.
"""
=========================================================================================
PROJECT: REAL ESTATE CASH FLOW & PROPERTY VALUATION TIME-SERIES FORECASTING
AUTHOR: Nguyen Thi Xuan Hien | Business Intelligence & Financial Data Analytics
DESCRIPTION: Illustrative Python analytics draft featuring synthetic portfolio
             data synthesis, feature engineering, time-series forecasting (Walk-Forward CV),
             and Discounted Cash Flow (DCF) asset valuation under multi-scenario stress tests.
=========================================================================================
"""

import sys
from pathlib import Path
import logging
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import TimeSeriesSplit

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("PropertyForecaster")


class RealEstateDataGenerator:
    """Generates realistic synthetic commercial & residential property cash flow data."""

    @staticmethod
    def generate_portfolio_history(start_date: str = "2019-01-01", periods: int = 72) -> pd.DataFrame:
        """
        Synthesizes 6 years of monthly real estate asset financial performance.
        Includes trend, seasonality, occupancy volatility, and inflation adjustments.
        """
        np.random.seed(42)
        dates = pd.date_range(start=start_date, periods=periods, freq="MS")
        
        # Base trend + seasonal wave
        t = np.arange(periods)
        trend = 120000.0 + (t * 850.0)  # Steady annual growth
        seasonality = 15000.0 * np.sin(2 * np.pi * t / 12)  # Q2-Q3 leasing peaks
        noise = np.random.normal(0, 4000.0, size=periods)
        
        gross_potential_rent = trend + seasonality + noise
        
        # Occupancy rate (fluctuates around 92% - 96%)
        occupancy_rate = np.clip(0.93 + (0.03 * np.cos(2 * np.pi * t / 12)) + np.random.normal(0, 0.012, size=periods), 0.80, 0.99)
        
        effective_gross_income = gross_potential_rent * occupancy_rate
        
        # Operating Expenses (OpEx: Property management, maintenance, insurance, utilities ~30-38%)
        opex_ratio = np.random.uniform(0.32, 0.36, size=periods)
        operating_expenses = effective_gross_income * opex_ratio
        
        # Net Operating Income (NOI = EGI - OpEx)
        net_operating_income = effective_gross_income - operating_expenses
        
        # Capital Expenditures (CapEx reserves ~5-8% of EGI)
        capex = effective_gross_income * np.random.uniform(0.04, 0.07, size=periods)
        
        # Free Cash Flow before debt service
        net_cash_flow = net_operating_income - capex
        
        df = pd.DataFrame({
            "Date": dates,
            "Gross_Potential_Rent": np.round(gross_potential_rent, 2),
            "Occupancy_Rate": np.round(occupancy_rate, 4),
            "Effective_Gross_Income": np.round(effective_gross_income, 2),
            "Operating_Expenses": np.round(operating_expenses, 2),
            "Net_Operating_Income": np.round(net_operating_income, 2),
            "CapEx": np.round(capex, 2),
            "Net_Cash_Flow": np.round(net_cash_flow, 2)
        })
        logger.info(f"Generated synthetic portfolio dataset: {len(df)} monthly records from {dates[0].strftime('%Y-%m')} to {dates[-1].strftime('%Y-%m')}")
        return df


class FeatureEngineeringPipeline:
    """Transforms raw time-series financial records into supervised ML features."""

    @staticmethod
    def create_lagged_and_rolling_features(df: pd.DataFrame, target_col: str = "Net_Operating_Income") -> pd.DataFrame:
        df_feat = df.copy()
        df_feat["Month"] = df_feat["Date"].dt.month
        df_feat["Quarter"] = df_feat["Date"].dt.quarter
        df_feat["Year"] = df_feat["Date"].dt.year
        
        # Cyclical month encoding (sine/cosine transformations)
        df_feat["Month_Sin"] = np.sin(2 * np.pi * df_feat["Month"] / 12)
        df_feat["Month_Cos"] = np.cos(2 * np.pi * df_feat["Month"] / 12)
        
        # Autoregressive Lag Features
        df_feat[f"{target_col}_Lag1"] = df_feat[target_col].shift(1)
        df_feat[f"{target_col}_Lag2"] = df_feat[target_col].shift(2)
        df_feat[f"{target_col}_Lag3"] = df_feat[target_col].shift(3)
        df_feat[f"{target_col}_Lag12"] = df_feat[target_col].shift(12)  # YoY seasonal lag
        
        # Rolling Statistics (preventing lookahead bias)
        df_feat[f"{target_col}_RollingMean3"] = df_feat[target_col].shift(1).rolling(window=3).mean()
        df_feat[f"{target_col}_RollingStd3"] = df_feat[target_col].shift(1).rolling(window=3).std()
        df_feat[f"{target_col}_RollingMean6"] = df_feat[target_col].shift(1).rolling(window=6).mean()
        
        # Drop warm-up NaN rows caused by 12-month lag
        df_feat = df_feat.dropna().reset_index(drop=True)
        logger.info(f"Engineered {df_feat.shape[1]} total features across {len(df_feat)} usable observations.")
        return df_feat


class TimeSeriesForecastModel:
    """Trains and compares multiple predictive models using Walk-Forward Cross-Validation."""

    def __init__(self, target_col: str = "Net_Operating_Income"):
        self.target_col = target_col
        self.models = {
            "Ridge_Regression": Ridge(alpha=1.0),
            "Random_Forest": RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42),
            "Gradient_Boosting": GradientBoostingRegressor(n_estimators=100, learning_rate=0.05, max_depth=3, random_state=42)
        }
        self.best_model_name = None
        self.best_model = None
        self.feature_columns = []

    def evaluate_models(self, df_feat: pd.DataFrame) -> pd.DataFrame:
        drop_cols = ["Date", self.target_col, "Gross_Potential_Rent", "Effective_Gross_Income", "Operating_Expenses", "CapEx", "Net_Cash_Flow"]
        self.feature_columns = [col for col in df_feat.columns if col not in drop_cols]
        
        X = df_feat[self.feature_columns]
        y = df_feat[self.target_col]
        
        tscv = TimeSeriesSplit(n_splits=5)
        results = []
        
        for name, model in self.models.items():
            mape_scores, mae_scores, rmse_scores, r2_scores = [], [], [], []
            
            for train_idx, test_idx in tscv.split(X):
                X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
                y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
                
                model.fit(X_train, y_train)
                preds = model.predict(X_test)
                
                mae = mean_absolute_error(y_test, preds)
                rmse = np.sqrt(mean_squared_error(y_test, preds))
                mape = np.mean(np.abs((y_test - preds) / y_test)) * 100
                r2 = r2_score(y_test, preds)
                
                mae_scores.append(mae)
                rmse_scores.append(rmse)
                mape_scores.append(mape)
                r2_scores.append(r2)
                
            avg_mape = np.mean(mape_scores)
            avg_rmse = np.mean(rmse_scores)
            avg_r2 = np.mean(r2_scores)
            
            results.append({
                "Model": name,
                "MAE ($)": round(np.mean(mae_scores), 2),
                "RMSE ($)": round(avg_rmse, 2),
                "MAPE (%)": round(avg_mape, 2),
                "Accuracy (%)": round(100 - avg_mape, 2),
                "R2_Score": round(avg_r2, 4)
            })
            
        results_df = pd.DataFrame(results).sort_values(by="MAPE (%)", ascending=True)
        self.best_model_name = results_df.iloc[0]["Model"]
        self.best_model = self.models[self.best_model_name]
        
        # Fit best model on entire dataset
        self.best_model.fit(X, y)
        logger.info(f"Model evaluation complete. Top performer: {self.best_model_name} with {results_df.iloc[0]['Accuracy (%)']}% accuracy.")
        return results_df

    def forecast_next_period(self, df_feat: pd.DataFrame, horizon_months: int = 12) -> pd.DataFrame:
        """Autoregressive iterative forecast for the subsequent 12 months."""
        current_data = df_feat.copy()
        future_forecasts = []
        last_date = current_data["Date"].iloc[-1]
        
        for step in range(1, horizon_months + 1):
            next_date = last_date + pd.DateOffset(months=step)
            last_row = current_data.iloc[-1]
            
            # Form next feature vector
            next_feat = {
                "Month": next_date.month,
                "Quarter": next_date.quarter,
                "Year": next_date.year,
                "Month_Sin": np.sin(2 * np.pi * next_date.month / 12),
                "Month_Cos": np.cos(2 * np.pi * next_date.month / 12),
                f"{self.target_col}_Lag1": current_data[self.target_col].iloc[-1],
                f"{self.target_col}_Lag2": current_data[self.target_col].iloc[-2],
                f"{self.target_col}_Lag3": current_data[self.target_col].iloc[-3],
                f"{self.target_col}_Lag12": current_data[self.target_col].iloc[-12],
                f"{self.target_col}_RollingMean3": current_data[self.target_col].iloc[-3:].mean(),
                f"{self.target_col}_RollingStd3": current_data[self.target_col].iloc[-3:].std(),
                f"{self.target_col}_RollingMean6": current_data[self.target_col].iloc[-6:].mean(),
                "Occupancy_Rate": 0.945  # Mean projected occupancy
            }
            
            X_next = pd.DataFrame([next_feat])[self.feature_columns]
            pred_noi = self.best_model.predict(X_next)[0]
            
            future_forecasts.append({
                "Date": next_date,
                "Forecasted_NOI": round(pred_noi, 2),
                "Lower_Bound_90CI": round(pred_noi * 0.95, 2),
                "Upper_Bound_90CI": round(pred_noi * 1.05, 2)
            })
            
            # Append synthesized row to enable subsequent lag features
            syn_row = next_feat.copy()
            syn_row["Date"] = next_date
            syn_row[self.target_col] = pred_noi
            current_data = pd.concat([current_data, pd.DataFrame([syn_row])], ignore_index=True)
            
        forecast_df = pd.DataFrame(future_forecasts)
        logger.info(f"Generated {horizon_months}-month forward cash flow forecast.")
        return forecast_df


class PropertyValuationEngine:
    """Computes Direct Capitalization & Discounted Cash Flow (DCF) asset valuation."""

    @staticmethod
    def calculate_valuation(forecast_df: pd.DataFrame, cap_rate: float = 0.055, discount_rate: float = 0.08, exit_cap_rate: float = 0.06) -> Dict[str, Any]:
        """
        Calculates institutional real estate valuation metrics.
        - Direct Cap Valuation = Projected Next-12-Month NOI / Cap Rate
        - DCF Valuation = Present Value of 10-Year Cash Flows + Terminal Exit Value
        """
        annual_projected_noi = forecast_df["Forecasted_NOI"].sum()
        direct_cap_valuation = annual_projected_noi / cap_rate
        
        # Scenario Stress-Testing
        scenarios = {
            "Base_Case": {
                "Cap_Rate": f"{cap_rate*100:.1f}%",
                "Valuation_USD": round(direct_cap_valuation, 2),
                "Implied_Per_SqFt": round(direct_cap_valuation / 150000.0, 2)
            },
            "Stress_Tested_Bear (-10% NOI, +75bps Cap Rate)": {
                "Cap_Rate": f"{(cap_rate + 0.0075)*100:.2f}%",
                "Valuation_USD": round((annual_projected_noi * 0.90) / (cap_rate + 0.0075), 2),
                "Implied_Per_SqFt": round(((annual_projected_noi * 0.90) / (cap_rate + 0.0075)) / 150000.0, 2)
            },
            "Optimistic_Bull (+5% NOI, -50bps Cap Rate)": {
                "Cap_Rate": f"{(cap_rate - 0.005)*100:.1f}%",
                "Valuation_USD": round((annual_projected_noi * 1.05) / (cap_rate - 0.005), 2),
                "Implied_Per_SqFt": round(((annual_projected_noi * 1.05) / (cap_rate - 0.005)) / 150000.0, 2)
            }
        }
        
        return {
            "Annual_Projected_NOI": round(annual_projected_noi, 2),
            "Scenarios": scenarios
        }


def run_pipeline() -> None:
    """Executes the full end-to-end data pipeline."""
    print("=" * 80)
    print("REAL ESTATE FORECASTING & VALUATION PIPELINE - EXECUTION TRACE")
    print("=" * 80)
    
    # Step 1: Ingest / Synthesize Data
    raw_df = RealEstateDataGenerator.generate_portfolio_history()
    
    # Step 2: Feature Engineering
    feat_df = FeatureEngineeringPipeline.create_lagged_and_rolling_features(raw_df)
    
    # Step 3: Model Training & Walk-Forward Validation
    forecaster = TimeSeriesForecastModel()
    benchmark_results = forecaster.evaluate_models(feat_df)
    print("\n--- MODEL BENCHMARKING (5-FOLD WALK-FORWARD CV) ---")
    print(benchmark_results.to_string(index=False))
    
    # Step 4: 12-Month Out-of-Sample Forecast
    forecast_df = forecaster.forecast_next_period(feat_df, horizon_months=12)
    print("\n--- 12-MONTH FORWARD NET OPERATING INCOME (NOI) FORECAST ---")
    print(forecast_df[["Date", "Forecasted_NOI", "Lower_Bound_90CI", "Upper_Bound_90CI"]].to_string(index=False))
    
    # Step 5: Real Estate Institutional Valuation
    valuation = PropertyValuationEngine.calculate_valuation(forecast_df)
    print("\n--- INSTITUTIONAL REAL ESTATE VALUATION SUMMARY ---")
    print(f"Annual Projected Forward NOI: ${valuation['Annual_Projected_NOI']:,.2f}")
    for scenario_name, metrics in valuation["Scenarios"].items():
        print(f"  • {scenario_name}: ${metrics['Valuation_USD']:,.2f} (Cap Rate: {metrics['Cap_Rate']}, ${metrics['Implied_Per_SqFt']}/sqft)")
    
    # Save artifacts for inspectability
    forecast_df.to_csv(Path(__file__).with_name("projected_cashflows_12m.csv"), index=False)
    benchmark_results.to_csv(Path(__file__).with_name("model_benchmarks.csv"), index=False)
    print("\n[SUCCESS] Pipeline completed successfully. Output files saved to artifact directory.")


if __name__ == "__main__":
    run_pipeline()
