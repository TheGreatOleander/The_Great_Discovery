
import matplotlib.pyplot as plt

def render_pressure_heatmap(pressure_dict):
    nodes = list(pressure_dict.keys())
    values = list(pressure_dict.values())

    plt.figure()
    plt.bar(nodes, values)
    plt.xticks(rotation=90)
    plt.title("Pressure Distribution")
    plt.tight_layout()
    plt.show()
