import pandas as pd
import matplotlib.pyplot as plt

# Read the CSV you wrote during simulation
# Expect columns: time_s, vessel_id, x, y, goal_x, goal_y
df = pd.read_csv("vessel_paths.csv")

fig, ax = plt.subplots()

for vid, group in df.groupby("vessel_id"):
    ax.plot(group["x"], group["y"], label=f"Vessel {vid}")
    # mark start
    ax.scatter(group.iloc[0]["x"], group.iloc[0]["y"], marker="o", s=50, edgecolor="k")
    # mark goal (same for every row of that vessel)
    gx, gy = group.iloc[0]["goal_x"], group.iloc[0]["goal_y"]
    ax.scatter(gx, gy, marker="*", s=100, edgecolor="r")

ax.set_aspect("equal", "box")
ax.set_xlabel("X (px)")
ax.set_ylabel("Y (px)")
ax.set_title("Vessel Trajectories")
ax.legend()
plt.show()
