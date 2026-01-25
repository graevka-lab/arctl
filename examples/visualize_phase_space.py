import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from mpl_toolkits.mplot3d import Axes3D

# --- PATH HACK ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from arctl.core.kernel import step, SystemState, ControllerConfig
from arctl.core.states import RawMetrics, OperationalMode

# --- CONFIG ---
STEPS = 200
OUTPUT_FILE = "arctl_phase_space.gif"

print(f"🚀 INITIALIZING 3D PHASE SPACE SIMULATION ({STEPS} steps)...")

# 1. Setup
cfg = ControllerConfig()
state = SystemState.initial(0.0)

# Data containers
history = {
    "rep": [],
    "energy": [],
    "temp": [],
    "mode": []
}

# 2. Simulation Loop
for t in range(STEPS):
    # Scenario: Waves of repetition
    # Sine wave input to trigger periodic emergencies
    base_rep = 0.4 + 0.5 * np.sin(t * 0.1) 
    
    # Feedback: If temp is high, repetition drops
    current_temp = state.active_config.temperature if state.active_config else 0.7
    if current_temp > 1.0:
        real_rep = base_rep * 0.2 # Loop broken
    else:
        real_rep = base_rep

    real_rep = np.clip(real_rep, 0.0, 1.0)
    
    # Step
    metrics = RawMetrics(entropy=0.5, divergence=0.0, repetition=real_rep)
    state = step(metrics, state, float(t), cfg)
    
    history["rep"].append(real_rep)
    history["energy"].append(state.energy)
    history["temp"].append(current_temp)
    history["mode"].append(state.mode)

# 3. Visualization Setup
fig = plt.figure(figsize=(10, 8), facecolor='white')
ax = fig.add_subplot(111, projection='3d')

# Styling
ax.set_xlabel("Repetition (Input)", fontsize=10)
ax.set_ylabel("Energy (Resource)", fontsize=10)
ax.set_zlabel("Temperature (Action)", fontsize=10)
ax.set_title("ARCTL: Phase Space Trajectory", fontsize=14)

# Limits
ax.set_xlim(0, 1)
ax.set_ylim(0, 10)
ax.set_zlim(0, 1.5)

# Lines
line, = ax.plot([], [], [], lw=2, color='blue', alpha=0.6)
head, = ax.plot([], [], [], marker='o', markersize=10, color='red')

def init():
    line.set_data([], [])
    line.set_3d_properties([])
    head.set_data([], [])
    head.set_3d_properties([])
    return line, head

def animate(i):
    # Trajectory up to i
    x = history["rep"][:i]
    y = history["energy"][:i]
    z = history["temp"][:i]
    
    # Color logic based on mode (complex to animate line color in 3d, keeping simple blue)
    # But we change the "Head" color
    current_mode = history["mode"][i] if i < len(history["mode"]) else history["mode"][-1]
    
    if current_mode == OperationalMode.EMERGENCY:
        head.set_color('#ff0000') # Red Hot
        head.set_markersize(15)
    elif current_mode == OperationalMode.COOLDOWN:
        head.set_color('#00ccff') # Cool Blue
        head.set_markersize(8)
    else:
        head.set_color('#00ff00') # Green Standard
        head.set_markersize(6)

    line.set_data(x, y)
    line.set_3d_properties(z)
    
    head.set_data([x[-1]], [y[-1]]) if x else head.set_data([], [])
    head.set_3d_properties([z[-1]]) if z else head.set_3d_properties([])
    
    # Rotate the camera for 3D effect
    ax.view_init(elev=20, azim=i * 0.5)
    
    return line, head

print(f"🎥 Rendering 3D Animation to {OUTPUT_FILE}...")
ani = FuncAnimation(fig, animate, init_func=init, frames=STEPS, interval=40, blit=False)
ani.save(OUTPUT_FILE, writer=PillowWriter(fps=25))
print("✅ Done.")

if __name__ == "__main__":
    pass  # Main code is executed at module level