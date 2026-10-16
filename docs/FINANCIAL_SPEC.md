# Batchwise — Financial Calculation Specification & Correctness Model

**Core Promise:** *“Every batch. Every cost. Every rupee.”*

This document defines the mathematical, financial, and unit-conversion models used across Batchwise. All calculations must adhere to these definitions and be implemented using Python's `decimal.Decimal` module. Binary floating-point arithmetic (`float`) is strictly prohibited for monetary calculations.

---

## 1. Analysis of Common Financial Contradictions & Pitfalls

### 1.1 The Wastage Double-Counting Pitfall
In home and artisanal food manufacturing, wastage occurs in two primary forms:
1. **Physical Yield Scrap (Output Reduction):** Burnt cookies, trimmings, spillage, taste-testing samples, broken packaging.
2. **Direct Monetary Loss (Direct Expense):** Spoiled raw ingredients thrown away prior to cooking, or special scrap disposal fees.

#### The Contradiction:
If a home baker incurs ₹1,000 in total batch costs (ingredients + fuel + packaging) and planned to get 100 cookies, but loses 10 cookies to burning (10% scrap):
- If the calculator sets $Q_{\text{sellable}} = 90$, the unit cost naturally increases:
  $$\text{Unit Cost} = \frac{₹1,000}{90} = ₹11.11 \text{ per cookie}$$
- If the system **also** adds a 10% "wastage cost" to the total expenditure ($₹1,000 + ₹100 = ₹1,100$) and divides by 90 sellable cookies:
  $$\text{Unit Cost (Double Counted)} = \frac{₹1,100}{90} = ₹12.22 \text{ per cookie}$$
  This is a mathematical contradiction: the baker has paid ₹1,000 in total out-of-pocket cash, yet the cost model reports ₹1,100 was spent. The burnt cookies were **already paid for** in the ingredients cost.

#### The Canonical Batchwise Solution:
- **Physical scrap/wastage reduces the sellable output quantity ($Q_{\text{sellable}}$)**. The total monetary expenditure ($C_{\text{batch}}$) remains the actual cash incurred.
- By dividing the actual batch cost by the reduced sellable quantity, the cost of wasted product is **naturally and accurately absorbed** across the remaining sellable units.
- An optional `direct_wastage_expense` (monetary ₹) is permitted *only* for unbudgeted out-of-pocket expenses (e.g., ruined extra batch ingredients or equipment repair).
- **Rule:** Never inflate the numerator ($C_{\text{batch}}$) with a percentage of costs if that percentage is already accounted for by shrinking the denominator ($Q_{\text{sellable}}$).

---

### 1.2 Profit Margin vs. Markup
Home food entrepreneurs routinely confuse **profit margin** with **markup**, leading to severe accidental underpricing.

| Metric | Definition | Mathematical Formula | Example ($Cost = ₹20, Target = 20\%$) |
| :--- | :--- | :--- | :--- |
| **Markup ($K$)** | Profit expressed as a percentage of **Cost** | $K = \frac{\text{Profit}}{\text{Cost}} \times 100\%$ | Selling Price = $20 \times (1 + 0.20) = \mathbf{₹24.00}$<br>Realized Margin = $\frac{24 - 20}{24} = \mathbf{16.67\%}$ *(Underpriced!)* |
| **Profit Margin ($M$)** | Profit expressed as a percentage of **Revenue** | $M = \frac{\text{Profit}}{\text{Revenue}} \times 100\%$ | Selling Price = $\frac{20}{1 - 0.20} = \mathbf{₹25.00}$<br>Realized Margin = $\frac{25 - 20}{25} = \mathbf{20.00\%}$ *(Accurate)* |

#### The Canonical Batchwise Solution:
1. Target pricing is calculated using the **Target Margin Formula**:
   $$P_{\text{target}} = \frac{U_c}{1 - \left(\frac{M_{\text{target}}}{100}\right)}$$
2. For complete clarity, the UI and API explicitly return both:
   - `profit_margin_pct` ($\frac{\text{Profit}}{\text{Revenue}} \times 100$)
   - `markup_pct` ($\frac{\text{Profit}}{\text{Cost}} \times 100$)
3. Target margin is strictly validated: $0\% \le M_{\text{target}} < 100\%$. Values $\ge 100\%$ are mathematically impossible (requiring infinite or negative prices).

---

### 1.3 Batch Economics (Projections) vs. Realized Sales (Cash Flow)
Another major point of confusion is treating a batch as an all-or-nothing event. A baker might bake 75 packets, but only sell 50 today.

#### The Canonical Batchwise Solution:
Batchwise models two distinct, clearly separated financial views:
1. **Full-Batch Projection (Potential Economics):**
   - Assumes 100% of sellable units ($Q_{\text{sellable}}$) are sold at planned price ($P_{\text{sell}}$).
   - Evaluates whether the recipe and pricing structure are fundamentally viable.
2. **Realized Batch Performance (Actuals to Date):**
   - Evaluates actual cash collected against total batch outlay:
     $$\text{Realized Cashflow} = (\text{Units Sold} \times P_{\text{sell}}) - C_{\text{batch}}$$
   - Calculates the **Break-Even Sales Volume**:
     $$Q_{\text{be\_units}} = \left\lceil \frac{C_{\text{batch}}}{P_{\text{sell}}} \right\rceil$$
     (The exact number of packets the seller must sell before they stop losing money on this batch).
   - Tracks remaining inventory ($Q_{\text{unsold}} = Q_{\text{sellable}} - Q_{\text{sold}}$) valued at cost price ($Q_{\text{unsold}} \times U_c$).

---

## 2. Mathematical Specification & Formulas

### 2.1 Ingredient Costing
Each ingredient $i$ has a purchase price $P_{\text{purchase}, i}$ for a purchase quantity $Q_{\text{purchase}, i}$, and a recipe usage quantity $Q_{\text{used}, i}$.

$$\text{Canonical Ratio}_i = \frac{\text{Convert}(Q_{\text{used}, i}, \text{Canonical Unit})}{\text{Convert}(Q_{\text{purchase}, i}, \text{Canonical Unit})}$$

$$C_{\text{ingredient}, i} = P_{\text{purchase}, i} \times \text{Canonical Ratio}_i$$

$$\text{Total Ingredients Cost } (C_{\text{ing}}) = \sum_{i=1}^{n} C_{\text{ingredient}, i}$$

### 2.2 Direct Expenses & Overheads
$$\text{Total Overheads } (C_{\text{ovh}}) = C_{\text{packaging}} + C_{\text{labour}} + C_{\text{fuel}} + C_{\text{delivery}} + C_{\text{other}} + C_{\text{direct\_waste}}$$

### 2.3 Total Production Cost
$$\text{Total Batch Cost } (C_{\text{batch}}) = C_{\text{ing}} + C_{\text{ovh}}$$

### 2.4 Sellable Output & Scrap Allocation
Given gross produced units $Q_{\text{gross}}$:
- If scrap units $Q_{\text{scrap}}$ are specified:
  $$Q_{\text{sellable}} = Q_{\text{gross}} - Q_{\text{scrap}}$$
- If scrap percentage $S_{\text{pct}}$ is specified:
  $$Q_{\text{scrap}} = Q_{\text{gross}} \times \left(\frac{S_{\text{pct}}}{100}\right)$$
  $$Q_{\text{sellable}} = Q_{\text{gross}} - Q_{\text{scrap}}$$
- Direct entry of $Q_{\text{sellable}}$ is also supported where sellers report packaged output directly.

**Constraint:** $Q_{\text{sellable}} \ge 0$. If $Q_{\text{sellable}} = 0$, the batch has zero viable commercial yield.

### 2.5 Unit Cost & Break-Even Price
$$\text{Cost per Sellable Unit } (U_c) = \frac{C_{\text{batch}}}{Q_{\text{sellable}}} \quad (\text{for } Q_{\text{sellable}} > 0)$$

$$\text{Break-Even Price per Unit } (P_{\text{be}}) = U_c$$

### 2.6 Revenue, Profit & Returns (at Planned Selling Price $P_{\text{sell}}$)
$$\text{Projected Revenue } (R_{\text{proj}}) = P_{\text{sell}} \times Q_{\text{sellable}}$$

$$\text{Projected Profit } (\Pi_{\text{proj}}) = R_{\text{proj}} - C_{\text{batch}}$$

$$\text{Profit per Unit } (\pi) = P_{\text{sell}} - U_c$$

$$\text{Profit Margin \% } (M) = \begin{cases} 
\left(\frac{\Pi_{\text{proj}}}{R_{\text{proj}}}\right) \times 100\% & \text{if } R_{\text{proj}} > 0 \\
\text{Undefined / None} & \text{if } R_{\text{proj}} \le 0 
\end{cases}$$

$$\text{Markup \% } (K) = \begin{cases} 
\left(\frac{P_{\text{sell}} - U_c}{U_c}\right) \times 100\% & \text{if } U_c > 0 \\
\text{Undefined / None} & \text{if } U_c \le 0 
\end{cases}$$

---

## 3. Dimension-Safe Unit Conversion Model

To prevent catastrophic costing mistakes, conversions are restricted strictly within identical physical dimensions.

### 3.1 Supported Physical Dimensions

| Dimension | Canonical Base Unit | Supported Units & Conversion Factors to Base |
| :--- | :--- | :--- |
| **MASS** | Gram (`g`) | `kg` = 1,000 g<br>`g` = 1 g |
| **VOLUME** | Milliliter (`ml`) | `l` (liter) = 1,000 ml<br>`ml` = 1 ml |
| **COUNT** | Piece / Unit (`unit`) | `unit` / `piece` = 1 unit<br>`dozen` = 12 units<br>`packet` / `pack` = 1 unit (default count unless packed batch count specified) |

### 3.2 Dimension Safety Rules
- Conversion between units of the same dimension is exact and automatic (e.g. 5 kg besan $\rightarrow$ 5,000 g; 250 g usage = $\frac{250}{5000} \times \text{Price}$).
- Conversion across different dimensions (e.g., `kg` to `ml`, `l` to `g`, `unit` to `kg`) is **strictly rejected** by raising `IncompatibleUnitDimensionError`.
- Batchwise **never** guesses liquid densities (e.g., assuming 1 liter of cooking oil equals 1 kilogram or 910 grams). If units do not share a physical dimension, the user must enter consistent units or specify the exact conversion.

---

## 4. Precision, Arithmetic & Rounding Policy

1. **Internal Precision:**
   - All arithmetic uses `decimal.Decimal`.
   - Intermediate unit costs and ratios maintain at least 6 decimal places of precision (`Decimal('0.000001')`).
2. **Display & Financial Settlement Rounding:**
   - Currency amounts (Rupees ₹ and paise) are rounded to 2 decimal places using `ROUND_HALF_UP` (`Decimal('0.01')`).
   - Percentages are rounded to 2 decimal places using `ROUND_HALF_UP`.
   - Break-even units to sell are rounded up using `ROUND_CEILING` to ensure full cost recovery.

---

## 5. Audit Trace Specification

Every calculation output contains a structured, human-readable audit trace explaining every calculation step:
- `step_name`: Identifies the formula applied (e.g. `INGREDIENT_COST`, `TOTAL_BATCH_COST`, `UNIT_COST`, `BREAK_EVEN_PRICE`, `TARGET_MARGIN_PRICE`).
- `formula`: Symbolic representation (e.g. `C_batch / Q_sellable`).
- `inputs`: Key-value map of exact `Decimal` inputs used.
- `output`: Resulting `Decimal` value before and after rounding.
- `explanation`: Plain-language explanation (e.g., *"Divided total batch cost of ₹860.00 by 75 sellable packets to get ₹11.47 per packet"*).

