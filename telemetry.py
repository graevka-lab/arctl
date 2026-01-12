# telemetry.py
class TelemetryCollector:
    def __init__(self):
        self.steps = []
        self.fallback_triggered = False

    def record_step(self, state, raw_metrics, duration):
        self.steps.append({
            "mode": state.mode.value,
            "energy": state.energy,
            "temperature": state.active_config.temperature if state.active_config else 0.0,
            "latency_sec": duration,
            "entropy": raw_metrics.entropy,
            "divergence": raw_metrics.divergence,
            "repetition": raw_metrics.repetition
        })
        if state.mode == "FBK":
            self.fallback_triggered = True

    def report(self):
        if not self.steps:
            return

        last = self.steps[-1]
        print("\n[Adaptive Core Telemetry]")
        print(f"• Final Mode: {last['mode']}")
        print(f"• Energy Left: {last['energy']}")
        print(f"• Temperature: {last['temperature']:.1f}")
        print(f"• Latency: {last['latency_sec']:.3f}s")
        if self.fallback_triggered:
            print("⚠️  FALLBACK TRIGGERED — SYSTEM IN TERMINAL STATE")