# arctl/run.py
from .adaptive_core import step, RawMetrics, SystemState, ControllerConfig
import time

class ArctlWrapper:
    def __init__(self):
        self.cfg = ControllerConfig()
        self.state = SystemState.initial(time.time())
    
    def control(self, entropy: float, divergence: float, repetition: float) -> dict:
        now = time.time()
        raw = RawMetrics(entropy, divergence, repetition)
        self.state = step(raw, self.state, now, self.cfg)
        return {
            "mode": self.state.mode.value,
            "temperature": self.state.active_config.temperature if self.state.active_config else 0.0,
            "energy": self.state.energy,
            "fallback": self.state.mode == "FBK"
        }