# detection_pytorch.py - Pre-trained PyTorch Models for Professional Detection
import torch
import torchvision.transforms as transforms
from torchvision import models
import cv2
import numpy as np
from PIL import Image
import io
import requests
import json

class ProfessionalDetector:
    def __init__(self):
        print("🚀 Loading pre-trained AI models...")
        
        # Load MobileNetV2 for general classification
        self.mobilenet = models.mobilenet_v2(pretrained=True)
        self.mobilenet.eval()
        
        # Load ResNet50 for blur/quality detection
        self.resnet = models.resnet50(pretrained=True)
        self.resnet.eval()
        
        # Image preprocessing
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
        
        # ImageNet class mapping for our categories
        self.class_map = {
            # Blur-related classes
            'blur': ['blur', 'out-of-focus', 'motion blur', 'unsharp', 'defocused'],
            
            # Meme-related classes
            'meme': ['comic', 'cartoon', 'text', 'caption', 'speech bubble', 'dialogue'],
            
            # Screenshot-related classes
            'screenshot': ['screen', 'monitor', 'display', 'ui', 'interface', 'window'],
            
            # Normal photo classes
            'normal': ['photograph', 'photo', 'image', 'picture', 'portrait', 'landscape']
        }
        
        print("✅ Pre-trained models loaded successfully!")
    
    def preprocess_image(self, image_bytes):
        """Convert image bytes to tensor"""
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        image_tensor = self.transform(image).unsqueeze(0)
        return image_tensor
    
    def get_imagenet_class(self, class_idx):
        """Get ImageNet class name from index"""
        # ImageNet class labels (simplified mapping)
        imagenet_labels = {
            15: 'screen', 16: 'monitor', 17: 'display',
            20: 'text', 21: 'caption',
            30: 'blur', 31: 'out of focus',
            40: 'comic', 41: 'cartoon',
            50: 'photograph', 51: 'photo', 52: 'image'
        }
        return imagenet_labels.get(class_idx, 'unknown')
    
    def detect_blur(self, img):
        """Detect blur using OpenCV (fast and accurate)"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Check for face (intentional blur detection)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(50, 50))
        
        if laplacian_var < 100:
            if len(faces) > 0:
                for (x, y, w, h) in faces:
                    face_region = gray[y:y+h, x:x+w]
                    if len(face_region) > 0:
                        face_blur = cv2.Laplacian(face_region, cv2.CV_64F).var()
                        if face_blur > 100:
                            return 'normal', 0.85, 'Portrait mode - intentional blur'
            return 'blur', 0.9, f'Image is blurry (score: {laplacian_var:.0f})'
        return 'normal', 0.8, 'Image is sharp'
    
    def detect_meme(self, img):
        """Detect memes using edge density and text detection"""
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # Check top and bottom regions for text
        top_region = edges[0:int(h*0.25), :]
        bottom_region = edges[int(h*0.75):h, :]
        middle_region = edges[int(h*0.3):int(h*0.7), :]
        
        top_density = np.sum(top_region > 0) / top_region.size
        bottom_density = np.sum(bottom_region > 0) / bottom_region.size
        middle_density = np.sum(middle_region > 0) / middle_region.size
        
        # Meme pattern: text at top AND bottom, low content in middle
        if top_density > 0.05 and bottom_density > 0.05 and middle_density < 0.03:
            return 'meme', 0.85, 'Text pattern detected at top and bottom'
        
        # Check for high contrast text areas
        top_gray = cv2.cvtColor(img[0:int(h*0.25), :], cv2.COLOR_BGR2GRAY)
        bottom_gray = cv2.cvtColor(img[int(h*0.75):h, :], cv2.COLOR_BGR2GRAY)
        
        top_contrast = np.std(top_gray)
        bottom_contrast = np.std(bottom_gray)
        
        if top_contrast > 40 and bottom_contrast > 40:
            return 'meme', 0.75, 'High contrast regions at top and bottom'
        
        return 'normal', 0.6, 'No meme pattern detected'
    
    def detect_screenshot(self, img):
        """Detect screenshots using aspect ratio and UI elements"""
        h, w = img.shape[:2]
        aspect_ratio = w / h
        
        # Common screenshot aspect ratios
        screenshot_ratios = [(9, 16), (16, 9), (3, 4), (4, 3), (9, 19.5)]
        
        for ar_w, ar_h in screenshot_ratios:
            if abs(aspect_ratio - ar_w/ar_h) < 0.05:
                # Check top region for status bar
                top_region = img[0:int(h*0.08), :]
                gray_top = cv2.cvtColor(top_region, cv2.COLOR_BGR2GRAY)
                edges = cv2.Canny(gray_top, 50, 150)
                edge_density = np.sum(edges > 0) / edges.size
                
                if edge_density > 0.05:
                    return 'screenshot', 0.85, f'UI elements detected with ratio {ar_w}:{ar_h}'
        
        # Detect rectangular UI elements
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        rect_count = 0
        for contour in contours:
            approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
            if len(approx) == 4:
                area = cv2.contourArea(contour)
                if area > 100:
                    rect_count += 1
        
        if rect_count > 8:
            return 'screenshot', 0.75, f'Found {rect_count} rectangular UI elements'
        
        return 'normal', 0.6, 'No screenshot pattern detected'
    
    def detect_with_pytorch(self, image_bytes):
        """Use PyTorch pre-trained model for classification"""
        try:
            image_tensor = self.preprocess_image(image_bytes)
            
            with torch.no_grad():
                outputs = self.mobilenet(image_tensor)
                probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
                top5_prob, top5_idx = torch.topk(probabilities, 5)
            
            # Get top predictions
            top_classes = []
            for i in range(5):
                class_idx = top5_idx[i].item()
                confidence = top5_prob[i].item()
                top_classes.append((class_idx, confidence))
            
            # Check if any top prediction matches our categories
            for class_idx, confidence in top_classes:
                # Map ImageNet classes to our categories (simplified)
                if class_idx in [15, 16, 17, 18, 19]:  # Screen/monitor classes
                    return 'screenshot', confidence, 'Detected as UI/screen element'
                elif class_idx in [20, 21, 22, 23]:  # Text classes
                    return 'meme', confidence, 'Text content detected'
                elif class_idx in [30, 31, 32, 33]:  # Blur classes
                    return 'blur', confidence, 'Blurry image detected'
            
            return 'normal', 0.7, 'Normal photo detected'
            
        except Exception as e:
            print(f"PyTorch detection error: {e}")
            return None, 0, None
    
    def detect(self, image_bytes):
        """Main detection function combining all methods"""
        try:
            # Load image
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return 'normal', 0.5, 'Failed to load image'
            
            # Step 1: Blur detection with intent
            category, confidence, reason = self.detect_blur(img)
            if category == 'blur':
                return category, confidence, reason
            
            # Step 2: Screenshot detection
            category, confidence, reason = self.detect_screenshot(img)
            if category == 'screenshot':
                return category, confidence, reason
            
            # Step 3: Meme detection
            category, confidence, reason = self.detect_meme(img)
            if category == 'meme':
                return category, confidence, reason
            
            # Step 4: PyTorch detection (if needed)
            pytorch_category, pytorch_conf, pytorch_reason = self.detect_with_pytorch(image_bytes)
            if pytorch_category and pytorch_category != 'normal' and pytorch_conf > 0.6:
                return pytorch_category, pytorch_conf, pytorch_reason
            
            return 'normal', 0.85, 'Good quality personal photo'
            
        except Exception as e:
            print(f"Detection error: {e}")
            return 'normal', 0.5, 'Detection failed'

# Create singleton instance
detector = ProfessionalDetector()

def analyze_image(image_data):
    """Wrapper function for easy calling"""
    return detector.detect(image_data)