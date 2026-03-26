# train_model.py - Use your dataset to train a classifier
import os
import cv2
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import pickle
import glob

# Path to your dataset
dataset_path = "/home/sweet/Desktop/madhu19yo/dataset/dataset/dataset"

categories = ['blurred', 'memes', 'screenshots', 'normal']
X = []
y = []

def extract_features(img_path):
    """Extract features from image"""
    img = cv2.imread(img_path)
    if img is None:
        return None
    
    # Resize
    img = cv2.resize(img, (128, 128))
    
    # Convert to different color spaces
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Feature 1: Blur score
    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    # Feature 2: Edge density
    edges = cv2.Canny(gray, 50, 150)
    edge_density = np.sum(edges > 0) / edges.size
    
    # Feature 3: Color histogram
    hist_r = cv2.calcHist([img], [0], None, [16], [0, 256]).flatten()
    hist_g = cv2.calcHist([img], [1], None, [16], [0, 256]).flatten()
    hist_b = cv2.calcHist([img], [2], None, [16], [0, 256]).flatten()
    
    # Feature 4: Top/Bottom edge difference (for memes)
    h, w = img.shape[:2]
    top_edges = edges[0:int(h*0.25), :]
    bottom_edges = edges[int(h*0.75):h, :]
    top_density = np.sum(top_edges > 0) / top_edges.size if top_edges.size > 0 else 0
    bottom_density = np.sum(bottom_edges > 0) / bottom_edges.size if bottom_edges.size > 0 else 0
    meme_feature = abs(top_density - bottom_density)
    
    # Feature 5: Aspect ratio
    aspect = w / h
    
    # Combine all features
    features = np.concatenate([
        [blur_score / 1000],  # Normalize
        [edge_density],
        hist_r,
        hist_g,
        hist_b,
        [top_density],
        [bottom_density],
        [meme_feature],
        [aspect]
    ])
    
    return features

print("Loading dataset...")
for category in categories:
    folder = os.path.join(dataset_path, category)
    images = glob.glob(os.path.join(folder, "*.*"))
    
    for img_path in images:
        features = extract_features(img_path)
        if features is not None:
            X.append(features)
            y.append(category)
            print(f"Loaded: {category} - {len(images)} images")

X = np.array(X)
y = np.array(y)

print(f"\nTotal images loaded: {len(X)}")
print(f"Features shape: {X.shape}")

# Train model
print("\nTraining model...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# Test accuracy
accuracy = clf.score(X_test, y_test)
print(f"Model accuracy: {accuracy:.2%}")

# Save model
with open('image_classifier.pkl', 'wb') as f:
    pickle.dump(clf, f)

print("✅ Model saved as 'image_classifier.pkl'")