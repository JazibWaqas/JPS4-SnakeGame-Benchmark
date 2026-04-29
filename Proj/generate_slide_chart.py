import matplotlib.pyplot as plt
import numpy as np

# Data from our 100x100 grid at 10% density
algorithms = ['Dijkstra', 'A*', 'JPS4']
expansions = [8987, 7903, 2379]
colors = ['#e05c5c', '#f5a623', '#3ecf8e'] # Red, Amber, Green

# Set dark theme for the presentation
plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(8, 5))
fig.patch.set_facecolor('#141720')
ax.set_facecolor('#141720')

# Create bars
bars = ax.barh(algorithms, expansions, color=colors, height=0.6)

# Remove borders
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['left'].set_visible(False)

# Add data labels
for bar in bars:
    width = bar.get_width()
    ax.text(width - 500, bar.get_y() + bar.get_height()/2, 
            f'{int(width):,}', 
            ha='right', va='center', color='white', fontweight='bold', fontsize=14)

# Formatting
ax.set_title('Tiles Checked to Find Optimal Path\n(100x100 Grid, Sparse)', 
             color='white', fontsize=16, pad=20, fontweight='bold')
ax.tick_params(axis='y', labelsize=14, left=False)
ax.tick_params(axis='x', bottom=False, labelbottom=False)

# Add "Winner" text for JPS4
ax.text(2379 + 300, 2, '70% Less Work \nSame Exact Path', 
        ha='left', va='center', color='#3ecf8e', fontweight='bold', fontsize=12)

plt.tight_layout()
plt.savefig('presentation_chart.png', dpi=300, bbox_inches='tight', transparent=True)
print("Saved presentation_chart.png")
