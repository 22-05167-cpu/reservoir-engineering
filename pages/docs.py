import streamlit as st
import urllib.parse

st.set_page_config(
    page_title="User Manual — MBE Tool",
    page_icon="📖",
    layout="wide",
)

BASE_URL = "/"


def _build_url(params: dict) -> str:
    return BASE_URL + "?" + urllib.parse.urlencode(params)


def _example_button(label: str, params: dict):
    url = _build_url(params)
    st.markdown(
        f'<a href="{url}" target="_self" style="display:inline-block;'
        f'padding:0.5em 1em;background:#1f77b4;color:white;'
        f'text-decoration:none;border-radius:6px;font-weight:bold;">'
        f'{label}</a>',
        unsafe_allow_html=True,
    )


st.title("📖 MBE Solver — User Manual")
st.caption("Everything you need to use this tool, from first click to expert analysis.")


# ── 1. Getting Started ──────────────────────────────────────────────────────

st.header("1. Getting Started")
st.markdown("""
This tool solves the **Material Balance Equation (MBE)** — a formula petroleum
engineers use to understand what's happening inside an oil or gas reservoir.

You give it numbers (production volumes, pressures, fluid properties), and it
calculates the one number you don't know. It can tell you:

- **N** — How much oil was originally underground
- **We** — How much water has flowed in from the aquifer
- **m** — How big the gas cap is, relative to the oil zone
- **deltaP** — How much the pressure dropped
- **G** — How much gas was originally underground

To launch the app, open a terminal and run:

```bash
streamlit run app.py
```

Your browser opens to `http://localhost:8501`. This page — the manual — lives at
`http://localhost:8501/docs`. The calculator itself is at the home page.
""")


# ── 2. The Interface ────────────────────────────────────────────────────────

st.header("2. The Interface")

st.subheader("The Sidebar")

st.markdown("""
Open the app and look at the left sidebar. This is where you tell the tool
*what kind of reservoir* you have and *what you want to solve for*.

**Fluid Type**
Choose between **Oil Reservoir** and **Gas Reservoir**. This changes
everything — the equation, the variable list, and the drive options. Gas
reservoirs are simpler (fewer variables, fewer drive mechanisms).

**Target Variable**
The dropdown labeled *"What do you want to solve for?"* is the single unknown
the computer will calculate. For oil, you can pick **N**, **We**, **m**, or
**deltaP**. For gas, you can pick **G** or **We**.

**Reservoir State** (Oil only)
- **Saturated** — Pressure is at or below the bubble point. Gas is bubbling
  out of the oil. You'll need to enter gas-related variables like `Rp`, `Rsi`,
  `Bg`, `Bgi`.
- **Unsaturated** — Pressure is still above the bubble point. No free gas
  exists. The app automatically hides gas variables and sets `Rp = Rsi`.

**Drive Mechanisms**
Three checkboxes control which physical forces are active in your reservoir:

| Checkbox | When OFF |
|---|---|
| Water Drive Active? | Sets `We`, `Wp`, `Bw` to zero and hides them |
| Gas Cap Active? | Sets `m`, `Bgi` to zero and hides them |
| Rock & Water Expansion Active? | Sets `cw`, `cf`, `Swi`, `deltaP` to zero and hides them |

The smart-hiding behavior means you only see input boxes for variables that
actually matter for your scenario. No clutter, no confusion.

**The "Unsaturated" shortcut**
When you select *Unsaturated*, the app automatically forces `m = 0`, `Bg = 0`,
`Bgi = 0`, and `Rsi = 0` — then hides them all. This is the equivalent of
turning off the Gas Cap drive, since there's no free gas above the bubble
point.
""")

st.subheader("Data Input Area")

st.markdown("""
Below the sidebar header, you choose how to provide your numbers:

**Manual Entry**
Input boxes appear in two columns. Each box shows the variable name, its
description, and a sensible default value. The app automatically hides:

- The variable you're solving for (that's the unknown)
- Variables forced to zero by your drive mechanism choices

Only fill in what you see. If a variable is missing from the screen, the app
is handling it for you.

**File Upload (CSV/Excel)**
Drop a spreadsheet file to load data from columns. The app matches column
names to variables (case-insensitive — `np` and `Np` both work). Only the
first row is used for calculation; if your file has multiple rows, the app
also generates time-series charts (Pressure vs Np, Havlena-Odeh F vs Et).

Hit the big blue **Calculate** button when you're ready. If you arrived here
from a tutorial link, the calculation runs automatically.
""")


# ── 3. Guided Tutorials ─────────────────────────────────────────────────────

st.header("3. Guided Tutorials")
st.caption("Work through these in order. Each one teaches a different concept.")

st.markdown("---")

st.subheader("Tutorial 1 — The Simplest Possible Case")
st.markdown("""
*Goal: See how few inputs you need for an unsaturated reservoir.*

You have a tight oil reservoir above the bubble point. No gas cap, no water
drive — only rock and water expansion are pushing oil out. You produced 1,000
barrels and want to know how many were originally there.

**Setup:**
- Fluid: **Oil**
- Target: **N**
- Reservoir State: **Unsaturated**
- Drives: turn **OFF** Water and Gas Cap, turn **ON** Expansion

**What you'll type:**
- Np = 1,000
- Bt = 1.2511
- Bti = 1.2417
- Swi = 0.20
- cw = 0.000003
- cf = 0.0000086
- deltaP = 670

**What happens:**
The app hides every variable related to gas and water. You see only seven
input boxes — clean and simple. The answer is a modest oil-in-place number,
driven entirely by rock and fluid compressibility.
""")
_example_button("▶️ Load Tutorial 1 in Calculator", {
    'target_var': 'N',
    'fluid_type': 'Oil',
    'reservoir_state': 'Unsaturated',
    'water_drive_active': 'false',
    'gas_cap_active': 'false',
    'expansion_active': 'true',
    'Np': '1000',
    'Bt': '1.2511',
    'Bti': '1.2417',
    'Swi': '0.20',
    'cw': '0.000003',
    'cf': '0.0000086',
    'deltaP': '670',
    'auto_calculate': 'true',
})

st.markdown("---")

st.subheader("Tutorial 2 — Finding Missing Water Influx")
st.markdown("""
*Goal: Solve for We when you already know N.*

You inherited a field report for a saturated oil reservoir. The previous
engineer calculated N = 10 MMSTB but never estimated water influx. All
three drive mechanisms are active.

**Setup:**
- Fluid: **Oil**
- Target: **We**
- Reservoir State: **Saturated**
- Drives: all three **ON**

**What you'll type:**
- N = 10,000,000
- Np = 1,000,000
- Bt = 1.655, Bti = 1.58
- Rsi = 1,040, Rp = 1,100
- Bg = 0.00092, Bgi = 0.00080
- Wp = 50,000, Bw = 1.0, m = 0.25
- Swi = 0.20, cw = 1.5×10⁻⁶, cf = 1.0×10⁻⁶
- deltaP = 200

**What happens:**
The solver rearranges the MBE to isolate We. The pie chart shows how much each
mechanism contributes — with all three drives active, you'll see four slices.
""")
_example_button("▶️ Load Tutorial 2 in Calculator", {
    'target_var': 'We',
    'fluid_type': 'Oil',
    'reservoir_state': 'Saturated',
    'water_drive_active': 'true',
    'gas_cap_active': 'true',
    'expansion_active': 'true',
    'N': '10000000',
    'Np': '1000000',
    'Bt': '1.655',
    'Bti': '1.58',
    'Rsi': '1040',
    'Rp': '1100',
    'Bg': '0.00092',
    'Bgi': '0.00080',
    'Wp': '50000',
    'Bw': '1.0',
    'm': '0.25',
    'Swi': '0.20',
    'cw': '0.0000015',
    'cf': '0.000001',
    'deltaP': '200',
    'auto_calculate': 'true',
})

st.markdown("---")

st.subheader("Tutorial 3 — The Classic Combination Drive")
st.markdown("""
*Goal: Solve for N with both water drive and gas cap active.*

This is the textbook problem. A saturated reservoir with a known gas cap size
and measured water influx. Expansion effects are negligible, so you turn them
off to simplify.

**Setup:**
- Fluid: **Oil**
- Target: **N**
- Reservoir State: **Saturated**
- Drives: Water **ON**, Gas Cap **ON**, Expansion **OFF**

**What you'll type:**
- Np = 5,000,000
- Bt = 1.48, Bti = 1.35
- Rsi = 600, Rp = 1,100
- Bg = 0.0015, Bgi = 0.0011
- We = 3,000,000, Wp = 200,000, Bw = 1.0
- m = 0.2

**What happens:**
With expansion off, variables like Swi, cw, cf, and deltaP disappear. The
result — about 36.6 MMSTB — matches the classic reservoir engineering
reference problem.
""")
_example_button("▶️ Load Tutorial 3 in Calculator", {
    'target_var': 'N',
    'fluid_type': 'Oil',
    'reservoir_state': 'Saturated',
    'water_drive_active': 'true',
    'gas_cap_active': 'true',
    'expansion_active': 'false',
    'Np': '5000000',
    'Bt': '1.48',
    'Bti': '1.35',
    'Rsi': '600',
    'Rp': '1100',
    'Bg': '0.0015',
    'Bgi': '0.0011',
    'We': '3000000',
    'Wp': '200000',
    'Bw': '1.0',
    'm': '0.2',
    'auto_calculate': 'true',
})

st.markdown("---")

st.subheader("Tutorial 4 — Gas Reservoir (Volumetric Depletion)")
st.markdown("""
*Goal: Use the gas MBE for a dry gas field.*

Switch the fluid type to Gas and see a completely different interface. No oil
variables, no gas cap ratio — just gas production and pressure data.

**Setup:**
- Fluid: **Gas**
- Target: **G**
- Drives: Water **OFF**

**What you'll type:**
- Gp = 5,000,000
- Bg = 0.0015
- Bgi = 0.0012

**What happens:**
With only three inputs, the solver calculates G = 25,000,000 Mscf (25 Bscf).
The drive chart shows a single "Gas Expansion" slice. This is the simplest
possible MBE calculation.
""")
_example_button("▶️ Load Tutorial 4 in Calculator", {
    'target_var': 'G',
    'fluid_type': 'Gas',
    'water_drive_active': 'false',
    'expansion_active': 'false',
    'Gp': '5000000',
    'Bg': '0.0015',
    'Bgi': '0.0012',
    'auto_calculate': 'true',
})


# ── 4. Understanding the Results ────────────────────────────────────────────

st.header("4. Understanding the Results")

st.markdown("""
After clicking Calculate (or arriving from a tutorial link), the page scrolls
down to the Results section. Here's what you see, in order:

### The Big Answer
The solved variable is displayed in large blue text, with units.
For example: **N = 36,593,625.50 STB | 36.59 MMSTB**.

### Recovery Factor (Oil only)
If you solved for N (or provided it), the app shows what percentage of the
original oil you've produced: **Rf = (Np / N) × 100%**.

### Drive Mechanism Analysis
A plain-language description of what's pushing the oil (or gas) out:

| Mechanism | When it appears |
|---|---|
| Solution Gas Drive | m = 0 and We = 0 |
| Gas Cap Drive | m > 0 |
| Water Drive | Significant We |
| Combination Drive | Both m > 0 and significant We |
| Volumetric Depletion | Gas reservoir with We = 0 |

### Expert Insights
Context-sensitive warnings appear based on your numbers. For example:
- If `Rp > Rsi`, you're losing pressure energy through the wellbore
- If rock/fluid expansion is the only drive, expect very low recovery factor
- Trend analysis tip: plot N over time to verify your drive mechanism assumptions

### Drive Indices Pie Chart
A donut chart showing each mechanism's percentage contribution.
For oil, the four slices are:
1. Oil Shrinkage / Solution Gas
2. Gas Cap Expansion
3. Rock & Water Expansion
4. Net Water Influx

For gas, the two slices are:
1. Gas Expansion
2. Net Water Influx

### Summary Table
Every variable, its final value, and its status (Target / Input / Forced Zero)
in a scrollable table.

### CSV Export
Click **Download Summary as CSV** to save the results table as
`mbe_results.csv`.
""")


# ── 5. Reference ────────────────────────────────────────────────────────────

st.header("5. Reference")

st.subheader("Variable Glossary")

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("""
**N** — Initial Oil-In-Place (STB)
: How much oil was originally in the ground.

**Np** — Cumulative Oil Produced (STB)
: How much oil you've pumped out so far.

**G** — Initial Gas-In-Place (Mscf)
: How much gas was originally in the ground.

**Gp** — Cumulative Gas Produced (Mscf)
: How much gas you've produced so far.

**Bt** — Current Two-Phase FVF (bbl/STB)
: How much space 1 barrel of oil takes up now, at reservoir conditions.
Bt = Bo + (Rsi − Rs) × Bg. If the reservoir is unsaturated, Rs = Rsi,
so the gas part is zero and Bt = Bo. This single variable works for both
saturated and unsaturated cases — the app uses Bt so you don't have to
worry about which state your reservoir is in.

**Bti** — Initial Two-Phase FVF (bbl/STB)
: How much space 1 barrel of oil took up originally.

**Rp** — Cumulative Produced GOR (scf/STB)
: How much gas came out with each barrel of oil, on average.

**Rsi** — Initial Solution GOR (scf/STB)
: How much gas was dissolved in each barrel of oil originally.

**Bg** — Current Gas FVF (bbl/scf)
: How much space 1 cubic foot of gas takes up now.
""")

with col_b:
    st.markdown("""
**Bgi** — Initial Gas FVF (bbl/scf)
: How much space 1 cubic foot of gas took up originally.

**We** — Cumulative Water Influx (bbl)
: How much water has flowed into the reservoir from the aquifer.

**Wp** — Cumulative Water Produced (bbl)
: How much water you've pumped out.

**Bw** — Water FVF (bbl/STB)
: How much space 1 barrel of water takes up.

**m** — Gas Cap Ratio (dimensionless)
: How big the gas cap is, compared to the oil zone. m = 0.2 means the gas
cap is 20% as large as the oil zone. If you don't have a gas cap, m = 0.
If the gas cap is the same size as the oil zone, m = 1.

**Swi** — Initial Water Saturation (decimal)
: What fraction of the rock pores were originally filled with water.
0.25 means 25%.

**cw** — Water Compressibility (psi⁻¹)
: How much water compresses when pressure drops. Tiny number.

**cf** — Formation Compressibility (psi⁻¹)
: How much the rock itself compresses when pressure drops. Also tiny.

**deltaP** — Change in Pressure (psi)
: How much the pressure dropped from initial to current.
""")

st.subheader("Units Reference")

st.markdown("""
| Unit | Meaning |
|---|---|
| STB | Stock Tank Barrel — oil volume at surface conditions |
| Mscf | Thousand Standard Cubic Feet — gas volume at surface |
| bbl | Barrel — volume at reservoir conditions |
| bbl/STB | Barrels per Stock Tank Barrel — formation volume factor |
| bbl/scf | Barrels per Standard Cubic Foot — gas formation volume factor |
| scf/STB | Standard Cubic Feet per Stock Tank Barrel — gas-oil ratio |
| psi | Pounds per Square Inch — pressure |
| psi⁻¹ | Per psi — compressibility |
| decimal | Fraction (0.25 = 25%) |
| dimensionless | No units — a pure ratio |
""")

st.subheader("The Material Balance Equation (Simplified)")

st.markdown("""
The MBE is a conservation law — what leaves the reservoir must be balanced by
what expands or flows in to fill the empty space.

For oil reservoirs, the full equation is:

```
N = (Np × [Bt + (Rp − Rsi) × Bg] − (We − Wp × Bw))
    ─────────────────────────────────────────────────
    (Bt − Bti) + m × Bti × [Bg/Bgi − 1] + Bti × (1+m) × [(Swi×cw+cf)/(1−Swi)] × deltaP
```

**Top (numerator):** Everything that came out of the reservoir minus what came in.
- `Np × Bt` — produced oil, converted to reservoir volume
- `Np × (Rp − Rsi) × Bg` — extra gas that bubbled out as pressure dropped
- `We − Wp × Bw` — net water (aquifer inflow minus produced water)

**Bottom (denominator):** How much space was created underground by expansion.
- `(Bt − Bti)` — oil itself expanded
- `m × Bti × (Bg/Bgi − 1)` — gas cap expanded
- `Bti × (1+m) × [...] × deltaP` — rock and water squeezed

**Why Bt works for everything.** Bt is the "two-phase" formation volume
factor: Bt = Bo + (Rsi − Rs) × Bg. When the reservoir is above the bubble
point (unsaturated), no solution gas has evolved yet, so Rs = Rsi. The gas
term (Rsi − Rs) × Bg becomes zero, and Bt simply equals Bo — the oil FVF.
When the reservoir is below the bubble point (saturated), Rs < Rsi, gas
comes out of solution, and Bt captures both the oil and the liberated gas
in one variable. This is why the manual works for both saturated and
unsaturated reservoirs — Bt handles the transition automatically.

For gas reservoirs, the equation is simpler:

```
G × (Bg − Bgi) = Gp × Bg − (We − Wp × Bw)
```

You don't need to memorize these. The app handles the math. The important
thing is understanding which terms correspond to which drive mechanisms,
so you know which checkboxes to turn on or off.
""")

st.subheader("The Havlena-Odeh Method")

st.markdown("""
The Havlena-Odeh method rearranges the MBE into a straight-line form:

**F = N × Et**

Where:
- **F** = everything produced (oil, gas, water)
- **Et** = everything that expanded (oil, gas cap, rock, water)

When you upload a CSV with multiple rows (one per time step), the app plots
F vs Et. A straight line through the origin confirms your drive mechanism
assumptions are correct. The slope of the line is **N**.

- **Straight line** — your m and We assumptions are correct
- **Curves upward** — you're missing an energy source (try a larger m or We)
- **Curves downward** — you're overestimating the energy
""")


# ── 6. Troubleshooting ──────────────────────────────────────────────────────

st.header("6. Troubleshooting")

st.subheader("Common Errors")

st.markdown("""
**"Missing known values for variables: ..."**
: You left one or more input boxes empty. The app tells you exactly which
variables are missing. Fill them in and try again.

**"Division by zero or undefined expression after substitution"**
: Your inputs created a mathematical impossibility — usually a zero in a
denominator like `Bg/Bgi` when both are forced to zero. Turn on the
relevant drive mechanism or provide a non-zero value.

**"Target variable cancels out"**
: The variable you're solving for doesn't appear in the equation after all
other values are substituted. For example, solving for deltaP when expansion
is turned off has no effect — turn on Rock & Water Expansion first.

**"No valid solution found"**
: SymPy couldn't find a numeric answer. Try different initial guesses, or
check that your inputs are physically reasonable.
""")

st.subheader("Quick Tips")

st.markdown("""
1. **Start with the tutorials above.** Each one loads a working example with
   one click. Study the setup, then tweak one number at a time to see how the
   answer changes.

2. **Turn off drives you don't need.** Unsure about water influx? Uncheck
   Water Drive. The app zeros it out and hides the relevant input boxes.

3. **The pie chart is your diagnostic tool.** If you expected "Water Drive"
   but the chart shows 100% "Solution Gas Drive," your We value is probably
   wrong or missing.

4. **CSV column names are case-insensitive.** Upload a file with columns
   named `np`, `bt`, `WE` — they'll all map correctly.

5. **For gas reservoirs, switch the fluid type first.** The interface
   completely changes — fewer variables, different target options.
""")
