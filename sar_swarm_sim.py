"""Search-and-rescue swarm simulation (starter project).

A swarm of agents explores an unknown rubble field from an entrance,
shares maps when within radio range, and looks for survivors.
Everything is simulated: no real data, no hardware.

Run:  python sar_swarm_sim.py
Needs: numpy, matplotlib
"""
from collections import deque

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

UNKNOWN, FREE, WALL = -1, 0, 1
NEIGHBOURS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


# ---------- world ----------
def make_world(rng, size=60, n_blocks=30, n_survivors=6):
    w = np.zeros((size, size), int)
    w[0, :] = w[-1, :] = w[:, 0] = w[:, -1] = WALL
    for _ in range(n_blocks):                       # rubble blocks
        x, y = rng.integers(4, size - 9, 2)
        dx, dy = rng.integers(2, 9, 2)
        w[y:y + dy, x:x + dx] = WALL
    w[1:5, 1:5] = FREE                              # entrance area
    reach = reachable(w, (2, 2))
    cells = [c for c in reach if c[0] > 8 or c[1] > 8]
    idx = rng.choice(len(cells), n_survivors, replace=False)
    return w, {cells[i] for i in idx}, reach


def reachable(world, start):
    seen, q = {start}, deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in NEIGHBOURS:
            n = (x + dx, y + dy)
            if n not in seen and world[n[1], n[0]] == FREE:
                seen.add(n)
                q.append(n)
    return seen


def line(a, b):
    """Bresenham line between two grid points."""
    (x0, y0), (x1, y1) = a, b
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err, pts = dx - dy, []
    while True:
        pts.append((x0, y0))
        if (x0, y0) == (x1, y1):
            return pts
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy


# ---------- agent ----------
class Agent:
    def __init__(self, pos, size, rng=None):
        self.rng = rng                      # optional: random tie-breaking in planning
        self.pos = pos
        self.map = np.full((size, size), UNKNOWN)
        self.found = set()
        self.target = None
        self.alive = True

    def sense(self, world, survivors, radius):
        size = world.shape[0]
        px, py = self.pos
        ring = [(px + d, py + e) for d in range(-radius, radius + 1) for e in (-radius, radius)]
        ring += [(px + e, py + d) for d in range(-radius, radius + 1) for e in (-radius, radius)]
        for tx, ty in ring:
            tx, ty = min(max(tx, 0), size - 1), min(max(ty, 0), size - 1)
            for x, y in line(self.pos, (tx, ty)):
                if (x - px) ** 2 + (y - py) ** 2 > radius ** 2:
                    break
                self.map[y, x] = world[y, x]
                if (x, y) in survivors:
                    self.found.add((x, y))
                if world[y, x] == WALL:             # walls block line of sight
                    break

    def plan(self, claimed, spread=7):
        """BFS to nearest frontier cell that is not close to a claimed target."""
        parent, q, fallback = {self.pos: None}, deque([self.pos]), None
        order = NEIGHBOURS if self.rng is None else [NEIGHBOURS[i] for i in self.rng.permutation(4)]
        while q:
            cur = q.popleft()
            x, y = cur
            is_frontier = cur != self.pos and any(
                self.map[y + dy, x + dx] == UNKNOWN for dx, dy in NEIGHBOURS)
            if is_frontier:
                far = all(abs(x - cx) + abs(y - cy) > spread for cx, cy in claimed)
                if far:
                    return self._path(parent, cur)
                fallback = fallback or cur
            for dx, dy in order:
                n = (x + dx, y + dy)
                if n not in parent and self.map[n[1], n[0]] == FREE:
                    parent[n] = cur
                    q.append(n)
        return self._path(parent, fallback) if fallback else []

    @staticmethod
    def _path(parent, end):
        path = []
        while parent[end] is not None:
            path.append(end)
            end = parent[end]
        return path[::-1]


# ---------- simulation ----------
def run(n_agents=8, seed=0, radius=5, comm_range=18, max_ticks=600, plot=False,
        coordinate=True, fail_prob=0.0, stop_on_found=True, info=None,
        snapshot_ticks=(), tie_break="fixed"):
    """Run one simulation. Returns (coverage_per_tick, {survivor: tick_found}, n_survivors).

    coordinate    : agents avoid frontiers already claimed by nearby agents
    fail_prob     : per-tick probability that each agent permanently fails
    stop_on_found : stop when all survivors are found (otherwise run until the whole
                    reachable area is mapped, or max_ticks)
    tie_break     : "fixed" (deterministic) or "random" (each agent breaks planning
                    ties randomly, so identical agents do not move in lockstep)
    info          : optional dict filled with the world, survivors and snapshots
    snapshot_ticks: ticks at which to store a picture of the swarm's shared map
    """
    rng = np.random.default_rng(seed)
    fail_rng = np.random.default_rng(seed + 1000)   # separate stream: same worlds across settings
    world, survivors, reach = make_world(rng)
    size = world.shape[0]
    agents = [Agent((2, 2), size, np.random.default_rng(seed * 1000 + i) if tie_break == "random" else None)
              for i in range(n_agents)]
    known_ever = np.zeros((size, size), bool)       # everything the live swarm has ever recorded
    coverage, found_at, snaps = [], {}, {}

    for t in range(max_ticks):
        alive = [a for a in agents if a.alive]
        if not alive:
            break
        for a in alive:
            a.sense(world, survivors, radius)

        # share maps and survivor sightings between agents in radio range
        for i, a in enumerate(alive):
            for b in alive[i + 1:]:
                if (a.pos[0] - b.pos[0]) ** 2 + (a.pos[1] - b.pos[1]) ** 2 <= comm_range ** 2:
                    merged = np.where(a.map == UNKNOWN, b.map, a.map)
                    a.map, b.map = merged, merged.copy()
                    a.found = b.found = a.found | b.found

        # plan and move one step each
        moved = False
        for a in alive:
            claimed = []
            if coordinate:
                claimed = [o.target for o in alive
                           if o is not a and o.target is not None
                           and (a.pos[0] - o.pos[0]) ** 2 + (a.pos[1] - o.pos[1]) ** 2 <= comm_range ** 2]
            path = a.plan(claimed)
            a.target = path[-1] if path else None
            if path:
                a.pos = path[0]
                moved = True

        known_ever |= np.any([a.map != UNKNOWN for a in alive], axis=0)
        coverage.append(sum(known_ever[y, x] for x, y in reach) / len(reach))
        for s in set().union(*[a.found for a in alive]):
            found_at.setdefault(s, t)
        if t in snapshot_ticks:
            snaps[t] = (known_ever.copy(), [a.pos for a in alive], set(found_at))

        for a in alive:                              # random permanent failures
            if fail_rng.random() < fail_prob:
                a.alive = False

        if stop_on_found and len(found_at) == len(survivors):
            break
        if not stop_on_found and (coverage[-1] >= 1.0 or not moved):
            break

    if info is not None:
        info.update(world=world, survivors=survivors, reach=reach, snaps=snaps)
    if plot:
        make_plot(world, [a for a in agents if a.alive] or agents, survivors, coverage, found_at)
    return coverage, found_at, len(survivors)


def make_plot(world, agents, survivors, coverage, found_at):
    fig, ax = plt.subplots(1, 2, figsize=(11, 5))
    ax[0].imshow(world, cmap="gray_r", origin="lower")
    ax[0].scatter(*zip(*survivors), c="red", marker="*", s=80, label="survivors")
    ax[0].scatter(*zip(*[a.pos for a in agents]), c="dodgerblue", s=25, label="agents")
    ax[0].set_title("Rubble field (ground truth)")
    ax[0].legend(loc="upper right")
    ax[1].plot(coverage)
    for s, t in found_at.items():
        ax[1].axvline(t, color="red", alpha=0.3)
    ax[1].set(xlabel="tick", ylabel="fraction of area mapped", title="Coverage over time")
    fig.tight_layout()
    fig.savefig("sar_swarm_result.png", dpi=120)


def experiment(sizes=(1, 2, 4, 8, 16), seeds=range(5)):
    """Does a bigger swarm find survivors faster? Averages over several worlds."""
    means = []
    for n in sizes:
        times = []
        for s in seeds:
            cov, found, total = run(n_agents=n, seed=s)
            times.append(len(cov) if len(found) == total else 600)
        means.append(np.mean(times))
        print(f"{n:>2} agents: mean ticks to find all survivors = {means[-1]:.0f}")
    plt.figure(figsize=(5, 4))
    plt.plot(sizes, means, "o-")
    plt.xlabel("swarm size")
    plt.ylabel("mean ticks to find all survivors")
    plt.tight_layout()
    plt.savefig("sar_swarm_scaling.png", dpi=120)


if __name__ == "__main__":
    cov, found, total = run(plot=True)
    print(f"Mapped {cov[-1]:.0%} of reachable area; found {len(found)}/{total} survivors in {len(cov)} ticks")
    experiment()
