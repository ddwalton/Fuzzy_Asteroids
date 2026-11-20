"""
Headless baseline: ScottDickController (team 1) vs TestController (team 2).

Runs N games with no graphics and prints per-game and total results.
Usage:
    .venv/bin/python run_baseline.py            # 5 games
    .venv/bin/python run_baseline.py 3          # 3 games
"""
import contextlib
import io
import sys
import time
import types

# --- Compatibility shim -------------------------------------------------------
# kesslergame 2.4.0 does `from tkinter import *` at import time (graphics_base.py),
# even when running with GraphicsType.NoGraphics. If this Python has no Tk support
# (e.g. Homebrew Python without python-tk), register an empty stand-in module so the
# headless game can still import. Tkinter graphics will NOT work in that case.
try:
    import tkinter  # noqa: F401
except ImportError:
    sys.modules["tkinter"] = types.ModuleType("tkinter")
# ------------------------------------------------------------------------------

from kesslergame import Scenario, TrainerEnvironment, GraphicsType  # noqa: E402

from scott_dick_controller import ScottDickController  # noqa: E402
from test_controller import TestController  # noqa: E402

NUM_GAMES = int(sys.argv[1]) if len(sys.argv) > 1 else 5
TIME_LIMIT = 60  # seconds of simulated game time per game


def make_scenario(seed: int) -> Scenario:
    # Based on examples/scenario_test.py (v2.4.0), with a second ship added.
    return Scenario(
        name=f"Baseline {seed}",
        num_asteroids=10,
        ship_states=[
            {"position": (400, 400), "angle": 90, "lives": 3, "team": 1, "mines_remaining": 3},
            {"position": (400, 600), "angle": 90, "lives": 3, "team": 2, "mines_remaining": 3},
        ],
        map_size=(1000, 800),
        time_limit=TIME_LIMIT,
        ammo_limit_multiplier=0,  # 0 = unlimited bullets
        stop_if_no_ammo=False,
        seed=seed,
    )


game_settings = {
    "perf_tracker": True,
    "graphics_type": GraphicsType.NoGraphics,
    "realtime_multiplier": 0,  # run as fast as possible
    "graphics_obj": None,
    "frequency": 30,
}
game = TrainerEnvironment(settings=game_settings)

totals: dict[str, dict[str, float]] = {}
t_start = time.perf_counter()

for g in range(1, NUM_GAMES + 1):
    controllers = [ScottDickController(), TestController()]
    pre = time.perf_counter()
    # Professor's controller prints a debug line every frame; swallow it.
    with contextlib.redirect_stdout(io.StringIO()):
        score, perf_data = game.run(scenario=make_scenario(seed=g), controllers=controllers)
    elapsed = time.perf_counter() - pre

    print(f"\n=== Game {g}/{NUM_GAMES}  (stop: {score.stop_reason.name}, "
          f"sim time {score.sim_time:.1f}s, wall {elapsed:.1f}s) ===")
    print(f"{'Team':<24}{'Asteroids hit':>14}{'Shots':>8}{'Accuracy':>10}{'Deaths':>8}")
    for team, ctrl in zip(score.teams, controllers):
        print(f"{ctrl.name:<24}{team.asteroids_hit:>14}{team.shots_fired:>8}"
              f"{team.accuracy:>10.1%}{team.deaths:>8}")
        t = totals.setdefault(ctrl.name, {"asteroids_hit": 0, "shots_fired": 0, "bullets_hit": 0, "deaths": 0})
        t["asteroids_hit"] += team.asteroids_hit
        t["shots_fired"] += team.shots_fired
        t["bullets_hit"] += team.bullets_hit
        t["deaths"] += team.deaths

print(f"\n=== TOTAL over {NUM_GAMES} games (wall {time.perf_counter() - t_start:.1f}s) ===")
print(f"{'Team':<24}{'Asteroids hit':>14}{'Shots':>8}{'Accuracy':>10}{'Deaths':>8}")
for name, t in totals.items():
    acc = t["bullets_hit"] / t["shots_fired"] if t["shots_fired"] else 0.0
    print(f"{name:<24}{int(t['asteroids_hit']):>14}{int(t['shots_fired']):>8}{acc:>10.1%}{int(t['deaths']):>8}")
