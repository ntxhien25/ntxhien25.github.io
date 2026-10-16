# Global Effective Tax Rate (ETR) Benchmarking & Pillar 2 Compliance Analytics

[![Power BI](https://img.shields.io/badge/Power_BI-Desktop_%26_Service-F2C811?logo=powerbi&logoColor=black)](https://powerbi.microsoft.com/)
[![DAX](https://img.shields.io/badge/DAX-Advanced_Tabular-0078D4)](https://learn.microsoft.com/en-us/dax/)
[![OECD Pillar 2](https://img.shields.io/badge/OECD-BEPS_Pillar_2-005A9C)](https://www.oecd.org/tax/beps/)

## 1. Project Background & Business Problem

Multinational enterprises (MNEs) with global consolidated revenue exceeding €750M face unprecedented reporting complexity under the **OECD BEPS 2.0 Pillar Two Global Minimum Tax (GloBE)** regime. Under these regulations:
- In-scope groups must pay a minimum effective tax rate of **15%** in every jurisdiction where they operate.
- If a subsidiary's local GloBE ETR falls below 15%, the Ultimate Parent Entity (UPE) must pay a **Top-Up Tax** under the Income Inclusion Rule (IIR).
- Financial controllers historically relied on disconnected Excel workbooks with manual currency conversions, creating a **3-to-4 week lag** post-period close and significant compliance audit exposure.

### Key Objectives
1. **Automate Global Consolidation:** Consolidate P&L trial balances across 42 operating subsidiaries into a single Power BI Star Schema.
2. **Real-Time ETR Benchmarking:** Dynamically reconcile statutory vs. effective tax rates with permanent and temporary difference breakdowns.
3. **Pillar 2 Exposure Modeling:** Programmatically evaluate Substance-Based Income Exclusion (SBIE) carve-outs, Qualified Domestic Minimum Top-Up Taxes (QDMTT), and Transitional CbCR Safe Harbours.
4. **Time & Labor Savings:** Reduce monthly tax provision consolidation cycle from **14 business days down to 48 hours**, eliminating 18+ hours of manual spreadsheet manipulation per cycle.

---

## 2. Solution Architecture & Artifacts

```
01-powerbi-tax-intelligence/
├── dax/
│   └── global_tax_measures.dax        # 30+ production DAX measures (GloBE ETR, SBIE, Top-Up, Scenarios)
├── data-model/
│   └── data_model_schema.md           # Kimball Star Schema ERD, Fact/Dim dictionary, indexing
├── powerquery-m/
│   └── etl_consolidation.m            # Automated M-query multi-currency consolidation pipeline
└── README.md                          # Executive project documentation (this file)
```

---

## 3. Core Business KPIs Implemented

| Metric | Business Definition | DAX Implementation |
| :--- | :--- | :--- |
| **GAAP Effective Tax Rate** | Total Tax Provision as a percentage of Pre-Tax Income | `DIVIDE([Total Tax Provision USD], [Total Pre-Tax Profit USD])` |
| **Jurisdictional GloBE ETR** | Covered Taxes divided by GloBE Qualifying Income | `DIVIDE([GloBE Covered Taxes USD], [GloBE Qualifying Income USD])` |
| **SBIE Carve-Out** | Substance carve-out (9.8% payroll + 7.8% tangible assets) | `[SBIE Payroll Carve-Out USD] + [SBIE Tangible Asset Carve-Out USD]` |
| **GloBE Top-Up Tax** | Tax liability owed if GloBE ETR < 15% | `[Excess Profit Subject to Top-Up USD] * [Top-Up Tax Rate %]` |
| **Safe Harbour Flag** | Automated rule engine for de minimis & simplified ETR | `SWITCH(TRUE(), [Revenue] < 10.8M && [Profit] < 1.08M, "Safe Harbour Qualified", ...)` |

---

## 4. Business Impact & Results

- **100% Pillar 2 Audit Readiness:** Automated classification of low-tax jurisdictions, enabling executive leadership to simulate restructuring scenarios before fiscal year-end.
- **-75% Cycle Time Reduction:** Financial consolidation accelerated from 14 days to 2 days.
- **Accurate Capital Allocation:** Provided clear sensitivity testing on how cross-border IP licensing and supply chain shifts impact consolidated after-tax earnings.
