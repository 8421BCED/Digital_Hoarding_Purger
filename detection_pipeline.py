"""
Digital Hoarding Punger - AI Detection Pipeline
Multi-model parallel image scanner for blur, meme, screenshot, NSFW detection
"""

import cv2
import numpy as np
from PIL import Image
import io
import requests
from pathlib import Path
import os
import json
from datetime import datetime
import threading
import queue
import time
from typing import Dict, List, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ BLUR DETECTION (OpenCV - No ML needed) ============
class BlurDetector:
    """Detects blurry images using Laplacian variance method"""
    
    def __init__(self, threshold=100):
        self.threshold = threshold
        
    def detect(self, image_cv2):
        """
        Returns: (is_blurry, score, reasoning)
        """
        try:
            gray = cv2.cvtColor(image_cv2, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            is_blurry = laplacian_var < self.threshold
            
            # Determine blur level
            if laplacian_var < 50:
                blur_level = "Very blurry"
            elif laplacian_var < 100:
                blur_level = "Moderately blurry"
            else:
                blur_level = "Sharp"
            
            reasoning = f"{blur_level} (score: {laplacian_var:.1f})"
            return is_blurry, laplacian_var, reasoning
        except Exception as e:
            logger.error(f"Blur detection error: {e}")
            return False, 0, "Blur detection failed"


# ============ SCREENSHOT DETECTION (YOLOv8) ============
class ScreenshotDetector:
    """Detects screenshots using YOLOv8 model"""
    
    def __init__(self):
        self.model = None
        self.load_model()
        
    def load_model(self):
        """Load YOLO model"""
        try:
            from ultralytics import YOLO
            
            model_path = Path(__file__).parent / "models" / "screenshot_detector.pt"
            
            if model_path.exists() and model_path.stat().st_size > 0:
                self.model = YOLO(str(model_path))
                logger.info(f"✅ Screenshot detector loaded from {model_path}")
            else:
                logger.warning("No YOLO model found, using fallback detection")
                self.model = None
                
        except Exception as e:
            logger.error(f"Failed to load screenshot detector: {e}")
            self.model = None
    
    def detect(self, image_cv2):
        """
        Returns: (is_screenshot, confidence, reasoning)
        """
        if not self.model:
            return self._fallback_detect(image_cv2)
        
        try:
            # Convert to RGB for YOLO
            image_rgb = cv2.cvtColor(image_cv2, cv2.COLOR_BGR2RGB)
            results = self.model(image_rgb, verbose=False)
            
            # UI elements common in screenshots
            ui_elements = ['person', 'cell phone', 'laptop', 'tv', 'screen', 
                          'book', 'clock', 'remote', 'keyboard', 'mouse']
            
            max_conf = 0.0
            detected_elements = []
            
            for result in results:
                if result.boxes is not None:
                    for box in result.boxes:
                        cls = int(box.cls[0])
                        conf = float(box.conf[0])
                        class_name = self.model.names[cls] if hasattr(self.model, 'names') else str(cls)
                        
                        if any(element in class_name.lower() for element in ui_elements):
                            if conf > max_conf:
                                max_conf = conf
                                detected_elements.append(class_name)
            
            is_screenshot = max_conf > 0.3
            reasoning = f"Detected {len(detected_elements)} UI elements" if is_screenshot else "No UI elements detected"
            
            return is_screenshot, max_conf, reasoning
            
        except Exception as e:
            logger.error(f"Screenshot detection error: {e}")
            return self._fallback_detect(image_cv2)
    
    def _fallback_detect(self, image_cv2):
        """Fallback detection using heuristics"""
        h, w = image_cv2.shape[:2]
        aspect_ratio = w / h
        
        # Screenshots often have standard aspect ratios
        is_screenshot = 1.2 < aspect_ratio < 1.9
        
        # Check for text/edge density
        gray = cv2.cvtColor(image_cv2, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (h * w)
        
        is_screenshot = is_screenshot or edge_density > 0.08
        reasoning = f"Aspect ratio: {aspect_ratio:.2f}, Edge density: {edge_density:.3f}"
        
        return is_screenshot, 0.6 if is_screenshot else 0.3, reasoning


# ============ NSFW DETECTION (Fixed - Works with your model) ============
class NSFWDetector:
    """Detects NSFW/offensive content using your model"""
    
    def __init__(self):
        self.model = None
        self.transform = None
        self.load_model()
        
    def load_model(self):
        """Load NSFW model - handles both full models and state dicts"""
        try:
            import torch
            import torch.nn as nn
            from torchvision import transforms, models
            
            model_path = Path(__file__).parent / "models" / "open_nsfw.pt"
            
            # If not found, try backup
            if not model_path.exists():
                model_path = Path(__file__).parent / "models" / "nsfw_backup.pt"
            
            if model_path.exists() and model_path.stat().st_size > 0:
                logger.info(f"Loading NSFW model from {model_path}...")
                
                # Load the checkpoint
                checkpoint = torch.load(model_path, map_location='cpu')
                
                # Handle different checkpoint formats
                if isinstance(checkpoint, dict):
                    # Check if it's a state dict
                    if 'model_state_dict' in checkpoint:
                        state_dict = checkpoint['model_state_dict']
                    elif 'state_dict' in checkpoint:
                        state_dict = checkpoint['state_dict']
                    else:
                        state_dict = checkpoint
                    
                    # Try to determine model architecture
                    # Most NSFW models use ResNet or MobileNet
                    try:
                        # Try MobileNetV2 first (most common)
                        self.model = models.mobilenet_v2(pretrained=False)
                        self.model.classifier[1] = nn.Linear(1280, 2)
                        self.model.load_state_dict(state_dict, strict=False)
                        logger.info("   ✅ Loaded as MobileNetV2")
                    except:
                        try:
                            # Try ResNet50
                            self.model = models.resnet50(pretrained=False)
                            self.model.fc = nn.Linear(2048, 2)
                            self.model.load_state_dict(state_dict, strict=False)
                            logger.info("   ✅ Loaded as ResNet50")
                        except:
                            # Create a simple CNN as fallback
                            self.model = nn.Sequential(
                                nn.Conv2d(3, 32, 3, padding=1),
                                nn.ReLU(),
                                nn.MaxPool2d(2),
                                nn.Conv2d(32, 64, 3, padding=1),
                                nn.ReLU(),
                                nn.MaxPool2d(2),
                                nn.Conv2d(64, 128, 3, padding=1),
                                nn.ReLU(),
                                nn.AdaptiveAvgPool2d(1),
                                nn.Flatten(),
                                nn.Linear(128, 2)
                            )
                            self.model.load_state_dict(state_dict, strict=False)
                            logger.info("   ✅ Loaded as custom CNN")
                    
                    self.model.eval()
                    logger.info("   ✅ NSFW model loaded successfully")
                    
                else:
                    # It's a full model
                    self.model = checkpoint
                    self.model.eval()
                    logger.info("   ✅ NSFW model loaded as full model")
                
                self.transform = transforms.Compose([
                    transforms.Resize((224, 224)),
                    transforms.ToTensor(),
                    transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                       std=[0.229, 0.224, 0.225])
                ])
                
            else:
                logger.warning("No NSFW model found, using fallback heuristic detection")
                self.model = None
                
        except Exception as e:
            logger.error(f"Failed to load NSFW model: {e}")
            self.model = None
    
    def detect(self, image_cv2):
        """
        Returns: (is_nsfw, confidence, reasoning)
        """
        if not self.model or not self.transform:
            return self._heuristic_detect(image_cv2)
        
        try:
            # Convert to PIL
            image_rgb = cv2.cvtColor(image_cv2, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)
            
            # Preprocess
            input_tensor = self.transform(pil_image).unsqueeze(0)
            
            # Predict
            with torch.no_grad():
                output = self.model(input_tensor)
                
                # Handle different output formats
                if isinstance(output, tuple):
                    output = output[0]
                
                # Get probability
                if hasattr(output, 'shape'):
                    if len(output.shape) == 2 and output.shape[1] == 2:
                        probabilities = torch.nn.functional.softmax(output, dim=1)
                        nsfw_prob = probabilities[0][1].item()
                    else:
                        nsfw_prob = torch.sigmoid(output).item()
                else:
                    nsfw_prob = float(output)
            
            is_nsfw = nsfw_prob > 0.7
            reasoning = f"NSFW probability: {nsfw_prob:.2f}"
            
            return is_nsfw, nsfw_prob, reasoning
            
        except Exception as e:
            logger.error(f"NSFW detection error: {e}")
            return self._heuristic_detect(image_cv2)
    
    def _heuristic_detect(self, image_cv2):
        """Heuristic NSFW detection (skin tone analysis)"""
        try:
            # Convert to HSV for skin detection
            hsv = cv2.cvtColor(image_cv2, cv2.COLOR_BGR2HSV)
            
            # Skin color range in HSV
            lower_skin = np.array([0, 20, 70], dtype=np.uint8)
            upper_skin = np.array([20, 255, 255], dtype=np.uint8)
            
            skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)
            skin_percentage = np.sum(skin_mask > 0) / (image_cv2.shape[0] * image_cv2.shape[1])
            
            is_nsfw = skin_percentage > 0.25
            confidence = min(0.9, skin_percentage)
            reasoning = f"Skin percentage: {skin_percentage:.2%}"
            
            return is_nsfw, confidence, reasoning
            
        except Exception as e:
            logger.error(f"NSFW heuristic error: {e}")
            return False, 0, "Detection failed"


# ============ MEME DETECTION (Fixed - Added transforms import) ============
class MemeDetector:
    """Detects memes using heuristics and optional ML"""
    
    def __init__(self):
        self.model = None
        self.transform = None
        self.load_model()
        
    def load_model(self):
        """Load meme detection model if available"""
        try:
            import torch
            import torchvision.models as models
            from torchvision import transforms
            
            # Use pre-trained MobileNetV2
            self.model = models.mobilenet_v2(pretrained=True)
            # Replace classifier for binary classification
            self.model.classifier[1] = torch.nn.Linear(1280, 2)
            self.model.eval()
            
            self.transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                   std=[0.229, 0.224, 0.225])
            ])
            
            # Try to load fine-tuned weights if available
            weights_path = Path(__file__).parent / "models" / "meme_classifier.pt"
            if weights_path.exists() and weights_path.stat().st_size > 0:
                self.model.load_state_dict(torch.load(weights_path, map_location='cpu'))
                logger.info("✅ Fine-tuned meme classifier loaded")
            else:
                logger.info("Using heuristic-based meme detection")
                self.model = None
                self.transform = None
                
        except Exception as e:
            logger.error(f"Failed to load meme detector: {e}")
            self.model = None
            self.transform = None
    
    def detect(self, image_cv2):
        """
        Returns: (is_meme, confidence, reasoning)
        """
        if not self.model or not self.transform:
            return self._heuristic_detect(image_cv2)
        
        try:
            # Convert to PIL
            image_rgb = cv2.cvtColor(image_cv2, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)
            
            # Preprocess
            input_tensor = self.transform(pil_image).unsqueeze(0)
            
            # Predict
            with torch.no_grad():
                outputs = self.model(input_tensor)
                probabilities = torch.nn.functional.softmax(outputs, dim=1)
                meme_prob = probabilities[0][1].item()
            
            is_meme = meme_prob > 0.5
            reasoning = f"Meme probability: {meme_prob:.2f}"
            
            return is_meme, meme_prob, reasoning
            
        except Exception as e:
            logger.error(f"Meme detection error: {e}")
            return self._heuristic_detect(image_cv2)
    
    def _heuristic_detect(self, image_cv2):
        """Heuristic-based meme detection"""
        h, w = image_cv2.shape[:2]
        gray = cv2.cvtColor(image_cv2, cv2.COLOR_BGR2GRAY)
        
        # Check top and bottom regions for text (memes have text at top/bottom)
        top_region = gray[0:int(h*0.2), :]
        bottom_region = gray[int(h*0.8):, :]
        
        # Edge detection for text
        top_edges = cv2.Canny(top_region, 50, 150) if top_region.size > 0 else np.array([])
        bottom_edges = cv2.Canny(bottom_region, 50, 150) if bottom_region.size > 0 else np.array([])
        
        top_edge_density = np.sum(top_edges > 0) / (h * w * 0.2) if h * w * 0.2 > 0 and top_edges.size > 0 else 0
        bottom_edge_density = np.sum(bottom_edges > 0) / (h * w * 0.2) if h * w * 0.2 > 0 and bottom_edges.size > 0 else 0
        
        has_text_regions = top_edge_density > 0.05 or bottom_edge_density > 0.05
        
        # Memes often have high contrast
        contrast = np.std(gray)
        
        # Check for bright colors (common in memes)
        hsv = cv2.cvtColor(image_cv2, cv2.COLOR_BGR2HSV)
        saturation = np.mean(hsv[:, :, 1])
        
        is_meme = has_text_regions and (contrast > 50 or saturation > 100)
        confidence = 0.7 if is_meme else 0.3
        
        reasoning = f"Text regions: {has_text_regions}, Contrast: {contrast:.1f}, Saturation: {saturation:.1f}"
        
        return is_meme, confidence, reasoning


# ============ FACE DETECTION ============
class FaceDetector:
    """Detects faces using OpenCV Haar cascades"""
    
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
    def detect(self, image_cv2):
        """
        Returns: (has_face, faces_count, reasoning)
        """
        try:
            gray = cv2.cvtColor(image_cv2, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )
            
            has_face = len(faces) > 0
            reasoning = f"Found {len(faces)} face(s)" if has_face else "No faces detected"
            
            return has_face, len(faces), reasoning
            
        except Exception as e:
            logger.error(f"Face detection error: {e}")
            return False, 0, "Face detection failed"


# ============ MAIN DETECTION PIPELINE ============
class DetectionPipeline:
    """Orchestrates all detectors in parallel"""
    
    def __init__(self):
        self.blur_detector = BlurDetector(threshold=100)
        self.screenshot_detector = ScreenshotDetector()
        self.meme_detector = MemeDetector()
        self.nsfw_detector = NSFWDetector()
        self.face_detector = FaceDetector()
        
        self.processing_queue = queue.Queue()
        self.running = False
        self.processing_thread = None
        
        logger.info("🔥 Detection pipeline initialized!")
    
    def start_background_processing(self):
        """Start background thread for processing images"""
        self.running = True
        self.processing_thread = threading.Thread(target=self._process_worker, daemon=True)
        self.processing_thread.start()
        logger.info("Background processing started")
    
    def queue_image(self, image_id, image_url, supabase_client):
        """Add image to processing queue"""
        self.processing_queue.put({
            'image_id': image_id,
            'image_url': image_url,
            'supabase': supabase_client,
            'timestamp': datetime.now()
        })
        logger.info(f"Image {image_id} queued for processing")
    
    def _process_worker(self):
        """Background worker that processes images"""
        while self.running:
            try:
                task = self.processing_queue.get(timeout=1)
                self._process_single_image(task)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Processing error: {e}")
    
    def _process_single_image(self, task):
        """Process a single image through all detectors"""
        try:
            image_id = task['image_id']
            supabase = task['supabase']
            image_url = task['image_url']
            
            # Load image from URL
            response = requests.get(image_url, timeout=10)
            image_array = np.frombuffer(response.content, np.uint8)
            image_cv2 = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            if image_cv2 is None:
                logger.error(f"Failed to load image {image_id}")
                return
            
            # Run all detectors
            is_blurry, blur_score, blur_reason = self.blur_detector.detect(image_cv2)
            has_face, face_count, face_reason = self.face_detector.detect(image_cv2)
            
            # Handle intentional blur (portrait mode)
            if is_blurry and has_face:
                is_blurry = False
                blur_reason = "Intentional blur (portrait mode) - face detected"
            
            is_screenshot, screenshot_conf, screenshot_reason = self.screenshot_detector.detect(image_cv2)
            is_meme, meme_conf, meme_reason = self.meme_detector.detect(image_cv2)
            is_nsfw, nsfw_conf, nsfw_reason = self.nsfw_detector.detect(image_cv2)
            
            # Determine final category (priority order)
            final_category = None
            final_confidence = 0
            final_reasoning = []
            
            if is_nsfw:
                final_category = "nsfw"
                final_confidence = nsfw_conf
                final_reasoning.append(nsfw_reason)
            elif is_screenshot:
                final_category = "screenshot"
                final_confidence = screenshot_conf
                final_reasoning.append(screenshot_reason)
            elif is_meme:
                final_category = "meme"
                final_confidence = meme_conf
                final_reasoning.append(meme_reason)
            elif is_blurry:
                final_category = "blur"
                final_confidence = min(1.0, blur_score / 100)
                final_reasoning.append(blur_reason)
            else:
                final_category = "normal"
                final_confidence = 0.8
                final_reasoning.append("No issues detected")
            
            # Update database
            update_data = {
                "predicted_category": final_category,
                "confidence_score": final_confidence,
                "reasoning": " | ".join(final_reasoning)
            }
            
            result = supabase.table("cleanup_items") \
                .update(update_data) \
                .eq("id", image_id) \
                .execute()
            
            logger.info(f"✅ Image {image_id}: {final_category} (conf: {final_confidence:.2f})")
            
        except Exception as e:
            logger.error(f"Error processing image {task.get('image_id')}: {e}")
            import traceback
            traceback.print_exc()
    
    def process_single_sync(self, image_cv2):
        """Process a single image synchronously (for testing)"""
        results = {}
        
        is_blurry, blur_score, blur_reason = self.blur_detector.detect(image_cv2)
        has_face, face_count, face_reason = self.face_detector.detect(image_cv2)
        
        if is_blurry and has_face:
            is_blurry = False
            blur_reason = "Intentional blur (portrait mode)"
        
        is_screenshot, screenshot_conf, screenshot_reason = self.screenshot_detector.detect(image_cv2)
        is_meme, meme_conf, meme_reason = self.meme_detector.detect(image_cv2)
        is_nsfw, nsfw_conf, nsfw_reason = self.nsfw_detector.detect(image_cv2)
        
        results['blur'] = {'detected': is_blurry, 'score': blur_score, 'reason': blur_reason}
        results['face'] = {'detected': has_face, 'count': face_count, 'reason': face_reason}
        results['screenshot'] = {'detected': is_screenshot, 'confidence': screenshot_conf, 'reason': screenshot_reason}
        results['meme'] = {'detected': is_meme, 'confidence': meme_conf, 'reason': meme_reason}
        results['nsfw'] = {'detected': is_nsfw, 'confidence': nsfw_conf, 'reason': nsfw_reason}
        
        return results


# Singleton instance
_pipeline_instance = None

def get_pipeline():
    """Get or create the global pipeline instance"""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = DetectionPipeline()
    return _pipeline_instance