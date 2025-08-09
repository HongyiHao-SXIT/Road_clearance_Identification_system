import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

data = {
    'Metric': ['Overall average confidence'],
    'Stream': [0.6108],
    'Video': [0.4127]
}

df = pd.DataFrame(data)

print("Preview of data:")
print(df)

try:
    plt.style.use('seaborn-v0_8')
except:
    plt.style.use('ggplot')

fig, ax = plt.subplots(figsize=(6, 5))
fig.suptitle('Average Detection Confidence: Stream vs Video', fontsize=14)

bars = ax.bar(['Stream', 'Video'], [df.loc[0, 'Stream'], df.loc[0, 'Video']],
              color=['#1f77b4', '#ff7f0e'], width=0.5)

ax.set_ylabel('Confidence Score', fontsize=12)
ax.set_ylim(0, 1)
ax.grid(axis='y', linestyle='--', alpha=0.7)

for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width() / 2, height + 0.02,
            f'{height:.4f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

plt.tight_layout()

output_path = 'confidence_comparison.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"\nChart saved to: {output_path}")
plt.show()
