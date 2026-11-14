"""Assemble the PDF report from metrics.pkl and the figure PNGs."""
import pickle
import numpy as np
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle, Preformatted)

M = pickle.load(open("metrics.pkl", "rb"))
N_WORLDS = len(M["size"][1]["t_all"])

def ci(a):
    a = np.asarray(a, float)
    return a.mean(), 1.96 * a.std(ddof=1) / np.sqrt(len(a))
def fmt(a):
    m, e = ci(a); return f"{m:.0f} ± {e:.0f}"
def mean(a): return float(np.mean(a))

# ---------- styles ----------
ss = getSampleStyleSheet()
NAVY = colors.HexColor("#1f3b5c")
body = ParagraphStyle("body", parent=ss["Normal"], fontName="Helvetica", fontSize=9.8, leading=14,
                      alignment=TA_JUSTIFY, spaceAfter=6)
h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=14.5, textColor=NAVY,
                    spaceBefore=12, spaceAfter=6, keepWithNext=1)
h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=11, textColor=NAVY,
                    spaceBefore=8, spaceAfter=4, keepWithNext=1)
title = ParagraphStyle("title", parent=ss["Title"], fontName="Helvetica-Bold", fontSize=21, leading=26,
                       textColor=NAVY, alignment=0, spaceAfter=6)
sub = ParagraphStyle("sub", parent=body, fontSize=11, textColor=colors.HexColor("#555555"), alignment=0)
small = ParagraphStyle("small", parent=body, fontSize=8.3, leading=11, textColor=colors.HexColor("#444444"))
cell = ParagraphStyle("cell", parent=body, fontSize=8.6, leading=11, alignment=0, spaceAfter=0)
cellb = ParagraphStyle("cellb", parent=cell, fontName="Helvetica-Bold")
callout = ParagraphStyle("callout", parent=body, backColor=colors.HexColor("#eef3f9"), borderPadding=(6, 6, 6, 6),
                         borderColor=colors.HexColor("#c4d3e6"), borderWidth=0.6, spaceBefore=6, spaceAfter=10)
bullet = ParagraphStyle("bullet", parent=body, leftIndent=14, bulletIndent=3, spaceAfter=3)

def P(t, s=body): return Paragraph(t, s)
def B(t): return Paragraph(t, bullet, bulletText="•")
def fig(path, width=16.4 * cm):
    w, h = ImageReader(path).getSize()
    return Image(path, width=width, height=width * h / w)

def table(rows, widths, header=True, zebra=True):
    data = [[Paragraph(str(c), cellb if (header and i == 0) else cell) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    st = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b9c2cc")),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5)]
    if header: st.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbe6f2")))
    if zebra:
        for i in range(2, len(rows), 2): st.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f6f8fb")))
    t.setStyle(TableStyle(st)); return t

# ---------- numbers used in the text ----------
S, C_, K, F = M["size"], M["comm"], M["coord"], M["fail"]
t1 = mean(S[1]["t_all"]); t4 = mean(S[4]["t_all"]); t8 = mean(S[8]["t_all"]); t16 = mean(S[16]["t_all"]); t2 = mean(S[2]["t_all"])
sp = lambda n: t1 / mean(S[n]["t_all"])

story = []
# ---------- title ----------
story += [P("Swarm Search-and-Rescue Exploration", title),
          P("A simulation study of swarm size, radio range, coordination and agent failure", sub),
          P("Yhoni D Shomron", ParagraphStyle("author", parent=body, fontName="Helvetica-Bold", fontSize=11, alignment=0, spaceAfter=2)),
          P("Simulation report &nbsp;|&nbsp; 13 November 2026", small), Spacer(1, 10)]

story.append(P("Abstract", h1))
story.append(P(
    "Small robot swarms are a promising way to map collapsed buildings, mines and caves quickly and to locate trapped "
    "people without sending rescuers into danger. This report describes a simple grid-based simulation in which identical "
    "agents explore an unknown rubble field from a single entrance, share maps only when they are within radio range, "
    f"and search for hidden survivors. Using {N_WORLDS} randomly generated worlds per setting, we measured how swarm "
    "size, radio range, coordination and random agent failures affect the time to find all survivors and to map the area. "
    f"A single agent needed about {t1:.0f} ticks to find all survivors. Two agents cut this to about {t2:.0f}, four to "
    f"about {t4:.0f}, and eight to about {t8:.0f}; sixteen agents gave no further improvement ({t16:.0f} ticks). "
    "Coordination mattered in an unexpected way: agents that start together and use a deterministic planner behave "
    "exactly like one agent, so adding robots gains nothing unless something breaks the symmetry. Longer radio range "
    "helped, and the swarm tolerated low failure rates but degraded sharply when most agents failed early. "
    "Everything is simulated on synthetic data, and the model deliberately omits many real-world effects (Section 5).", body))

story.append(P("Key findings", h2))
story += [
    B(f"<b>Diminishing returns.</b> Time to find all survivors fell from about {t1:.0f} ticks (1 agent) to about {t4:.0f} "
      f"(4 agents), then flattened: {t8:.0f} for 8 agents and {t16:.0f} for 16."),
    B("<b>Symmetry is a hidden failure mode.</b> With no claims and a deterministic planner, eight identical agents "
      f"performed exactly like one ({fmt(K['none_fixed']['t_all'])} ticks). Claims or random tie-breaking fixed it."),
    B("<b>Radio range helps most at the short end.</b> Moving from a very short range to a moderate one gave large "
      "gains; very long ranges gave smaller additional gains."),
    B("<b>Robust to light attrition.</b> Low failure rates barely changed the results, but at the highest rate tested "
      "the swarm often failed to find every survivor."),
]

# ---------- 1 introduction ----------
story.append(P("1. Introduction", h1))
story.append(P(
    "After an earthquake, mine collapse or building failure, the first hours are critical, yet the interior is often "
    "too dangerous or too confined for people to enter. Small mobile robots can reach such spaces, and a group of "
    "robots can cover more ground than one. Real deployments, however, are constrained: radio signals do not travel "
    "well through rubble, so robots can share information only when they are near each other, and some robots will "
    "break or get stuck.", body))
story.append(P("This project builds a minimal simulator to explore four questions:", body))
story += [B("<b>RQ1.</b> How does the time to find survivors scale with the number of agents?"),
          B("<b>RQ2.</b> How much does limited radio range slow the search?"),
          B("<b>RQ3.</b> How much does coordination between agents matter?"),
          B("<b>RQ4.</b> How gracefully does the swarm degrade when agents fail?")]
story.append(P(
    "The aim is not to model a specific robot, but to build intuition about the trade-offs and to provide a clean, "
    "reproducible baseline that can be extended. The work is civilian and entirely in simulation.", body))

# ---------- 2 method ----------
story.append(P("2. Method", h1))
story.append(P(
    "The simulator is written in Python (NumPy, Matplotlib). Each simulation advances in discrete time steps called "
    "ticks. Figure 1 shows the loop that every agent runs each tick.", body))
story.append(fig("fig1_architecture.png", 15.5 * cm))
story.append(P("2.1 World", h2))
story.append(P(
    "The world is a 60 × 60 grid. The boundary is solid, and 30 rectangular rubble blocks (2 to 8 cells wide) are placed "
    "at random. A 4 × 4 entrance area is kept clear in one corner, where all agents start. Six survivors are placed "
    "at random on free cells that are reachable from the entrance and not in the entrance area. Each random seed gives a "
    "different world, and the same seeds are used across all experimental settings so that comparisons are paired by world.", body))
story.append(P("2.2 Sensing and mapping", h2))
story.append(P(
    "Each agent keeps its own map with three cell states: unknown, free and rubble. Every tick it senses by casting lines "
    "of sight (Bresenham rays) out to a radius of 5 cells. Rubble blocks a ray, so agents cannot see through walls. "
    "A survivor is recorded as found when its cell is revealed to any agent.", body))
story.append(P("2.3 Communication", h2))
story.append(P(
    "Agents exchange information only with agents within a fixed radio range (18 cells by default, or 30% of the world "
    "width). When two agents are in range they merge their maps (keeping any cell that either has seen) and their survivor "
    "lists. Sharing is direct only: there is no multi-hop relaying, so a chain of agents does not pass messages along. "
    "The radio range is a plain disc and does not account for signal loss through rubble.", body))
story.append(P("2.4 Planning and movement", h2))
story.append(P(
    "A frontier is a known free cell next to an unknown cell. Each tick an agent runs a breadth-first search over its own "
    "map to the nearest frontier and moves one cell along that path. In the coordinated setting, an agent skips frontiers "
    "within 7 cells (Manhattan distance) of a target currently claimed by another agent in radio range, which spreads the "
    "swarm out. If every frontier is claimed, it falls back to the nearest one. In the uncoordinated settings there are no "
    "claims. The planner can break ties in a fixed order (deterministic) or randomly per agent.", body))
story.append(P("2.5 Failures", h2))
story.append(P(
    "In the failure experiment each live agent fails permanently with a fixed probability each tick. A failed agent stops "
    "sensing, moving and sharing. Information it had not already shared with a live agent is lost.", body))
story.append(P("2.6 Metrics", h2))
story += [B("<b>Time to find all survivors</b>: the tick when the last survivor was first recorded by a live agent. "
            "Runs that never found all survivors are counted as the maximum of 1200 ticks (censored)."),
          B("<b>Time to map 90%</b> and <b>time to map 100%</b> of the reachable free cells."),
          B("<b>Survivors found</b>: the average fraction found by the end of the run.")]
story.append(P("2.7 Experimental design", h2))
story.append(P(
    f"Every setting was run on the same {N_WORLDS} worlds (seeds 0 to {N_WORLDS - 1}), with the baseline of 8 agents, "
    "radio range 18, coordination on and no failures. One factor was varied at a time. Results are reported as the mean "
    "with an approximate 95% confidence interval (1.96 × standard error, normal approximation) across worlds.", body))
story.append(table([
    ["Parameter", "Baseline", "Values tested"],
    ["World size", "60 × 60 cells", "fixed"],
    ["Rubble blocks / survivors", "30 / 6", "fixed"],
    ["Sensing radius", "5 cells", "fixed"],
    ["Swarm size", "8", "1, 2, 4, 8, 16"],
    ["Radio range", "18 cells", "2, 6, 12, 18, 30, 60"],
    ["Coordination", "claims on", "claims; no claims with random ties; no claims with fixed ties"],
    ["Failure probability per agent per tick", "0", "0, 0.002, 0.005, 0.01"],
    ["Worlds per setting", f"{N_WORLDS}", "same worlds for all settings"],
    ["Maximum run length", "1200 ticks", "fixed"],
], [5.6 * cm, 3.4 * cm, 7.4 * cm]))

# ---------- 3 results ----------
story.append(P("3. Results", h1))
story.append(P("3.1 An example run", h2))
story.append(P(
    "Figure 2 shows one run with eight agents. The swarm leaves the entrance together, spreads into different branches "
    "of the rubble field, and finds survivors as it goes. The left panel is the hidden ground truth; the others show what "
    "the swarm has collectively mapped at four moments.", body))
story.append(fig("fig2_snapshots.png", 12.4 * cm))

story.append(P("3.2 Swarm size (RQ1)", h2))
story.append(fig("fig3_coverage.png", 12.6 * cm))
story.append(P(
    "Figure 3 shows mapping progress over time. Adding agents steepens the curve, but the curves for 4, 8 and 16 agents "
    "are close together. Figure 4 summarises the time to find all survivors and the time to map 90% of the area.", body))
story.append(fig("fig4_scaling.png", 15.2 * cm))
rows = [["Agents", "Time to find all survivors", "Speed-up vs 1 agent", "Time to map 90%", "Time to map 100%", "Survivors found"]]
for n in (1, 2, 4, 8, 16):
    rows.append([n, fmt(S[n]["t_all"]), f"{sp(n):.1f}×", fmt(S[n]["t90"]), fmt(S[n]["tfull"]), f"{mean(S[n]['frac']) * 100:.0f}%"])
story.append(KeepTogether([P("Table 1. Effect of swarm size (ticks, mean ± 95% CI over worlds).", small),
    table(rows, [1.6 * cm, 3.6 * cm, 2.8 * cm, 3.0 * cm, 3.0 * cm, 2.4 * cm])]))
story.append(Spacer(1, 6))
story.append(P(
    f"Four agents were about {sp(4):.1f} times faster than one, and eight about {sp(8):.1f} times faster. Going from eight "
    f"to sixteen agents did not help: {fmt(S[8]['t_all'])} versus {fmt(S[16]['t_all'])} ticks, which overlap within the "
    "uncertainty. Returns diminish well before the number of agents becomes large for a world of this size.", body))

story.append(P("3.3 Radio range (RQ2)", h2))
story.append(fig("fig5_comm.png", 11.8 * cm))
rows = [["Radio range (cells)", "Time to find all survivors", "Time to map 90%", "Time to map 100%", "Survivors found"]]
for r in (2, 6, 12, 18, 30, 60):
    rows.append([r, fmt(C_[r]["t_all"]), fmt(C_[r]["t90"]), fmt(C_[r]["tfull"]), f"{mean(C_[r]['frac']) * 100:.0f}%"])
story.append(KeepTogether([P("Table 2. Effect of radio range with 8 agents (ticks, mean ± 95% CI).", small),
    table(rows, [3.0 * cm, 4.2 * cm, 3.4 * cm, 3.4 * cm, 2.6 * cm])]))
story.append(Spacer(1, 6))
story.append(P(
    f"With a very short range (2 cells) agents share almost nothing after they separate, and the swarm took "
    f"{fmt(C_[2]['t_all'])} ticks to find all survivors, versus {fmt(C_[18]['t_all'])} at the baseline range of 18. "
    f"The time to map the whole area fell steadily as the range grew, from {fmt(C_[2]['tfull'])} ticks at range 2 to "
    f"{fmt(C_[60]['tfull'])} at range 60.", body))

story.append(P("3.4 Coordination (RQ3) and failures (RQ4)", h2))
story.append(fig("fig6_ablation.png", 15.6 * cm))
rows = [["Condition", "Time to find all survivors", "Time to map 100%", "Survivors found"]]
for label, key in (("Claims (baseline)", True), ("No claims, random tie-breaking", "none_random"), ("No claims, fixed tie-breaking", "none_fixed")):
    rows.append([label, fmt(K[key]["t_all"]), fmt(K[key]["tfull"]), f"{mean(K[key]['frac']) * 100:.0f}%"])
for p in (0.002, 0.005, 0.01):
    rows.append([f"Failure probability {p:g} per tick", fmt(F[p]["t_all"]), fmt(F[p]["tfull"]), f"{mean(F[p]['frac']) * 100:.0f}%"])
story.append(KeepTogether([P("Table 3. Coordination and failure conditions with 8 agents (ticks, mean ± 95% CI).", small),
    table(rows, [6.0 * cm, 4.2 * cm, 3.4 * cm, 3.0 * cm])]))
story.append(Spacer(1, 6))
story.append(P(
    f"<b>Coordination.</b> With no claims and a fixed tie-breaking order, the eight agents took {fmt(K['none_fixed']['t_all'])} "
    f"ticks, identical to the single-agent result in Table 1. The reason is symmetry: all agents start in the same cell "
    "with the same map, so the same planner makes the same choice for each of them, and they move in lockstep forever. "
    f"Either claims ({fmt(K[True]['t_all'])}) or random tie-breaking ({fmt(K['none_random']['t_all'])}) breaks the symmetry. "
    f"For the time to find all survivors the two were not clearly different, but random tie-breaking reached 90% "
    f"mapping sooner ({fmt(K['none_random']['t90'])} versus {fmt(K[True]['t90'])} ticks). This suggests the "
    "7-cell claim rule is not optimal, and that cheap randomness can rival explicit coordination in a world this small.", body))
story.append(P(
    f"<b>Failures.</b> At a failure probability of 0.002 per tick (an expected lifetime of about 500 ticks) results were "
    f"close to the no-failure baseline ({fmt(F[0.002]['t_all'])} versus {fmt(F[0.0]['t_all'])} ticks). At 0.005 the time to "
    f"map the whole area grew noticeably, and at 0.01 (an expected lifetime of about 100 ticks, shorter than a typical "
    f"search) the swarm found only {mean(F[0.01]['frac']) * 100:.0f}% of survivors on average and took much longer.", body))

# ---------- 4 discussion ----------
story.append(P("4. Discussion", h1))
story.append(P(
    "<b>More robots are not always better.</b> The largest gains came from the first few agents. Plausible reasons are that "
    "all agents leave from one entrance and must pass through the same corridors, that agents increasingly explore areas "
    "that are close together, and that the world is small, so the search ends before a large swarm can spread out. "
    "These are hypotheses suggested by the curves, not conclusions: the simulation did not directly measure congestion or "
    "overlap, which would be a natural next experiment.", body))
story.append(P(
    "<b>Symmetry deserves attention.</b> The lockstep result is a simple but important lesson. Identical robots with "
    "identical information and a deterministic rule can behave as a single robot. Real systems have noise, different start "
    "positions and different sensor readings that break the symmetry, but swarm designers should not rely on that by accident.", body))
story.append(P(
    "<b>Communication is a design parameter.</b> The benefit of longer radio range was clearest in the time to map the "
    "whole area. This supports the idea of dropping relay nodes or keeping agents within range of each other, and it "
    "suggests that communication-aware planning is worth studying.", body))
story.append(P(
    "<b>Reliability sets the mission length.</b> A swarm that tolerates a few failures can still fail if the mean time to "
    "failure is shorter than the time needed to search. In practice that argues for redundancy, battery and fault "
    "management, and a way to hand over work from failed units.", body))

# ---------- 5 limitations ----------
story.append(P("5. Limitations", h1))
story.append(P("These results describe a simplified model and should not be read as predictions for real systems.", body))
story += [
    B("The world is a 2D grid with randomly placed rectangular blocks, not a real collapse, tunnel or cave."),
    B("Agents know their own position exactly. There is no localisation error, drift or mapping noise."),
    B("Sensing is noise-free: a survivor is always detected when its cell is seen."),
    B("The radio range is a fixed disc with direct sharing only, with no signal attenuation through rubble and no multi-hop relaying."),
    B("Survivors do not move, and there is no time pressure, battery limit or base station."),
    B(f"Only {N_WORLDS} worlds were used per setting, so some differences are within the uncertainty. Confidence intervals use a normal approximation."),
    B("All agents start together at one entrance. Different deployment patterns could change the conclusions."),
    B("Runs that never found every survivor were counted as the 1200-tick maximum, which understates the true time."),
]

# ---------- 6 future work ----------
story.append(P("6. Future work", h1))
story += [
    B("Add multi-hop relaying and signal loss that depends on the amount of rubble between agents."),
    B("Add localisation and sensor noise, including false alarms and missed detections for survivors."),
    B("Measure congestion and overlap directly, and test different start positions."),
    B("Compare planners such as random walk, frontier-based and market-based task assignment."),
    B("Extend to 3D or tunnel-network maps, and to relay nodes dropped behind the swarm."),
    B("Increase the number of worlds and test on more realistic rubble generators."),
    B("Port the model to MATLAB to compare implementations."),
]

# ---------- 7 reproducibility ----------
story.append(P("7. Reproducibility", h1))
story.append(P("All code is in the accompanying files. The experiments use fixed seeds, so results can be reproduced exactly.", body))
story.append(table([
    ["File", "Purpose"],
    ["sar_swarm_sim.py", "The simulator, with run() and a quick swarm-size experiment"],
    ["sar_experiments.py", "Runs all settings on the same worlds and saves raw results"],
    ["make_figures.py", "Builds Figures 1 to 6 and the summary statistics"],
    ["build_report.py", "Assembles this report"],
], [5.0 * cm, 11.4 * cm]))
story.append(Spacer(1, 4))
story.append(Preformatted("python sar_swarm_sim.py      # demo run and swarm-size check\n"
                          "python sar_experiments.py    # full experiment suite\n"
                          "python make_figures.py       # figures and statistics\n"
                          "python build_report.py       # PDF report",
                          ParagraphStyle("code", fontName="Courier", fontSize=8.5, leading=11,
                                         backColor=colors.HexColor("#f3f3f3"), borderPadding=5)))

# ---------- appendix ----------
story.append(P("Appendix A. Planner pseudocode", h1))
story.append(Preformatted(
"""for each tick:
    for each live agent:  sense(world)                     # line of sight, radius 5
    for each pair of live agents within radio range:
        merge maps and survivor lists
    moved = False
    for each live agent a:
        claimed = targets of other agents within radio range      (if coordination on)
        path = BFS(a.map, from a.position)
               to nearest frontier cell not within 7 cells of any claimed target
               (fallback: nearest frontier)
        if path: a.target = last cell of path; a.position = first cell of path; moved = True
    record coverage and newly found survivors
    for each live agent: with probability p, mark as failed
    stop when all cells are mapped, or nothing moved, or max ticks""",
    ParagraphStyle("code2", fontName="Courier", fontSize=7.8, leading=10.2,
                   backColor=colors.HexColor("#f3f3f3"), borderPadding=5)))

def footer(canvas, doc):
    canvas.saveState(); canvas.setFont("Helvetica", 8); canvas.setFillColor(colors.HexColor("#777777"))
    canvas.drawString(2 * cm, 1.1 * cm, "Swarm search-and-rescue simulation report")
    canvas.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"Page {doc.page}")
    canvas.restoreState()

doc = SimpleDocTemplate("sar_swarm_report.pdf", pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                        topMargin=1.8 * cm, bottomMargin=1.8 * cm, title="Swarm Search-and-Rescue Exploration",
                        author="Yhoni D Shomron")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("report built")
