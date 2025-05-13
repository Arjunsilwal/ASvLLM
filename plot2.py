import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from matplotlib.animation import FuncAnimation

df = pd.read_csv("experiments/gpt_experiments/detailed/detailed_prompt_crossing_experiment_1.csv")
df = df.sort_values("time_s")

times = np.unique(df["time_s"].values)
vessel_ids = np.unique(df["vessel_id"].values)

coords = np.zeros((len(vessel_ids), len(times), 2))
has_goals = ("goal_x" in df.columns and "goal_y" in df.columns)
if has_goals:
    goals = np.zeros((len(vessel_ids), 2))

for i, vid in enumerate(vessel_ids):
    sub = df[df["vessel_id"] == vid].set_index("time_s")[["x", "y"]]
    re = sub.reindex(times, method="nearest")
    coords[i, :, 0] = re["x"].values
    coords[i, :, 1] = re["y"].values

    if has_goals:
        gxs = df[df["vessel_id"] == vid]["goal_x"].dropna().unique()
        gys = df[df["vessel_id"] == vid]["goal_y"].dropna().unique()
        if len(gxs) and len(gys):
            goals[i, 0] = gxs[0]
            goals[i, 1] = gys[0]

fig, ax = plt.subplots(figsize=(8, 6))
plt.subplots_adjust(bottom=0.25)

# plot full tracks in light dashed
for i, vid in enumerate(vessel_ids):
    ax.plot(coords[i, :, 0], coords[i, :, 1], "--", alpha=0.3, label=f"Vessel {vid}")

# plot goals
if has_goals:
    for i in range(len(vessel_ids)):
        ax.scatter(goals[i, 0], goals[i, 1], marker="*", s=150, edgecolor="r", zorder=2)

ax.invert_yaxis()
ax.set_aspect("auto")
ax.set_xlabel("X (px)")
ax.set_ylabel("Y (px)")
ax.set_title("Animated Vessel Trajectories")
ax.legend(loc="upper right")

# one dot per vessel
dots = [ax.scatter([], [], s=100, edgecolor="k", zorder=3) for _ in vessel_ids]

ax_slider = plt.axes([0.15, 0.10, 0.70, 0.03])
slider = Slider(ax_slider, "Time (s)", times[0], times[-1], valinit=times[0])


def update(frame_idx):
    for i, d in enumerate(dots):
        d.set_offsets([coords[i, frame_idx]])
    return dots


def on_slider(val):
    # jump to that time
    idx = int(np.argmin(np.abs(times - val)))
    update(idx)
    fig.canvas.draw_idle()


slider.on_changed(on_slider)


ani = FuncAnimation(
    fig,
    update,
    frames=len(times),
    interval=400,  # ms between frames – increase to slow down
    blit=True,
    repeat=False
)

plt.show()
