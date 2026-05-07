# Reservoir Engineering MBE Tool — Complete Documentation

> **Simple words. No fluff. Everything you need to understand this project.**

---

## 1. What Is This Project?

This is a **web calculator** for Reservoir Engineering students. It solves the **General Material Balance Equation (MBE)** — a math formula that tells you how much oil is underground, or how much water is flowing in, or how big the gas cap is.

**Think of it like a calculator, but for oil reservoirs.**

You give it some numbers (like how much oil you pumped out, what the pressure is, etc.), and it tells you the one number you don't know.

### What Can It Calculate?
- **N** — How much oil was originally in the ground (Initial Oil-In-Place)
- **We** — How much water has flowed into the reservoir from an aquifer
- **m** — How big the gas cap is (as a ratio)
- **deltaP** — How much the pressure dropped
- **G** — How much gas was originally in the ground (Initial Gas-In-Place)

---

## 2. What Is the Material Balance Equation?

The MBE is a **conservation law**. It says:

> "The oil you originally had underground = the oil you produced + the oil still left + the water that pushed in + the gas that expanded."

Or in simpler terms:

> "What you started with = what you took out + what moved around to fill the empty space."

The full formula we use is:

```
N = (Np × [Bt + (Rp - Rsi) × Bg] - (We - Wp × Bw))
    ─────────────────────────────────────────────────
    (Bt - Bti) + m × Bti × [Bg/Bgi - 1] + Bti × (1+m) × [(Swi×cw + cf)/(1-Swi)] × deltaP
```

**Don't panic.** Here's what each part means in plain English:

### Top Part (Numerator)
This is **what came OUT of the reservoir** minus **what came IN**.

- `Np × Bt` — The oil you produced, converted to reservoir volume
- `Np × (Rp - Rsi) × Bg` — The extra gas that bubbled out of the oil because pressure dropped
- `We - Wp × Bw` — Net water: water that flowed IN from the aquifer, minus water you produced

### Bottom Part (Denominator)
This is **how much space was created underground** — the "drive energy" that pushes oil out.

- `(Bt - Bti)` — Oil shrinkage: oil takes up less space when pressure drops
- `m × Bti × (Bg/Bgi - 1)` — Gas cap expansion: the gas cap grows as pressure drops
- `Bti × (1+m) × [(Swi×cw + cf)/(1-Swi)] × deltaP` — Rock and water expansion: the rocks and water squeeze a tiny bit

### The Big Idea
The equation balances **production** (top) with **expansion** (bottom). 

If a lot of water flows in (`We` is big), that water pushes oil out. 
If there's a big gas cap (`m` is big), the gas expands and pushes oil out. 
If there's no gas cap and no water, the only thing pushing oil out is the oil itself shrinking and gas bubbling out of it.

### Gas Reservoir MBE

For gas reservoirs, the equation is much simpler:

```
G × (Bg - Bgi) = Gp × Bg - (We - Wp × Bw)
```

Gas expansion is the primary drive. A water-drive gas reservoir adds the
aquifer term. There is no oil shrinkage, no gas cap, and no rock/fluid
expansion term for gas.

Switching between Oil and Gas is done via the **Fluid Type** selector in the
sidebar. The interface, variable list, and equation all change automatically.

---

## 3. How to Run This Project

### Step 1: Install Python
You need Python 3.11 or newer.

### Step 2: Create a Virtual Environment
```bash
python3 -m venv venv
```

### Step 3: Activate It
**Mac/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

This installs:
- **Streamlit** — makes the web app
- **SymPy** — does the symbolic math
- **Pandas** — reads CSV/Excel files
- **Plotly** — draws the pie chart
- **NumPy** — handles numbers

### Step 5: Run the App
```bash
streamlit run app.py
```

Your browser will open to `http://localhost:8501`.

**Documentation:** The built-in user manual is at `http://localhost:8501/docs`
— it includes guided tutorials with one-click example buttons.

---

## 4. Project Structure

```
reservoir-engineering/
│
├── app.py                 ← The web app (Streamlit UI, main entry point)
├── config.py              ← Shared constants: variable definitions, SymPy symbols
├── mbe_solver.py          ← The math engine (SymPy solver, drive indices)
├── havlena_odeh.py        ← Havlena-Odeh linear-form calculation (F vs Et plotting)
├── test_cases.py          ← Tests to verify the math is correct
├── requirements.txt       ← List of Python packages needed
│
├── ui/
│   ├── __init__.py
│   ├── sidebar.py         ← Sidebar: target var, reservoir state, drive toggles
│   ├── data_input.py      ← Manual input fields and CSV/Excel file upload
│   ├── results.py         ← Results display: answer, drive chart, summary table, export
│   └── time_series.py     ← Time-series charts (Pressure vs Np, Havlena-Odeh F vs Et)
│
├── pages/
│   └── docs.py            ← Beginner-friendly documentation page (/docs)
│
├── test_data_v2.csv       ← Sample data you can upload
├── test_all_vars.csv      ← Another sample data file
│
├── .gitignore             ← Tells git what NOT to upload
└── DOCUMENTATION.md       ← This file (you are reading it!)
```

---

## 5. Deep Dive: `mbe_solver.py`

This is the **brain** of the project. It does all the math.

### Why SymPy?

Normally, you'd write a separate formula for each case:
- One formula to solve for N
- One formula to solve for We
- One formula to solve for m
- One formula to solve for deltaP

That's **4 separate formulas** to maintain and debug.

Instead, we use **SymPy** (a Python library for symbolic math). We define the equation **once**, and SymPy rearranges it automatically to solve for whichever variable we want.

### How It Works (Step by Step)

#### Step 1: Define Symbols
```python
N, Np, Bt, Bti, ... = sp.symbols('N Np Bt Bti ...')
```

This tells SymPy: "These letters are not just text — they are math variables."

#### Step 2: Build the Equation
```python
numerator = Np * (Bt + (Rp - Rsi) * Bg) - (We - Wp * Bw)
base_denominator = (Bt - Bti) + m * Bti * (Bg / Bgi - 1)
expansion_term = Bti * (1 + m) * ((Swi * cw + cf) / (1 - Swi)) * deltaP
denominator = base_denominator + expansion_term
```

We split the equation into pieces so it's easier to read and debug.

#### Step 3: Write the Implicit Form
```python
MBE_IMPLICIT = N * denominator - numerator
```

This says: `N × denominator = numerator`. 

We set it equal to **zero** because SymPy's solver likes equations in the form `something = 0`.

**Why implicit?** Because now SymPy can solve for ANY variable:
- If we want `N`, SymPy isolates N
- If we want `We`, SymPy isolates We
- If we want `m`, SymPy isolates m
- If we want `deltaP`, SymPy isolates deltaP

**One equation. Four possible answers.** No copy-paste errors.

For gas reservoirs, a separate implicit equation is used:

```python
GAS_MBE_IMPLICIT = G * (Bg - Bgi) - Gp * Bg + (We - Wp * Bw)
```

The `fluid_type` parameter (`'oil'` or `'gas'`) determines which equation and
variable set is used. Both share the same validation and solving pipeline.

#### Step 4: Substitute Known Values
```python
substitutions = {}
# Force zeros (e.g., if water drive is turned OFF)
for var in forced_zeros:
    substitutions[SYMBOLS[var]] = 0.0

# Add user's known values
for var, val in known_values.items():
    substitutions[SYMBOLS[var]] = float(val)

# Remove the target variable (the one we want to solve for)
substitutions.pop(target_symbol, None)
```

We build a dictionary that says: "Replace every known variable with its number."

**Validation:** The solver checks which variables are relevant for the current
fluid type (`OIL_VARS` or `GAS_VARS`) and only requires those. Variables
outside the active set are ignored.

**Iterative substitution:** To prevent division-by-zero errors, the solver
substitutes variables one at a time in order. Variables that "collapse" terms
(like `m = 0` zeroing out the gas cap term) are processed before variables
that could cause division by zero inside collapsed terms (like `Bgi = 0`
inside `Bg/Bgi`).

#### Step 5: Solve!
```python
# Try direct algebra first
solutions = sp.solve(expr_to_solve, target_symbol)

# If that fails, try numerical guessing
sp.nsolve(expr_to_solve, target_symbol, guess)
```

**Direct solving** works for simple cases (N, We, m). SymPy rearranges the equation like you would on paper.

**Numerical solving** works for hard cases (deltaP). SymPy tries different numbers until it finds one that makes the equation balance.

#### Step 6: Return Everything
```python
return {
    'success': True,
    'result': 36_593_625.50,  # The answer
    'error_message': None,
    'all_values': {           # Every variable and its value
        'N': 36_593_625.50,
        'Np': 5_000_000,
        'Bt': 1.48,
        ...
    }
}
```

We return the answer AND all the input values. This lets the UI show a nice summary table.

### The `compute_drive_indices()` Function

After solving, we want to show a pie chart of **which mechanism is doing most of the work**.

We calculate four "energy contributions":

1. **Oil shrinkage / Solution gas**: `N × (Bt - Bti)`
2. **Gas cap expansion**: `N × m × Bti × (Bg/Bgi - 1)`
3. **Rock & water expansion**: `N × Bti × (1+m) × [(Swi×cw+cf)/(1-Swi)] × deltaP`
4. **Net water influx**: `We - Wp × Bw`

**Why multiply by N?** Because the denominator terms are in `bbl/STB` (barrels per stock tank barrel), but water influx is in `bbl` (just barrels). We multiply by `N` (which is in STB) to get everything in the same units: **barrels**.

Then we convert to percentages for the pie chart.

---

## 6. Deep Dive: `app.py`

This is the **face** of the project. It's the web page you interact with.

### Built With Streamlit

Streamlit is a Python library that turns Python scripts into web apps. You write Python, and Streamlit creates the buttons, dropdowns, and charts automatically.

### The Sidebar (Left Side)

When you open the app, you see controls on the left:

#### 1. Target Variable Dropdown
"Fluid Type" — Choose between **Oil Reservoir** and **Gas Reservoir**.
This changes the equation, variable list, and drive options.

"What do you want to solve for?"
- Oil: N (Initial Oil-In-Place), We (Water Influx), m (Gas Cap Size), deltaP (Pressure Change)
- Gas: G (Initial Gas-In-Place), We (Water Influx)

**What it does:** Tells the solver which variable to calculate.

#### 2. Reservoir State Radio Buttons (Oil only)
- **Saturated** (p ≤ pb) — Gas is bubbling out of the oil normally
- **Unsaturated** (p > pb) — Pressure is above bubble point, no free gas

**What it does:** If you pick "Unsaturated," the app automatically:
- Sets `m = 0` (no gas cap)
- Sets `Rp = Rsi` (no evolved gas)

#### 3. Drive Mechanism Checkboxes
- **Water Drive Active?** — If OFF, sets `We = 0`, `Wp = 0`, and hides `Bw`
- **Gas Cap Active?** (Oil only) — If OFF, sets `m = 0` and hides `Bgi`
- **Rock & Water Expansion Active?** (Oil only) — If OFF, sets `cw = 0`, `cf = 0`, and hides `Swi` (also hides `deltaP` unless you're solving for it)

**What it does:** These are "shortcuts." Instead of typing 0 for many variables, you just uncheck a box. The app also hides input fields for variables that become irrelevant when a drive is off — for example, if water drive is off, `Bw` (Water FVF) doesn't matter and disappears from the screen. This keeps the interface clean and beginner-friendly.

### The Main Page (Center)

#### Input Method
You can choose:
- **Manual Entry** — Type numbers into boxes
- **File Upload** — Upload a CSV or Excel file

**Manual Entry:**
The app shows input boxes ONLY for variables you need to fill in. It hides:
- The variable you're solving for
- Variables that are forced to 0 by the sidebar toggles

**File Upload:**
The app reads the first row of your CSV/Excel file. It maps column names to variables (case-insensitive). It skips the target variable column (since that's what we're solving for).

#### The Calculate Button
When you click "Calculate":

1. The app gathers all inputs
2. It applies forced zeros
3. It starts a timer (`time.perf_counter()`)
4. It calls `solve_mbe()` from `mbe_solver.py`
5. It stops the timer
6. It shows the result

### The Results Section

After calculation, you see:

#### 1. The Big Answer
```
N = 36,593,625.50 STB  |  36.59 MMSTB
```

Formatted nicely with commas and units.

#### 2. Recovery Factor
```
Recovery Factor (Rf) = 13.66%
```

Tells you what percentage of the original oil you've produced so far.

#### 3. Execution Timer
```
⏱️ Calculation completed in 0.0183 seconds
```

Shows how fast the solver ran.

#### 4. Drive Mechanism Analysis
A text explanation of what's pushing the oil (or gas) out:
- For oil: "Solution Gas Drive", "Gas Cap Drive", "Water Drive", or "Combination Drive"
- For gas: "Volumetric Depletion" (no water) or "Water Drive"

#### 5. Expert Insights & Recommendations
Practical tips based on your results. For example:
- Warns you if Secondary Gas Saturation is developing (you're losing pressure energy)
- Alerts you if Rock & Fluid Expansion is the only energy source (least efficient drive)
- Suggests trend analysis to verify your drive mechanism assumptions
- (Oil only — not shown for gas reservoirs)

#### 6. Drive Indices Pie Chart
A Plotly donut chart showing the percentage contribution of each mechanism:
- Oil Shrinkage / Solution Gas
- Gas Cap Expansion
- Rock & Water Expansion
- Net Water Influx

#### 7. Summary Data Table
A table showing every variable, its value, and its status:
- **Target** — The variable we solved for
- **Input** — A value you provided
- **Forced Zero** — A value set to 0 by a sidebar toggle

#### 8. Export Button
```
[Download Summary as CSV]
```

Downloads the summary table as a CSV file called `mbe_results.csv`.

---

## 7. Deep Dive: `test_cases.py`

This file contains **automated tests** that verify the math is correct.

### Test 1: Base Saturated Case
Solves for N with water drive + gas cap active.

**Expected:** N ≈ 36,593,625 STB

This is the "reference problem" from the project guidelines.

### Test 2: Solution Gas Drive Only
Solves for N with NO water drive and NO gas cap.

**Expected:** N ≈ 85,769,231 STB

Because the denominator is smaller (only oil shrinkage), N must be bigger to match the same production.

### Test 3: Solve for Water Influx
Given N from Test 1, solves for We.

**Expected:** We ≈ 3,000,000 bbl

This verifies the solver works "backwards."

### Test 4: Solve for Gas Cap Size
Given N from Test 1, solves for m.

**Expected:** m ≈ 0.2

This verifies the solver can isolate m.

### Test 5: Unsaturated Reservoir
Solves for N with NO gas cap, NO water drive, but WITH rock/fluid expansion.

**Expected:** N ≈ 70,325,581 STB

This tests the expansion term specifically.

### How to Run Tests
```bash
pytest test_cases.py -v
```

You should see:
```
test_cases.py::test_case_1_base_saturated_solve_N PASSED
test_cases.py::test_case_2_solution_gas_drive_only PASSED
test_cases.py::test_case_3_solve_for_water_influx PASSED
test_cases.py::test_case_4_solve_for_gas_cap_size PASSED
test_cases.py::test_case_5_unsaturated_reservoir_logic PASSED
```

**All 5 tests must pass.** If any fail, the math engine has a bug.

---

## 8. The Math: Why This Formula?

### The Physical Story

Imagine an underground cave filled with oil, with some gas on top, and water surrounding it.

When you pump oil out:
1. The pressure drops
2. The oil shrinks a little (it takes up less space)
3. Gas bubbles out of the oil (like soda fizzing)
4. The gas cap above expands to fill the void
5. Water from surrounding rocks pushes in
6. The rocks themselves squeeze slightly

**The MBE counts all these volume changes and makes sure they add up.**

### Why the Denominator Has `(Bt - Bti)`?

`Bt` is how much space oil takes up NOW.
`Bti` is how much space oil took up INITIALLY.

If pressure drops, oil shrinks, so `Bt > Bti`.
The difference `(Bt - Bti)` is how much **extra space** was created.

That extra space must be filled by something: gas expanding, water pushing in, or rock squeezing.

### Why We Use `(Bt - Bti)` Instead of `(Bti - Bt)`?

The project guidelines specifically asked for `(Bt - Bti)`. 

Some textbooks or handwritten notes might flip the sign, but we follow the **official formula** as written in the requirements.

This means our answer for the test case is **~36.59 MMSTB** (not 31.14 MMSTB). The 31.14 number comes from a sign error in the handwritten sample.

---

## 9. Error Handling

The app handles several error cases gracefully:

### Missing Inputs
If you forget to provide a required variable, the app shows:
```
Calculation failed: Missing known values for variables: Swi
```

### Division by Zero
The solver uses **iterative substitution** to avoid division-by-zero errors. When variables that "collapse" terms (like `m = 0`) and variables that could cause division by zero (like `Bgi = 0` inside `Bg/Bgi`) are both forced to zero, the solver processes the collapsing variables first so the dangerous terms vanish before problematic divisions are evaluated.

If `Swi = 1` (which makes `1 - Swi = 0`), the app shows:
```
Calculation failed: Division by zero: Swi=1 with non-zero rock/fluid expansion term
```

### Target Variable Cancels Out
If you try to solve for a variable that doesn't affect the equation (e.g., deltaP when all expansion terms are 0), the app shows:
```
Calculation failed: Target variable deltaP cancels out; equation is inconsistent
```

### No Valid Solution
If SymPy can't find an answer, the app shows:
```
Calculation failed: No valid solution found
```

---

## 10. Tips for Using the App

### Tip 1: Use the Built-in Tutorials
Open `http://localhost:8501/docs` for the user manual. Each tutorial has a
**▶️ Load in Calculator** button that opens the main app with all inputs
pre-filled and runs the calculation automatically. No typing required.

### Tip 2: Check the Drive Chart
The pie chart tells you which mechanism is doing most of the work. If you expected "Water Drive" but see "Solution Gas Drive," your inputs might be wrong.

### Tip 3: Start with the Test Case
Upload `test_data_v2.csv` and make sure you get N = 36.59 MMSTB. If you don't, something is wrong with your setup.

### Tip 4: For Unsaturated Reservoirs
- Set reservoir state to "Unsaturated"
- Turn OFF "Gas Cap Active"
- Turn ON "Rock & Water Expansion Active"
- The app will automatically set `m = 0` and `Rp = Rsi`

### Tip 5: For Gas Reservoirs
- Switch fluid type to "Gas Reservoir" in the sidebar
- The interface changes completely — fewer variables, different targets
- Water drive is the only optional drive mechanism for gas

### Tip 6: Understanding Units
- **STB** = Stock Tank Barrels (oil at surface conditions)
- **Mscf** = Thousand Standard Cubic Feet (gas at surface)
- **bbl** = Barrels (volume at reservoir conditions)
- **scf/STB** = Standard Cubic Feet per Stock Tank Barrel (gas per oil)
- **psi** = Pounds per Square Inch (pressure)
- **decimal** = Fraction (e.g., 0.25 means 25%)
- **psi⁻¹** = Per psi (compressibility)

---

## 11. For Developers: How to Extend This

### Add a New Variable to Solve For
1. Add the symbol to the `SYMBOLS` dict in `config.py`
2. Add its UI metadata to `var_info` in `config.py`
3. Add it to the dropdown options in `ui/sidebar.py`

### Change the MBE Formula
Edit the `numerator`, `base_denominator`, and `expansion_term` equations in `mbe_solver.py`. The implicit form (`MBE_IMPLICIT`) will automatically adapt.

### Add a New Chart
After computing `drive_data`, create a new Plotly figure:
```python
fig = go.Figure(data=[go.Bar(x=drive_data['labels'], y=drive_data['values'])])
st.plotly_chart(fig)
```

---

## 12. Common Questions

**Q: Why is my answer different from the handwritten sample?**
A: The handwritten sample has a sign error. We use the correct formula with `(Bt - Bti)`.

**Q: Can I solve for multiple variables at once?**
A: No. The MBE has one equation, so you can only solve for one unknown at a time.

**Q: What if I don't know some inputs?**
A: You must provide all inputs EXCEPT the target variable. If a variable is unknown and not the target, you can try forcing it to 0 by turning off its drive mechanism.

**Q: Can I use Excel files?**
A: Yes! Upload `.xlsx` or `.xls` files. The app uses Pandas to read them.

**Q: How do I switch between oil and gas reservoirs?**
A: Use the "Fluid Type" radio button in the sidebar. The interface, variable list, and MBE equation all change automatically.

**Q: What units does the gas MBE use?**
A: Gas volumes (G, Gp) are in Mscf (thousand standard cubic feet). The answer is displayed in both Mscf and Bscf/MMscf when large.

**Q: Can I share a specific calculation with someone?**
A: Yes! The URL updates with query parameters when you use the tutorial buttons. Copy the URL from your browser after calculating — it contains all inputs and can be shared.

**Q: Is this tool accurate enough for real reservoirs?**
A: This is an educational tool. Real reservoir engineering uses more complex models, but the MBE is the foundation.

---

## 13. Summary

| Component | File | What It Does |
|-----------|------|-------------|
| Math Engine | `mbe_solver.py` | Defines the MBE (oil + gas), solves for any variable using SymPy |
| Shared Config | `config.py` | Variable definitions, SymPy symbols, oil/gas variable lists |
| Web App | `app.py` | Streamlit UI with inputs, charts, timer, export, URL query param hydration |
| Sidebar | `ui/sidebar.py` | Fluid type selector, target variable, drive mechanism toggles |
| Data Input | `ui/data_input.py` | Manual input fields and CSV/Excel file upload |
| Results | `ui/results.py` | Answer display, drive analysis, pie chart, summary table, CSV export |
| Time Series | `ui/time_series.py` | Pressure vs Np and Havlena-Odeh F vs Et charts |
| User Manual | `pages/docs.py` | Built-in documentation with guided tutorials |
| Tests | `test_cases.py` | 5 pytest tests verifying correctness |
| Dependencies | `requirements.txt` | Lists all Python packages needed |
| Sample Data | `test_data_v2.csv` | Ready-to-upload test case |

**The big idea:** Define the equation once with SymPy, let the computer rearrange it for you, and wrap it in a friendly web interface — now supporting both oil and gas reservoirs.

---

*Built with Python, SymPy, Streamlit, and Plotly.*
