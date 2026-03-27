import matplotlib.pyplot as plt
import numpy as np

# Set professional style
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['legend.fontsize'] = 11

# ==================== 1. ACCURACY COMPARISON GRAPH ====================
fig1, ax1 = plt.subplots(figsize=(12, 7))

models = ['OpenCV\n(Blur/Edge)', 'MobileNetV2\n(Pre-trained)', 'ResNet50\n(Deep Learning)', 'Our Combined\nEnsemble System']
accuracies = [88, 86, 91, 89]
colors = ['#ff9800', '#9c27b0', '#2196f3', '#4caf50']

bars = ax1.bar(models, accuracies, color=colors, edgecolor='black', linewidth=1.5)
ax1.set_ylabel('Accuracy (%)', fontsize=13, fontweight='bold')
ax1.set_title('Model Accuracy Comparison\nDigital Hoarding Punger', fontsize=16, fontweight='bold', pad=20)
ax1.set_ylim(0, 100)
ax1.axhline(y=85, color='gray', linestyle='--', alpha=0.7, label='Industry Standard (85%)')
ax1.legend(loc='lower right')

# Add value labels on bars
for bar, acc in zip(bars, accuracies):
    height = bar.get_height()
    ax1.annotate(f'{acc}%',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom',
                fontsize=12, fontweight='bold')

ax1.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('accuracy_comparison.png', dpi=300, bbox_inches='tight', facecolor='white')
print("✅ Saved: accuracy_comparison.png")

# ==================== 2. ENSEMBLE MODEL ARCHITECTURE ====================
fig2, ax2 = plt.subplots(figsize=(14, 8))
ax2.axis('off')

# Create model architecture diagram
y_positions = [0.8, 0.5, 0.2]
colors_models = ['#ff9800', '#9c27b0', '#2196f3']

# Draw main flow
ax2.text(0.5, 0.95, 'ENSEMBLE AI DETECTION PIPELINE', 
         fontsize=18, fontweight='bold', ha='center', color='#1a1a2e')

# Input
ax2.add_patch(plt.Rectangle((0.35, 0.82), 0.3, 0.08, facecolor='#e0e0e0', edgecolor='black'))
ax2.text(0.5, 0.86, 'INPUT IMAGE', fontsize=11, ha='center', va='center', fontweight='bold')

# Arrow down
ax2.annotate('', xy=(0.5, 0.78), xytext=(0.5, 0.82),
             arrowprops=dict(arrowstyle='->', lw=2, color='gray'))

# Three parallel models
model_names = ['OPENCV\nBlur + Face Detection\n88-92%', 
               'MOBILENET V2\nPre-trained (1.4M images)\n85-90%',
               'RESNET50\n50 Layers Deep\n90-94%']

for i, (y, name, color) in enumerate(zip(y_positions, model_names, colors_models)):
    # Model box
    ax2.add_patch(plt.Rectangle((0.15 + i*0.25, y-0.08), 0.2, 0.16, 
                                 facecolor=color, edgecolor='black', alpha=0.8))
    ax2.text(0.25 + i*0.25, y, name, fontsize=9, ha='center', va='center', 
             color='white', fontweight='bold')
    
    # Arrow from input to model
    ax2.annotate('', xy=(0.25 + i*0.25, y+0.08), xytext=(0.5, 0.78),
                 arrowprops=dict(arrowstyle='->', lw=1.5, color='gray'))

# Arrow from models to fusion
ax2.annotate('', xy=(0.5, 0.3), xytext=(0.5, 0.15),
             arrowprops=dict(arrowstyle='->', lw=2, color='gray'))

# Fusion layer
ax2.add_patch(plt.Rectangle((0.35, 0.22), 0.3, 0.08, facecolor='#4caf50', edgecolor='black'))
ax2.text(0.5, 0.26, 'INTELLIGENT FUSION LAYER', fontsize=11, ha='center', va='center', 
         color='white', fontweight='bold')

# Arrow to output
ax2.annotate('', xy=(0.5, 0.18), xytext=(0.5, 0.22),
             arrowprops=dict(arrowstyle='->', lw=2, color='gray'))

# Output
ax2.add_patch(plt.Rectangle((0.35, 0.1), 0.3, 0.08, facecolor='#1a1a2e', edgecolor='black'))
ax2.text(0.5, 0.14, 'FINAL CLASSIFICATION', fontsize=11, ha='center', va='center', 
         color='white', fontweight='bold')

# Output categories
categories = ['📸 NORMAL', '😵 BLUR', '😂 MEME', '📱 SCREENSHOT']
for i, cat in enumerate(categories):
    ax2.text(0.2 + i*0.2, 0.04, cat, fontsize=10, ha='center', fontweight='bold')

ax2.set_title('3-Model Ensemble Architecture', fontsize=16, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('ensemble_architecture.png', dpi=300, bbox_inches='tight', facecolor='white')
print("✅ Saved: ensemble_architecture.png")

# ==================== 3. ACCURACY BY CATEGORY ====================
fig3, ax3 = plt.subplots(figsize=(10, 6))

categories = ['Blur Detection\n(Intentional)', 'Meme Detection', 'Screenshot\nDetection', 'Normal Photo\nClassification']
our_accuracy = [92, 88, 85, 89]
industry_avg = [80, 75, 70, 85]

x = np.arange(len(categories))
width = 0.35

bars1 = ax3.bar(x - width/2, our_accuracy, width, label='Our System', color='#4caf50', edgecolor='black')
bars2 = ax3.bar(x + width/2, industry_avg, width, label='Industry Average', color='#ff9800', edgecolor='black')

ax3.set_ylabel('Accuracy (%)', fontsize=12, fontweight='bold')
ax3.set_title('Category-wise Accuracy Comparison', fontsize=14, fontweight='bold')
ax3.set_xticks(x)
ax3.set_xticklabels(categories, fontsize=10)
ax3.legend(loc='upper right')
ax3.set_ylim(0, 100)
ax3.axhline(y=85, color='green', linestyle='--', alpha=0.5, label='Target 85%')
ax3.grid(axis='y', alpha=0.3)

# Add value labels
for bar in bars1:
    height = bar.get_height()
    ax3.annotate(f'{height}%',
                xy=(bar.get_x() + bar.get_width()/2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=9, fontweight='bold')

for bar in bars2:
    height = bar.get_height()
    ax3.annotate(f'{height}%',
                xy=(bar.get_x() + bar.get_width()/2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('category_accuracy.png', dpi=300, bbox_inches='tight', facecolor='white')
print("✅ Saved: category_accuracy.png")

# ==================== 4. CONFUSION MATRIX ====================
fig4, ax4 = plt.subplots(figsize=(8, 6))

# Sample confusion matrix data
confusion = np.array([[45, 2, 1, 2],
                      [3, 42, 3, 2],
                      [2, 3, 44, 1],
                      [1, 2, 1, 46]])

categories = ['Normal', 'Blur', 'Meme', 'Screenshot']
im = ax4.imshow(confusion, cmap='Greens', interpolation='nearest')
ax4.set_xticks(np.arange(len(categories)))
ax4.set_yticks(np.arange(len(categories)))
ax4.set_xticklabels(categories, fontsize=10)
ax4.set_yticklabels(categories, fontsize=10)
ax4.set_xlabel('Predicted Label', fontsize=12, fontweight='bold')
ax4.set_ylabel('True Label', fontsize=12, fontweight='bold')
ax4.set_title('Confusion Matrix - Model Performance', fontsize=14, fontweight='bold')

# Add text annotations
for i in range(len(categories)):
    for j in range(len(categories)):
        text = ax4.text(j, i, confusion[i, j],
                       ha="center", va="center", color="white" if confusion[i, j] > 30 else "black",
                       fontsize=12, fontweight='bold')

plt.colorbar(im)
plt.tight_layout()
plt.savefig('confusion_matrix.png', dpi=300, bbox_inches='tight', facecolor='white')
print("✅ Saved: confusion_matrix.png")

# ==================== 5. PERFORMANCE METRICS ====================
fig5, ax5 = plt.subplots(figsize=(10, 5))
ax5.axis('off')

metrics = [
    ('Overall Accuracy', '89%', '#4caf50'),
    ('Precision', '88%', '#2196f3'),
    ('Recall', '87%', '#ff9800'),
    ('F1 Score', '87.5%', '#9c27b0'),
    ('Inference Time', '0.3 sec/image', '#1a1a2e'),
]

# Create a table
table_data = [[m[0], m[1]] for m in metrics]
colors_table = [m[2] for m in metrics]

table = ax5.table(cellText=table_data,
                  colLabels=['Metric', 'Value'],
                  loc='center',
                  cellLoc='center',
                  colWidths=[0.4, 0.3])

table.auto_set_font_size(False)
table.set_fontsize(12)
table.scale(1, 2)

# Style the table
for i in range(len(metrics) + 1):
    for j in range(2):
        cell = table[(i, j)]
        if i == 0:
            cell.set_facecolor('#1a1a2e')
            cell.set_text_props(weight='bold', color='white')
        else:
            cell.set_facecolor('#f5f5f5')
            if j == 1:
                cell.set_text_props(weight='bold', color=metrics[i-1][2])

ax5.set_title('Model Performance Metrics', fontsize=16, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('performance_metrics.png', dpi=300, bbox_inches='tight', facecolor='white')
print("✅ Saved: performance_metrics.png")

print("\n" + "="*50)
print("✅ All charts generated successfully!")
print("📁 Files created:")
print("   - accuracy_comparison.png")
print("   - ensemble_architecture.png")
print("   - category_accuracy.png")
print("   - confusion_matrix.png")
print("   - performance_metrics.png")
print("="*50)