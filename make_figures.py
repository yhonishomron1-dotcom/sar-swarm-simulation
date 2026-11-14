"""Build all report figures from results.pkl (and one example run for snapshots)."""
import pickle
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.colors import ListedColormap
import sar_swarm_sim as sim

plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 150, "axes.grid": True, "grid.alpha": 0.25})
C = {"blue": "#1f5fa8", "red": "#c0392b", "green": "#2e8b57", "grey": "#666666", "orange": "#e08a1e"}
MAXT = 1200

def ci(a):
    a = np.asarray(a, float)
    return a.mean(), 1.96 * a.std(ddof=1) / np.sqrt(len(a))

def pad(cov, n=MAXT):
    return np.array(cov + [cov[-1]] * (n - len(cov)))

def metrics(runs):
    t_all, t90, tfull, fin, frac = [], [], [], [], []
    for r in runs:
        cov = np.array(r["coverage"])
        k = r["n_surv"]
        t_all.append(max(r["found_at"].values()) + 1 if len(r["found_at"]) == k else MAXT)
        t90.append(int(np.argmax(cov >= 0.9)) + 1 if (cov >= 0.9).any() else MAXT)
        tfull.append(len(cov) if cov[-1] >= 1.0 else MAXT)
        fin.append(cov[-1]); frac.append(len(r["found_at"]) / k)
    return dict(t_all=t_all, t90=t90, tfull=tfull, final=fin, frac=frac)

# ---------- Figure 1: architecture ----------
def fig_architecture():
    fig, ax = plt.subplots(figsize=(7.2, 3.3)); ax.set_xlim(0, 100); ax.set_ylim(0, 46); ax.axis("off")
    ax.grid(False)
    def box(x, y, w, h, text, fc):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.5",
                                    fc=fc, ec="#333", lw=1))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8.2)
    def arrow(p, q, rad=0.0):
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=11, lw=1.2,
                                     color="#333", connectionstyle=f"arc3,rad={rad}"))
    box(2, 30, 20, 11, "Hidden world\n(rubble map,\nsurvivors)", "#eeeeee")
    box(30, 30, 20, 11, "1. Sense\nline of sight,\nradius R", "#dbe9f6")
    box(58, 30, 20, 11, "2. Share\nmerge maps if\nwithin radio range", "#dbe9f6")
    box(58, 8, 20, 11, "3. Plan\nBFS to nearest\nunclaimed frontier", "#dbe9f6")
    box(30, 8, 20, 11, "4. Move\none cell per\ntick", "#dbe9f6")
    box(82, 19, 16, 11, "5. Metrics\ncoverage,\ntime to find", "#e3f1e6")
    box(2, 8, 20, 11, "Failures\n(optional)\nagents drop out", "#f9e3e0")
    arrow((22.5, 35.5), (29.5, 35.5)); arrow((50.5, 35.5), (57.5, 35.5))
    arrow((68, 29.5), (68, 19.8)); arrow((57.5, 13.5), (50.5, 13.5))
    arrow((40, 19.8), (40, 29.5), rad=0.0)
    ax.text(41.5, 24.5, "next tick", fontsize=7.5, color=C["grey"], rotation=90, va="center")
    arrow((78.5, 14), (85, 18.8), rad=-0.1); arrow((78.5, 35.5), (88, 30.5), rad=-0.1)
    arrow((22.5, 13.5), (29.5, 13.5))
    ax.set_title("Figure 1. Simulation loop: each agent repeats steps 1 to 4 every tick", fontsize=9, loc="left")
    fig.tight_layout(); fig.savefig("fig1_architecture.png"); plt.close(fig)

# ---------- Figure 2: example run snapshots ----------
def fig_snapshots():
    info = {}
    ticks = (0, 20, 60, 140)
    cov, found, k = sim.run(n_agents=8, seed=0, stop_on_found=False, max_ticks=MAXT,
                            info=info, snapshot_ticks=ticks)
    world, surv, snaps = info["world"], info["survivors"], info["snaps"]
    fig, axs = plt.subplots(2, 3, figsize=(7.0, 4.9))
    axs = axs.ravel()
    cmap = ListedColormap(["#f0f0f0", "#ffffff", "#444444"])
    ax = axs[0]
    ax.imshow(world, cmap=ListedColormap(["#ffffff", "#444444"]), origin="lower")
    ax.scatter(*zip(*surv), c=C["red"], marker="*", s=45)
    ax.set_title("Ground truth (hidden from agents)", fontsize=8)
    for ax, t in zip(axs[1:5], ticks):
        known, pos, fnd = snaps[t]
        img = np.where(known, np.where(world == sim.WALL, 2, 1), 0)
        ax.imshow(img, cmap=cmap, origin="lower", vmin=0, vmax=2)
        ax.scatter(*zip(*pos), c=C["blue"], s=14)
        s_found = [s for s in surv if s in fnd]
        if s_found: ax.scatter(*zip(*s_found), c=C["red"], marker="*", s=45)
        ax.set_title(f"t = {t}  ({len(fnd)} of {len(surv)} survivors found)", fontsize=8)
    ax = axs[5]; ax.axis("off")
    ax.text(0.0, 0.9, "Key", fontsize=9, weight="bold", va="top")
    ax.text(0.0, 0.72, "Light grey: not yet explored\nWhite: explored, free\nBlack: rubble\nBlue dots: agents\nRed stars: survivors",
            fontsize=8.5, va="top", linespacing=1.6)
    for ax in axs[:5]:
        ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
        for sp in ax.spines.values(): sp.set_visible(True)
    fig.suptitle("Figure 2. One example run with 8 agents", fontsize=9, x=0.01, ha="left")
    fig.tight_layout(); fig.savefig("fig2_snapshots.png", bbox_inches="tight"); plt.close(fig)
    return cov, found

# ---------- Figure 3: coverage curves by swarm size ----------
def fig_coverage(res):
    fig, ax = plt.subplots(figsize=(6.2, 3.3))
    cols = plt.cm.viridis(np.linspace(0.05, 0.85, 5))
    for col, n in zip(cols, (1, 2, 4, 8, 16)):
        arr = np.array([pad(r["coverage"]) for r in res[("size", n)]])
        m, se = arr.mean(0), 1.96 * arr.std(0, ddof=1) / np.sqrt(len(arr))
        ax.plot(m, color=col, lw=1.6, label=f"{n} agent{'s' if n > 1 else ''}")
        ax.fill_between(range(MAXT), m - se, m + se, color=col, alpha=0.18)
    ax.axhline(0.9, color=C["grey"], ls="--", lw=0.8); ax.text(MAXT * 0.62, 0.915, "90% mapped", fontsize=7.5, color=C["grey"])
    ax.set_xlim(0, MAXT); ax.set_ylim(0, 1.02); ax.set_xlabel("tick"); ax.set_ylabel("fraction of reachable area mapped")
    ax.legend(frameon=False, ncol=1, loc="lower right")
    ax.set_title("Figure 3. Mapping progress by swarm size (mean, shaded = 95% CI, 15 worlds)", fontsize=8.5, loc="left")
    fig.tight_layout(); fig.savefig("fig3_coverage.png"); plt.close(fig)

# ---------- Figure 4: time to find / time to 90% by swarm size ----------
def fig_scaling(res):
    sizes = (1, 2, 4, 8, 16)
    M = {n: metrics(res[("size", n)]) for n in sizes}
    fig, axs = plt.subplots(1, 2, figsize=(7.0, 3.0))
    for ax, key, title in ((axs[0], "t_all", "Time to find all survivors"), (axs[1], "t90", "Time to map 90% of the area")):
        ms = [ci(M[n][key]) for n in sizes]
        ax.errorbar(sizes, [m for m, _ in ms], yerr=[e for _, e in ms], fmt="o-", color=C["blue"], capsize=3, lw=1.5)
        ax.set_xscale("log", base=2); ax.set_xticks(sizes); ax.set_xticklabels(sizes)
        ax.set_xlabel("swarm size"); ax.set_ylabel("ticks"); ax.set_title(title, fontsize=8.5)
    fig.suptitle("Figure 4. Diminishing returns from adding agents (mean, 95% CI)", fontsize=8.5, x=0.01, ha="left")
    fig.tight_layout(); fig.savefig("fig4_scaling.png"); plt.close(fig)
    return M

# ---------- Figure 5: radio range ----------
def fig_comm(res):
    ranges = (2, 6, 12, 18, 30, 60)
    M = {r: metrics(res[("comm", r)]) for r in ranges}
    fig, ax = plt.subplots(figsize=(5.6, 3.0))
    ms = [ci(M[r]["t_all"]) for r in ranges]
    ax.errorbar(ranges, [m for m, _ in ms], yerr=[e for _, e in ms], fmt="o-", color=C["orange"], capsize=3, lw=1.5)
    ax.set_xscale("log"); ax.set_xticks(ranges); ax.set_xticklabels(ranges)
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter()); ax.minorticks_off()
    ax.set_xlabel("radio range (grid cells)"); ax.set_ylabel("ticks to find all survivors")
    ax.set_title("Figure 5. Effect of radio range, 8 agents (mean, 95% CI)", fontsize=8.5, loc="left")
    fig.tight_layout(); fig.savefig("fig5_comm.png"); plt.close(fig)
    return M

# ---------- Figure 6: coordination and failures ----------
def fig_ablation(res):
    keys = [True, "none_random", "none_fixed"]
    Mc = {k: metrics(res[("coord", k)]) for k in keys}
    fps = (0.0, 0.002, 0.005, 0.01)
    Mf = {p: metrics(res[("fail", p)]) for p in fps}
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.1))
    ax = axs[0]
    labels = ["Claims\n(coordinated)", "No claims,\nrandom ties", "No claims,\nfixed ties"]
    vals = [ci(Mc[k]["t_all"]) for k in keys]
    ax.bar(labels, [v[0] for v in vals], yerr=[v[1] for v in vals], color=[C["blue"], C["orange"], C["grey"]], capsize=4, width=0.6)
    ax.set_ylabel("ticks to find all survivors"); ax.set_title("Coordination ablation", fontsize=8.5)
    ax.tick_params(axis="x", labelsize=7.5)
    ax = axs[1]
    vals = [ci(Mf[p]["t_all"]) for p in fps]
    ax.errorbar(range(4), [v[0] for v in vals], yerr=[v[1] for v in vals], fmt="o-", color=C["red"], capsize=3)
    ax.set_xticks(range(4)); ax.set_xticklabels([f"{p:g}" for p in fps])
    ax.set_xlabel("failure probability per agent per tick"); ax.set_ylabel("ticks to find all survivors")
    ax.set_title("Random agent failures", fontsize=8.5)
    fig.suptitle("Figure 6. Ablations with 8 agents (mean, 95% CI)", fontsize=8.5, x=0.01, ha="left")
    fig.tight_layout(); fig.savefig("fig6_ablation.png"); plt.close(fig)
    return Mc, Mf

if __name__ == "__main__":
    res = pickle.load(open("results.pkl", "rb"))
    fig_architecture(); fig_snapshots(); fig_coverage(res)
    Ms = fig_scaling(res); Mcomm = fig_comm(res); Mc, Mf = fig_ablation(res)
    pickle.dump(dict(size=Ms, comm=Mcomm, coord=Mc, fail=Mf), open("metrics.pkl", "wb"))
    print("figures done")
