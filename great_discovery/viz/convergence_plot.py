
import matplotlib.pyplot as plt

def plot_convergence(history):
    pressures = [h[0] for h in history]
    plt.figure()
    plt.plot(pressures)
    plt.title("Pressure Convergence Over Time")
    plt.xlabel("Cycle")
    plt.ylabel("Pressure")
    plt.tight_layout()
    plt.show()
