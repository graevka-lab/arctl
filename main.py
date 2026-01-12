# main.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from arctl.run import ArctlWrapper
from arctl.integrations import estimate_metrics_from_text
import matplotlib.pyplot as plt

def demo():
    arctl = ArctlWrapper()
    query = "What is the answer to life?"
    drafts = [
        "I think maybe 42...",
        "As an AI, I cannot...",
        "The answer is 42."
    ]
    modes = []
    energies = []

    for draft in drafts:
        metrics = estimate_metrics_from_text(draft, query)
        status = arctl.control(**metrics)
        modes.append(status["mode"])
        energies.append(status["energy"])
        print(f"Draft: '{draft}' → Mode={status['mode']}, Energy={status['energy']}")

    # График
    plt.figure(figsize=(10, 5))
    plt.plot(range(1, len(drafts)+1), energies, marker='o')
    plt.title("Energy Consumption per Draft")
    plt.xlabel("Draft Number")
    plt.ylabel("Energy Level")
    plt.xticks(range(1, len(drafts)+1))
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    demo()