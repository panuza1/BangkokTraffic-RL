"""Plot the saved experiment with the system matplotlib installation."""
import csv
from pathlib import Path
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parents[1]
with (root / 'results/phase3_ablation.csv').open(newline='') as f:
    rows = list(csv.DictReader(f))
cases = {'baseline': 'Baseline', 'link3_free_lane': 'Link 3 free lane',
         'link6_storage': 'Link 6 +100 m', 'longer_greens': '18 s greens'}
metrics = [('inserted', 'Inserted'), ('arrived', 'Arrived'), ('running', 'Running'),
           ('waiting', 'Waiting outside'), ('mean_route_halted', 'Mean halted on route edges'),
           ('mean_completed_travel_s', 'Completed travel time (s)')]
fig, axes = plt.subplots(2, 3, figsize=(13, 7), constrained_layout=True)
for ax, (key, label) in zip(axes.flat, metrics):
    for case, name in cases.items():
        data = [r for r in rows if r['case'] == case]
        ax.plot([100 * float(r['demand_fraction']) for r in data], [float(r[key]) for r in data],
                marker='o', label=name)
    ax.set(title=label, xlabel='Estimated demand (%)')
    ax.set_xticks([25, 50, 100])
    ax.grid(alpha=0.25)
axes[0, 0].legend(fontsize=8)
fig.suptitle('Exploratory SUMO ablations — seed 42, 900 s; not calibrated')
fig.savefig(root / 'results/phase3_ablation.png', dpi=160)
