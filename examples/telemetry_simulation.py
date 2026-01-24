import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

# --- PATH SETUP ---
from pathlib import Path
current_dir = Path(__file__).parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import from the NEW structure
from arctl.core import step, SystemState, ControllerConfig
from arctl.core.states import RawMetrics, OperationalMode

# --- CONFIGURATION ---
STEPS = 150
OUTPUT_FILE = "arctl_demo.gif"

print(f"🚀 INITIALIZING TELEMETRY SIMULATION ({STEPS} steps)...")

# 1. Initialize Controller
cfg = ControllerConfig()
# Mocking time for simulation
state = SystemState.initial(0.0)

# 2. Data Containers
time_points = []
rep_vals = []
temp_vals = []
modes = []

# 3. Simulation Loop
for t in range(STEPS):
    # Synthetic Scenario
    if t < 50:
        input_rep = 0.1 + (t * 0.002) + np.random.normal(0, 0.02)
    elif t < 80:
        input_rep = 0.2 + ((t-50) * 0.03)
    else:
        # Feedback Loop Simulation
        current_temp = state.active_config.temperature if state.active_config else 0.7
        if current_temp > 1.0:
            input_rep = 0.15 + np.random.normal(0, 0.05) # Loop Broken!
        else:
            input_rep = 0.95 # Still stuck
            
    input_rep = np.clip(input_rep, 0.0, 1.0)
    
    # Controller Step
    metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=input_rep)
    state = step(metrics, state, float(t), cfg)
    
    # Record
    time_points.append(t)
    rep_vals.append(input_rep)
    current_temp = state.active_config.temperature if state.active_config else 0.7
    temp_vals.append(current_temp)
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

ax2.set_ylabel('Temperature')
ax2.set_ylim(0, 1.5)
ax2.set_xlabel('Logical Time')

status_text = ax1.text(0.02, 0.85, "", transform=ax1.transAxes, color='white', fontweight='bold')

def init():
    line_rep.set_data([], [])
    line_temp.set_data([], [])
    return line_rep, line_temp, status_text

def animate(i):
    x = time_points[:i]
    line_rep.set_data(x, rep_vals[:i])
    line_temp.set_data(x, temp_vals[:i])
    
    mode = modes[i] if i < len(modes) else modes[-1]
    if mode == OperationalMode.EMERGENCY:
        status_text.set_text("🔴 EMERGENCY")
        status_text.set_color('#ff3333')
    elif mode == OperationalMode.COOLDOWN:
        status_text.set_text("🔵 COOLDOWN")
        status_text.set_color('#00ccff')
    else:
        status_text.set_text("🟢 STANDARD")
        status_text.set_color('#00ff00')
        
    return line_rep, line_temp, status_text

print(f"🎥 Rendering {OUTPUT_FILE}...")
ani = FuncAnimation(fig, animate, init_func=init, frames=STEPS, interval=30, blit=False)
ani.save(OUTPUT_FILE, writer=PillowWriter(fps=30))
print("✅ Done.")