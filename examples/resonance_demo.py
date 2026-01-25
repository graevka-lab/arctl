"""
Resonance Analysis Demo.
Shows how the system extracts invariant truth across different cognitive modes.
"""

import sys
import os

# --- PATH SETUP (Robust) ---
from pathlib import Path
# Get absolute path to the examples directory
current_dir = Path(__file__).parent
# Navigate up one level to the project root
project_root = current_dir.parent

# Add project root to sys.path so Python can find the 'arctl' package
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
# --------------------------

# Now Python can see the 'arctl' package
from arctl.engine.synthesizer import ResonanceSynthesizer
from arctl.verification.metrics import ResonanceVerifier

class MockModel:
    """
    A mock LLM for demonstration purposes. 
    Replace this with your actual API wrapper (OpenAI, Anthropic, Local).
    """
    def generate(self, prompt: str) -> str:
        # Simulating model responses based on the injected anchor
        if "Analytical Clarity" in prompt:
            return "PWM (Pulse Width Modulation) controls analog circuits via digital signals by varying the duty cycle."
        elif "Creative Exploration" in prompt:
            return "PWM is like a flickering candle! Digital pulses breathe life into circuits through the rhythm of the duty cycle."
        elif "Critical Vigilance" in prompt:
            return "WARNING: PWM implementation requires careful EMI filtering. Incorrect duty cycles can damage components."
        else:
            return "PWM varies pulse width to control power."

def main():
    print("🚀 Initializing Resonance Engine...")
    
    # 1. Setup
    model = MockModel() 
    synthesizer = ResonanceSynthesizer(model)
    verifier = ResonanceVerifier()
    
    query = "What is PWM?"
    print(f"\nQuery: {query}")
    
    # 2. Multi-Pass Generation
    print("-> Running Multi-Pass Synthesis...")
    multi_result = synthesizer.multi_synthesize(query, domain="technical")
    
    # 3. Verification
    print("-> Verifying Semantic Invariance...")
    verification = verifier.verify(multi_result["responses"])
    
    # 4. Report
    print("\n=== RESONANCE REPORT ===")
    print(f"Resonance Score: {verification.get('resonance_score', 0):.3f}")
    print(f"Stability: {'✅ STABLE' if verification.get('is_stable') else '⚠️ UNSTABLE'}")
    
    print("\n=== PERSPECTIVES ===")
    for mode, response in multi_result["responses"].items():
        print(f"\n[{mode.upper()}]: {response}")

if __name__ == "__main__":
    try:
        main()
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure all dependencies are installed: pip install sentence-transformers numpy matplotlib")
        exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()