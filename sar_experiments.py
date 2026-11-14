"""Run all report experiments and save raw results to results.pkl."""
import pickle, sys, time
import sar_swarm_sim as sim

SEEDS = range(15)
MAX_TICKS = 1200
BASE = dict(n_agents=8, comm_range=18, coordinate=True, fail_prob=0.0)

CONFIGS = {}
for n in (1, 2, 4, 8, 16):
    CONFIGS[("size", n)] = {**BASE, "n_agents": n}
for r in (2, 6, 12, 18, 30, 60):
    CONFIGS[("comm", r)] = {**BASE, "comm_range": r}
CONFIGS[("coord", "none_fixed")] = {**BASE, "coordinate": False}
CONFIGS[("coord", "none_random")] = {**BASE, "coordinate": False, "tie_break": "random"}
CONFIGS[("coord", True)] = dict(BASE)
for p in (0.0, 0.002, 0.005, 0.01):
    CONFIGS[("fail", p)] = {**BASE, "fail_prob": p}

# configs that are identical to the baseline are computed once and reused
BASE_KEYS = [("size", 8), ("comm", 18), ("coord", True), ("fail", 0.0)]
import os
cache = pickle.load(open('cache.pkl','rb')) if os.path.exists('cache.pkl') else {}
results = {}
t0 = time.time()
BUDGET = float(sys.argv[1]) if len(sys.argv) > 1 else 1e9
for key, cfg in CONFIGS.items():
    ck = tuple(sorted(cfg.items()))
    if ck not in cache:
        if time.time() - t0 > BUDGET:
            print('budget reached, rerun to continue', flush=True); sys.exit(0)
        runs = []
        for seed in SEEDS:
            cov, found, k = sim.run(seed=seed, stop_on_found=False, max_ticks=MAX_TICKS, **cfg)
            runs.append(dict(seed=seed, coverage=cov, found_at=found, n_surv=k))
        cache[ck] = runs
        pickle.dump(cache, open('cache.pkl','wb'))
        print(f"{key} done  t={time.time()-t0:.0f}s", flush=True)
    results[key] = cache[ck]
pickle.dump(results, open("results.pkl", "wb"))
print("ALL DONE", flush=True)
