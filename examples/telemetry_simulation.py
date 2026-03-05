"""
Telemetry Simulation: Real-time ARCTL monitoring.
Visualizes repetition triggers and temperature intervention.
"""
import os
import sys
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from arctl.core.kernel import ControllerConfig, SystemState, step
from arctl.core.states import OperationalMode, RawMetrics

# --- PATH SETUP ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- CONFIG ---
STEPS = 150
OUTPUT_FILE = "arctl_demo.gif"
WINDOW_SIZE = 5.0
print(f"🚀 INITIALIZING TELEMETRY SIMULATION ({STEPS} steps)...")

# 1. Setup
cfg = ControllerConfig()
state = SystemState.initial(0.0)

# Data containers
time_points = []
rep_vals = []
temp_vals = []
modes = []

# 2. Simulation Loop
for t in range(STEPS):
    if t < 30:
        base_rep = 0.2 + 0.05 * np.sin(t * 0.5)
    elif t < 60:
        base_rep = 0.2 + (t - 30) * 0.03
    else:
        current_temp = state.active_config.temperature if state.active_config else 0.7
        if current_temp > 1.0:
            base_rep = 0.2 + np.random.normal(0, 0.05)
        else:
            base_rep = 0.9
    
    base_rep = np.clip(base_rep, 0.0, 1.0)

    metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=base_rep)
    state = step(metrics, state, float(t) * 0.1, cfg)

    time_points.append(state.logical_time)
    rep_vals.append(base_rep)
    temp_vals.append(state.active_config.temperature if state.active_config else 0.7)
    modes.append(state.mode)

# 4. Visualization (Dark Mode)
plt.style.use('dark_background')
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)

line_rep, = ax1.plot([], [], color='#ff4d4d', lw=2, label='Repetition Metric')
ax1.axhline(y=0.6, color='#666666', ls='--', alpha=0.5)
line_temp, = ax2.plot([], [], color='#00ccff', lw=2, label='Sampling Temperature')

ax1.set_ylabel('Repetition')
ax1.set_ylim(0, 1.1)
ax1.legend(loc='upper left', fontsize=8)
ax1.set_title("ARCTL: HARD CORE INTERVENTION", color='#00ffcc', loc='left', fontsize=10)
ax1.grid(True, alpha=0.1)

ax2.set_ylabel('Temperature')
ax2.set_ylim(0, 1.5)
ax2.set_xlabel('Logical Time (s)')
ax2.grid(True, alpha=0.1)

status_text = ax1.text(0.02, 0.85, "", transform=ax1.transAxes, color='white', fontweight='bold')


def init() -> tuple:
    line_rep.set_data([], [])
    line_temp.set_data([], [])
    ax1.set_xlim(0, WINDOW_SIZE)
    return line_rep, line_temp, status_text


def animate(i: int) -> tuple:
    x = time_points[:i]
    y_rep = rep_vals[:i]
    y_temp = temp_vals[:i]
    
    line_rep.set_data(x, y_rep)
    line_temp.set_data(x, y_temp)

    if x:
        current_time = x[-1]
        if current_time > WINDOW_SIZE:
            ax1.set_xlim(current_time - WINDOW_SIZE, current_time)
            ax2.set_xlim(current_time - WINDOW_SIZE, current_time)
        else:
            ax1.set_xlim(0, WINDOW_SIZE)
            ax2.set_xlim(0, WINDOW_SIZE)

    mode = modes[i] if i < len(modes) else modes[-1]
    if mode == OperationalMode.EMERGENCY:
        status_text.set_text("[!] EMERGENCY")
        status_text.set_color('#ff3333')
        ax2.axvspan(max(0, x[-1] - 0.1), x[-1], color='#330000', alpha=0.5)
    elif mode == OperationalMode.COOLDOWN:
        status_text.set_text("(*) COOLDOWN")
        status_text.set_color('#00ccff')
    else:
        status_text.set_text("(OK) STANDARD")
        status_text.set_color('#00ff00')

    return line_rep, line_temp, status_text


print(f"🎥 Rendering {OUTPUT_FILE}...")
ani = FuncAnimation(fig, animate, init_func=init, frames=STEPS, interval=50, blit=False)
ani.save(OUTPUT_FILE, writer=PillowWriter(fps=20))
print("✅ Done.")

if __name__ == "__main__":
    pass