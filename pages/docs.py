import urllib.parse

import streamlit as st

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
        f"padding:0.5em 1em;background:#1f77b4;color:white;"
        f'text-decoration:none;border-radius:6px;font-weight:bold;">'
        f"{label}</a>",
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

To launch the app, open a terminal in the project folder and run:

```bash
make run
```

To run the tests:

```bash
make test
```

To clean up cache files:

```bash
make clean
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

**Time-Series Table**
Below the manual input fields, an expandable table lets you enter
multiple rows of time-varying data (production volumes, PVT properties
at different pressures). Enter at least two rows to unlock the
Pressure-Decline and Havlena-Odeh regression plots.

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
- Bo = 1.2511
- Boi = 1.2417
- Swi = 0.20
- cw = 0.000003
- cf = 0.0000086
- deltaP = 670

**What happens:**
The app hides every variable related to gas and water. You see only seven
input boxes — clean and simple. The answer is a modest oil-in-place number,
driven entirely by rock and fluid compressibility.
""")
_example_button(
    "▶️ Load Tutorial 1 in Calculator",
    {
        "target_var": "N",
        "fluid_type": "Oil",
        "reservoir_state": "Unsaturated",
        "water_drive_active": "false",
        "gas_cap_active": "false",
        "expansion_active": "true",
        "Np": "1000",
        "Bo": "1.2511",
        "Boi": "1.2417",
        "Rs": "0",
        "Rsi": "0",
        "Swi": "0.20",
        "cw": "0.000003",
        "cf": "0.0000086",
        "deltaP": "670",
        "auto_calculate": "true",
    },
)

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
- Bo = 1.4800, Boi = 1.58
- Rsi = 1,040, Rs = 850, Rp = 1,100
- Bg = 0.00092, Bgi = 0.00080
- Wp = 50,000, Bw = 1.0, m = 0.25
- Swi = 0.20, cw = 1.5×10⁻⁶, cf = 1.0×10⁻⁶
- deltaP = 200

**What happens:**
The solver rearranges the MBE to isolate We. The pie chart shows how much each
mechanism contributes — with all three drives active, you'll see four slices.
""")
_example_button(
    "▶️ Load Tutorial 2 in Calculator",
    {
        "target_var": "We",
        "fluid_type": "Oil",
        "reservoir_state": "Saturated",
        "water_drive_active": "true",
        "gas_cap_active": "true",
        "expansion_active": "true",
        "N": "10000000",
        "Np": "1000000",
        "Bo": "1.4800",
        "Boi": "1.58",
        "Rsi": "1040",
        "Rs": "850",
        "Rp": "1100",
        "Bg": "0.00092",
        "Bgi": "0.00080",
        "Wp": "50000",
        "Bw": "1.0",
        "m": "0.25",
        "Swi": "0.20",
        "cw": "0.0000015",
        "cf": "0.000001",
        "deltaP": "200",
        "auto_calculate": "true",
    },
)

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
- Bo = 1.33, Boi = 1.35
- Rsi = 600, Rs = 500, Rp = 1,100
- Bg = 0.0015, Bgi = 0.0011
- We = 3,000,000, Wp = 200,000, Bw = 1.0
- m = 0.2

**What happens:**
With expansion off, variables like Swi, cw, cf, and deltaP disappear. The
result — about 36.6 MMSTB — matches the classic reservoir engineering
reference problem.
""")
_example_button(
    "▶️ Load Tutorial 3 in Calculator",
    {
        "target_var": "N",
        "fluid_type": "Oil",
        "reservoir_state": "Saturated",
        "water_drive_active": "true",
        "gas_cap_active": "true",
        "expansion_active": "false",
        "Np": "5000000",
        "Bo": "1.33",
        "Boi": "1.35",
        "Rsi": "600",
        "Rs": "500",
        "Rp": "1100",
        "Bg": "0.0015",
        "Bgi": "0.0011",
        "We": "3000000",
        "Wp": "200000",
        "Bw": "1.0",
        "m": "0.2",
        "auto_calculate": "true",
    },
)

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
_example_button(
    "▶️ Load Tutorial 4 in Calculator",
    {
        "target_var": "G",
        "fluid_type": "Gas",
        "water_drive_active": "false",
        "expansion_active": "false",
        "Gp": "5000000",
        "Bg": "0.0015",
        "Bgi": "0.0012",
        "auto_calculate": "true",
    },
)

st.markdown("---")

st.subheader("Tutorial 5 — Volumetric Undersaturated (Example 11-3)")
st.markdown("""
*Goal: Find N using the F vs Eo+Efw plot for an undersaturated reservoir.*

The volumetric undersaturated plot shows **F vs Eo + Efw** where the slope of
the line is **N**. Enter the data below into the time-series table, then:

**Setup:**
- Fluid: **Oil**
- Target: **N**
- Reservoir State: **Unsaturated**
- Drives: all **OFF** (no gas cap, no water, no expansion)

**What to do:**
1. Expand the **"📊 Optional: Time-Series Data"** section below the manual inputs
2. Copy the data from the table below into the editable grid (each row = one pressure step)
3. Click Calculate
4. Scroll to the Havlena-Odeh section
5. Look for the **Volumetric Undersaturated** plot

**Expected result:** The trendline slope gives N (Initial Oil-in-Place).
""")
with st.expander("📋 Example 11-3 Data — copy into the time-series table"):
    st.dataframe(
        {
            "Np (STB)": [
                20481,
                34750,
                78557,
                101846,
                215681,
                364613,
                542985,
                841591,
                1273530,
                1691887,
                2127077,
                2575330,
            ],
            "Bo (bbl/STB)": [
                1.3104,
                1.3104,
                1.3105,
                1.3105,
                1.3109,
                1.3116,
                1.3122,
                1.3128,
                1.3130,
                1.3150,
                1.3160,
                1.3170,
            ],
            "Wp (bbl)": [0, 0, 0, 0, 0, 0, 159, 805, 2579, 5008, 6500, 8000],
            "deltaP (psi)": [5, 9, 18, 21, 45, 80, 118, 170, 237, 325, 410, 497],
        }
    )


st.markdown("---")

st.subheader("Tutorial 6 — Volumetric Saturated (Case 2)")
st.markdown("""
*Goal: Find N using the F vs Eo plot for a saturated reservoir with no drives.*

The volumetric saturated plot shows **F vs Eo** (oil expansion only) where the
slope is **N**. Enter the data below into the time-series table, then:

**Setup:**
- Fluid: **Oil**
- Target: **N**
- Reservoir State: **Saturated**
- Drives: all **OFF** (no gas cap, no water, no expansion)

**What to do:**
1. Expand the **"📊 Optional: Time-Series Data"** section below the manual inputs
2. Copy the data from the table below into the editable grid
3. Click Calculate
4. Scroll to the Havlena-Odeh section
5. Look for the **Volumetric Saturated** plot

**Expected result:** Slope ≈ 50,000,000 STB (N).
""")
with st.expander("📋 Case 2 Data — copy into the time-series table"):
    st.dataframe(
        {
            "Np (STB)": [
                500000,
                1200000,
                2500000,
                4000000,
                6000000,
                8000000,
                11000000,
                14000000,
                17000000,
                20000000,
            ],
            "Rp (scf/STB)": [600, 700, 850, 1050, 1300, 1600, 2000, 2500, 3100, 3800],
            "Bo (bbl/STB)": [
                1.38,
                1.42,
                1.48,
                1.55,
                1.62,
                1.70,
                1.80,
                1.92,
                2.05,
                2.20,
            ],
            "Rs (scf/STB)": [550, 500, 440, 380, 320, 260, 200, 150, 100, 60],
            "Bg (bbl/scf)": [
                0.0012,
                0.0013,
                0.0015,
                0.0018,
                0.0022,
                0.0028,
                0.0036,
                0.0048,
                0.0065,
                0.0090,
            ],
            "deltaP (psi)": [100, 250, 500, 800, 1200, 1700, 2300, 3000, 3800, 4700],
        }
    )


# ── 4. Understanding the Results

# ── 4. Understanding the Results ────────────────────────────────────────────

st.header("4. Understanding the Results")

st.markdown(r"""
After clicking Calculate (or arriving from a tutorial link), the page scrolls
down to the Results section. Here's what you see, in order:

### The Big Answer
The solved variable is displayed in large blue text, with units.
For example: **N = 36,593,625.50 STB | 36.59 MMSTB**.

### Recovery Factor (Oil only)
If you solved for N (or provided it), the app shows what percentage of the
original oil you've produced: $R_f = (N_p / N) \times 100\%$.

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

### Rp Sensitivity Analysis (Oil + Saturated only)
After the Drive Indices pie chart, a "Rp Sensitivity Analysis" section
appears for saturated oil reservoirs. It shows an interactive graph of
how the Recovery Factor (RF) changes with Cumulative Produced GOR (Rp).
A slider lets you pick different Rp values to see the corresponding RF.
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

**Bo** — Current Oil FVF (bbl/STB)
: How much space 1 barrel of oil takes up now, at reservoir conditions.
This is the formation volume factor for oil at current pressure.

**Boi** — Initial Oil FVF (bbl/STB)
: How much space 1 barrel of oil took up originally, at initial pressure.

**Rs** — Current Solution GOR (scf/STB)
: How much gas is dissolved in each barrel of oil at current pressure.
If the reservoir is unsaturated, $R_s = R_{si}$. Under saturated conditions,
$R_s < R_{si}$ as gas comes out of solution.

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

""")
st.latex(r"""
N = \frac{
    N_p \bigl[ B_o + (R_p - R_s) B_g \bigr] - (W_e - W_p B_w)
}{
    (B_o - B_{oi})
    + (R_{si} - R_s) B_g
    + m B_{oi} \left( \frac{B_g}{B_{gi}} - 1 \right)
    + B_{oi} (1 + m) \left( \frac{S_{wi} c_w + c_f}{1 - S_{wi}} \right) \Delta P
}
""")
st.markdown(r"""

**Top (numerator):** Everything that came out of the reservoir minus what came in.
- $N_p B_o$ — produced oil, converted to reservoir volume
- $N_p (R_p - R_s) B_g$ — extra gas that bubbled out as pressure dropped below the bubble point
- $W_e - W_p B_w$ — net water (aquifer inflow minus produced water)

**Bottom (denominator):** How much space was created underground by expansion.
- $(B_o - B_{oi})$ — oil itself expanded due to pressure change
- $(R_{si} - R_s) B_g$ — solution gas evolved from the oil as pressure dropped
- $m B_{oi} (B_g / B_{gi} - 1)$ — gas cap expanded
- $B_{oi} (1 + m) \frac{S_{wi} c_w + c_f}{1 - S_{wi}} \Delta P$ — rock and water squeezed

**Relationship to the two-phase FVF.** The old "two-phase" formation volume factor
$B_t = B_o + (R_{si} - R_s) B_g$ combined oil shrinkage and solution gas evolution
into a single variable. The expanded form separates these into $B_o$ (oil behavior)
and $R_s$ (gas solubility), which is the textbook-strict presentation and matches
exactly how the professor writes the equation by hand.

For gas reservoirs, the equation is simpler:

""")
st.latex(r"""
G (B_g - B_{gi}) = G_p B_g - (W_e - W_p B_w)
""")
st.markdown("""

You don't need to memorize these. The app handles the math. The important
thing is understanding which terms correspond to which drive mechanisms,
so you know which checkboxes to turn on or off.
""")

st.subheader("The Havlena-Odeh Method")

st.markdown(r"""
The Havlena-Odeh method rearranges the MBE into a straight-line form:

$F = N \times E_t$

Where:
- $F$ = everything produced (oil, gas, water)
- $E_t$ = everything that expanded (oil, gas cap, rock, water)

When you enter multiple rows in the time-series table (one per time step),
the app first plots $F$ vs $E_t$. A straight line through the origin confirms
your drive
mechanism assumptions are correct.

- **Straight line** — your m and We assumptions are correct
- **Curves upward** — you're missing an energy source (try a larger m or We)
- **Curves downward** — you're overestimating the energy

### Parameterized Havlena-Odeh Plots

Depending on your sidebar configuration, the app also shows specialized
linear regressions for different drive mechanisms:

| Reservoir State | Drive Type | Plot | Intercept | Slope |
|---|---|---|---|---|
| Unsaturated (no gas, no water) | Volumetric Undersaturated | $F$ vs $E_o + E_{fw}$ | — | $N$ |
| Saturated (no gas cap, no water) | Volumetric Saturated | $F$ vs $E_o$ | — | $N$ |
| Saturated (gas cap active) | Gas Cap Drive | $F/E_o$ vs $E_{gc}/E_o$ | $N$ | $m \times N$ |
| Saturated (water drive active) | Water Drive | $F/E_o$ vs $\Delta P / E_o$ | $N$ | $K$ |

Where the expansion terms are:
- $E_o = (B_o - B_{oi}) + (R_{si} - R_s) B_g$ — oil shrinkage + solution gas
- $E_{gc} = B_{oi} (B_g / B_{gi} - 1)$ — gas cap expansion (without m)
- $E_{fw}$ — rock and water expansion
- $K$ — water influx constant (from the linear aquifer model $W_e = K \cdot \Delta P$)
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

4. **The time-series table uses your sidebar constants.** Variables like
   Boi, Bgi, Rsi, Bw, Swi, cw, cf, and m come from your manual inputs
   above the table. Only enter what changes with each time step.

5. **For gas reservoirs, switch the fluid type first.** The interface
    completely changes — fewer variables, different target options.
""")


# ── 7. Performance Prediction ────────────────────────────────────────────────

st.header("7. Performance Prediction (Tracy's Method)")

st.markdown("""
The **prediction** page takes the answer from the MBE solver and tells you what
happens next — how much oil you'll produce, how the gas-oil ratio will change,
and how the reservoir saturations will evolve as pressure drops.

Navigate to **prediction** in the sidebar.

### What It Does

Tracy's method (Chapter 12) predicts reservoir performance for a
**solution-gas-drive reservoir** by iterating through pressure steps below the
bubble point. At each step it:

1. Computes Tracy's PVT functions Φₒ and Φg from your fluid data
2. Guesses the producing gas-oil ratio (GOR)
3. Iterates until the GOR from the equation matches the GOR from the
   relative permeability at the computed gas saturation
4. Moves to the next lower pressure, carrying forward the results

### Required Inputs

| Input | Description |
|---|---|
| N | Initial oil-in-place — get this from the MBE solver first |
| Swi | Initial water saturation (decimal) |
| pi | Initial reservoir pressure (psi) |
| pb | Bubble-point pressure (psi) |
| Abandonment pressure | Lowest pressure to predict down to |
| μo | Oil viscosity at reservoir conditions (cp) |
| μg | Gas viscosity at reservoir conditions (cp) |

**PVT Table** — Pressure vs Bo, Bg, Rs. Edit the grid with your own data or
use the pre-loaded Example 12-4 values from the textbook.

**Relative Permeability Table** — Sg vs krg/kro. Two modes:

- **Table mode:** Enter pairs of gas saturation and krg/kro. Use lab data or
  field-calculated values.
- **Exponential mode:** Fit `krg/kro = a × exp(b × Sg)`. Useful when you only
  have the correlation coefficients.

### Outputs

After clicking **Run Prediction**, you get:

- **Summary metrics:** Ultimate recovery, recovery factor, total gas produced,
  pressure range
- **Prediction table:** Np, Gp, GOR, Rp, So, Sg, krg/kro at each pressure step
- **Six performance curves:**
  1. Np vs Pressure — cumulative oil production declines
  2. GOR vs Pressure — gas-oil ratio rises as gas evolves
  3. Cumulative Gp vs Pressure — total gas produced
  4. So/Sg vs Pressure — oil saturation drops, gas saturation grows
  5. Rp vs Pressure — cumulative GOR trend
  6. krg/kro vs Sg — relative permeability ratio on log scale

- **Drive Mechanism Insights:** Automatic analysis — gas mobility warnings,
  recovery factor classification, and secondary gas cap detection
- **CSV Download:** Export all prediction data for reports

### Workflow

1. Use the **app** page to find N (initial oil-in-place)
2. Switch to the **prediction** page
3. Enter N and the PVT/relperm data
4. Run the prediction
5. Use the plots and insights to understand how the reservoir will deplete
""")
