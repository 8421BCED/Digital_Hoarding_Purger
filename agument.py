# augment_dataset.py
import cv2
import numpy as np
import os
import glob
from sklearn.model_selection import train_test_split
import pickle

def augment_image(img):
    """Create variations of the same image"""
    augmented = []
    
    # Original
    augmented.append(img)
    
    # Rotate
    h, w = img.shape[:2]
    center = (w//2, h//2)
    for angle in [5, -5, 10, -10]:
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(img, M, (w, h))
        augmented.append(rotated)
    
    # Flip horizontally
    augmented.append(cv2.flip(img, 1))
    
    # Brightness variations
    for factor in [0.8, 1.2]:
        bright = cv2.convertScaleAbs(img, alpha=factor, beta=0)
        augmented.append(bright)
    
    # Contrast variations
    for factor in [0.8, 1.2]:
        contrast = cv2.convertScaleAbs(img, alpha=1, beta=factor*50)
        augmented.append(contrast)
    
    return augmented

def extract_features(img):
    """Extract features from image"""
    img = cv2.resize(img, (128, 128))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Blur score
    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    # Edge density
    edges = cv2.Canny(gray, 50, 150)
    edge_density = np.sum(edges > 0) / edges.size if edges.size > 0 else 0
    
    # Color histograms
    hist_r = cv2.calcHist([img], [0], None, [16], [0, 256]).flatten()
    hist_g = cv2.calcHist([img], [1], None, [16], [0, 256]).flatten()
    hist_b = cv2.calcHist([img], [2], None, [16], [0, 256]).flatten()
    
    # Top/Bottom edges
    h, w = img.shape[:2]
    top_edges = edges[0:int(h*0.25), :]
    bottom_edges = edges[int(h*0.75):h, :]
    top_density = np.sum(top_edges > 0) / top_edges.size if top_edges.size > 0 else 0
    bottom_density = np.sum(bottom_edges > 0) / bottom_edges.size if bottom_edges.size > 0 else 0
    meme_feature = abs(top_density - bottom_density)
    
    # Aspect ratio
    aspect = w / h
    
    # Texture features (GLCM-like using variance)
    texture = np.std(gray) / 255
    
    features = np.concatenate([
        [blur_score / 1000],
        [edge_density],
        [texture],
        hist_r,
        hist_g,
        hist_b,
        [top_density],
        [bottom_density],
        [meme_feature],
        [aspect]
    ])
    
    return features

# Load and augment data
dataset_path = "/home/sweet/Desktop/madhu19yo/dataset/dataset/dataset"
categories = ['blurred', 'memes', 'screenshots', 'normal']

X = []
y = []

print("Loading and augmenting dataset...")

for category in categories:
    folder = os.path.join(dataset_path, category)
    images = glob.glob(os.path.join(folder, "*.*"))[:50]  # Use 50 per category
    
    for img_path in images:
        img = cv2.imread(img_path)
        if img is None:
            continue
        
        # Augment image
        augmented_images = augment_image(img)
        
        for aug_img in augmented_images:
            features = extract_features(aug_img)
            X.append(features)
            y.append(category)
    
    print(f"{category}: {len(images)} original → {len(augmented_images) * len(images)} augmented")

X = np.array(X)
y = np.array(y)

print(f"\nTotal training samples: {len(X)}")
print(f"Features shape: {X.shape}")

# Train model
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

print("\nTraining model...")
clf = RandomForestClassifier(n_estimators=200, max_depth=20, random_state=42)
scores = cross_val_score(clf, X, y, cv=5)
print(f"Cross-validation accuracy: {scores.mean():.2%} (+/- {scores.std():.2%})")

# Train final model
clf.fit(X, y)

# Save model
with open('image_classifier.pkl', 'wb') as f:
    pickle.dump(clf, f)

print("\n✅ Model saved as 'image_classifier.pkl'")
print(f"✅ Trained on {len(X)} samples from {len(categories)} categories")