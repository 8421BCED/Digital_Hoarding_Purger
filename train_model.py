# train_model.py - Train the AI model using your dataset
import os
import cv2
import numpy as np
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import glob
from PIL import Image
import io

# Path to your dataset
dataset_path = "/home/sweet/Desktop/madhu19yo/dataset/dataset(1)/dataset"

categories = ['blurred', 'memes', 'screenshots', 'normal']
X = []
y = []

def extract_features(img_path):
    """Extract features from image"""
    try:
        # Load image
        img = cv2.imread(img_path)
        if img is None:
            return None
        
        # Resize to standard size
        img = cv2.resize(img, (128, 128))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Feature 1: Blur score (Laplacian variance)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Feature 2: Edge density
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size if edges.size > 0 else 0
        
        # Feature 3: Texture (standard deviation)
        texture = np.std(gray) / 255
        
        # Features 4-19: Color histograms (16 bins each for R,G,B)
        hist_r = cv2.calcHist([img], [0], None, [16], [0, 256]).flatten()
        hist_g = cv2.calcHist([img], [1], None, [16], [0, 256]).flatten()
        hist_b = cv2.calcHist([img], [2], None, [16], [0, 256]).flatten()
        
        # Features 20-21: Top/Bottom edge densities (for meme detection)
        h, w = img.shape[:2]
        top_region = edges[0:int(h*0.25), :]
        bottom_region = edges[int(h*0.75):h, :]
        top_density = np.sum(top_region > 0) / top_region.size if top_region.size > 0 else 0
        bottom_density = np.sum(bottom_region > 0) / bottom_region.size if bottom_region.size > 0 else 0
        
        # Feature 22: Meme feature (difference between top and bottom density)
        meme_feature = abs(top_density - bottom_density)
        
        # Feature 23: Aspect ratio
        aspect = w / h
        
        # Combine all features
        features = np.concatenate([
            [blur_score / 1000],  # Normalize blur score
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
        
    except Exception as e:
        print(f"Error extracting features from {img_path}: {e}")
        return None

print("="*60)
print("Training AI Model for Digital Hoarding Punger")
print("="*60)

# Load images from each category
for category in categories:
    folder = os.path.join(dataset_path, category)
    if not os.path.exists(folder):
        print(f"⚠️ Folder not found: {folder}")
        continue
    
    images = glob.glob(os.path.join(folder, "*.*"))
    print(f"Loading {len(images)} images from {category}...")
    
    for img_path in images:
        features = extract_features(img_path)
        if features is not None:
            X.append(features)
            y.append(category)

X = np.array(X)
y = np.array(y)

print(f"\n✅ Total samples loaded: {len(X)}")
print(f"✅ Features shape: {X.shape}")

if len(X) == 0:
    print("❌ No images found! Please check your dataset path.")
    exit()

# Split data for training and testing
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print(f"\n📊 Training set: {len(X_train)} samples")
print(f"📊 Test set: {len(X_test)} samples")

# Train Random Forest model
print("\n🚀 Training Random Forest model...")
clf = RandomForestClassifier(
    n_estimators=200,
    max_depth=20,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1
)

clf.fit(X_train, y_train)

# Evaluate model
train_score = clf.score(X_train, y_train)
test_score = clf.score(X_test, y_test)

print(f"\n📈 Training Accuracy: {train_score:.2%}")
print(f"📈 Test Accuracy: {test_score:.2%}")

# Save the model
model_path = '/home/sweet/Desktop/madhu19yo/image_classifier.pkl'
with open(model_path, 'wb') as f:
    pickle.dump(clf, f)

print(f"\n✅ Model saved to: {model_path}")
print("\n🎉 AI Model training complete!")

# Test on a sample image
def test_model():
    print("\n" + "="*60)
    print("Testing model on sample images...")
    print("="*60)
    
    # Test on one image from each category
    for category in categories:
        folder = os.path.join(dataset_path, category)
        images = glob.glob(os.path.join(folder, "*.*"))
        if images:
            test_img_path = images[0]
            features = extract_features(test_img_path)
            if features is not None:
                pred = clf.predict(features.reshape(1, -1))[0]
                print(f"  {category}: {os.path.basename(test_img_path)}")
                print(f"    Predicted: {pred} {'✓' if pred == category else '✗'}")
    
    print("\n✅ Model test complete!")

test_model()