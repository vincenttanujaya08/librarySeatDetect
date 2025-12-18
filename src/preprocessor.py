"""
Image Preprocessor
Preprocessing frame sebelum masuk ke YOLO detector
Includes: Brightness, Contrast, Histogram Eq, CLAHE, Denoising, Sharpening
"""

import cv2
import numpy as np
from src.config import *


class ImagePreprocessor:
    """
    Preprocessor untuk frame sebelum masuk YOLO
    Features:
    - Basic: Brightness, Contrast
    - Histogram: Histogram Equalization, CLAHE
    - Quality: Denoising, Sharpening
    """
    
    def __init__(self):
        # Basic adjustments
        self.brightness = PREPROCESSING_BRIGHTNESS
        self.contrast = PREPROCESSING_CONTRAST
        
        # Histogram equalization
        self.hist_eq_enabled = PREPROCESSING_HIST_EQ
        self.clahe_enabled = PREPROCESSING_CLAHE
        self.clahe_clip_limit = CLAHE_CLIP_LIMIT
        self.clahe_grid_size = CLAHE_GRID_SIZE
        
        # Quality improvements
        self.denoise_enabled = PREPROCESSING_DENOISE
        self.denoise_strength = DENOISE_STRENGTH
        self.sharpen_enabled = PREPROCESSING_SHARPEN
        self.sharpen_strength = SHARPEN_STRENGTH
        
        # Create CLAHE object (reuse untuk performa)
        if self.clahe_enabled:
            self.clahe_obj = cv2.createCLAHE(
                clipLimit=self.clahe_clip_limit,
                tileGridSize=self.clahe_grid_size
            )
    
    def adjust_brightness_contrast(self, image, brightness=1.0, contrast=1.0):
        """
        Adjust brightness and contrast
        
        Args:
            image: Input image (BGR)
            brightness: 1.0 = normal, >1.0 = brighter, <1.0 = darker
            contrast: 1.0 = normal, >1.0 = more contrast
        
        Returns:
            Adjusted image
        """
        if brightness == 1.0 and contrast == 1.0:
            return image
        
        # Convert to float untuk perhitungan
        img_float = image.astype(np.float32)
        
        # Apply brightness
        img_float = img_float * brightness
        
        # Apply contrast
        if contrast != 1.0:
            # Contrast around mean value
            mean = np.mean(img_float)
            img_float = mean + contrast * (img_float - mean)
        
        # Clip and convert back to uint8
        img_float = np.clip(img_float, 0, 255)
        return img_float.astype(np.uint8)
    
    def histogram_equalization(self, image):
        """
        Apply histogram equalization to improve contrast
        Works globally on entire image
        
        Args:
            image: Input image (BGR)
        
        Returns:
            Equalized image
        
        Note:
            Good for uniformly low contrast images.
            Can over-enhance in some cases.
            Consider using CLAHE instead for better results.
        """
        # Convert BGR to YUV
        yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
        
        # Equalize Y channel (luminance only)
        yuv[:, :, 0] = cv2.equalizeHist(yuv[:, :, 0])
        
        # Convert back to BGR
        return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
    
    def clahe(self, image):
        """
        Contrast Limited Adaptive Histogram Equalization
        Locally adaptive - better than regular histogram eq
        
        Args:
            image: Input image (BGR)
        
        Returns:
            CLAHE enhanced image
        
        Note:
            RECOMMENDED over histogram_equalization.
            Good for images with varying lighting conditions.
            Prevents over-enhancement by clipping histogram.
        """
        # Convert BGR to LAB color space
        # LAB separates luminance (L) from color (A, B)
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        
        # Apply CLAHE to L channel only (luminance)
        lab[:, :, 0] = self.clahe_obj.apply(lab[:, :, 0])
        
        # Convert back to BGR
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    def denoise(self, image, strength=10):
        """
        Remove noise using Non-local Means Denoising
        
        Args:
            image: Input image (BGR)
            strength: 3-30, higher = more denoising (tapi lebih lambat)
        
        Returns:
            Denoised image
        
        Warning:
            This is SLOW! Only use if really needed.
            Can significantly impact FPS.
        """
        return cv2.fastNlMeansDenoisingColored(image, None, strength, strength, 7, 21)
    
    def sharpen(self, image, strength=1.0):
        """
        Sharpen image using unsharp mask
        
        Args:
            image: Input image (BGR)
            strength: 0.5-2.0, higher = more sharpening
        
        Returns:
            Sharpened image
        
        Note:
            Good for slightly blurry images.
            Don't use with noisy images (will enhance noise).
        """
        # Gaussian blur
        blurred = cv2.GaussianBlur(image, (0, 0), 3)
        
        # Unsharp mask: original + (original - blurred) * strength
        sharpened = cv2.addWeighted(image, 1.0 + strength, blurred, -strength, 0)
        
        return sharpened
    
    def process(self, image):
        """
        Apply all preprocessing steps in order
        
        Processing order:
        1. Histogram Equalization / CLAHE (improve contrast)
        2. Brightness & Contrast (manual adjustment)
        3. Denoising (remove noise)
        4. Sharpening (enhance edges)
        
        Args:
            image: Input image (BGR)
        
        Returns:
            Processed image
        """
        if not PREPROCESSING_ENABLED:
            return image
        
        processed = image.copy()
        
        # Step 1: Histogram processing (mutually exclusive)
        if self.hist_eq_enabled:
            processed = self.histogram_equalization(processed)
        elif self.clahe_enabled:
            processed = self.clahe(processed)
        
        # Step 2: Brightness & Contrast (after histogram)
        if self.brightness != 1.0 or self.contrast != 1.0:
            processed = self.adjust_brightness_contrast(
                processed, 
                self.brightness, 
                self.contrast
            )
        
        # Step 3: Denoising (WARNING: SLOW)
        if self.denoise_enabled:
            processed = self.denoise(processed, self.denoise_strength)
        
        # Step 4: Sharpening (last step)
        if self.sharpen_enabled:
            processed = self.sharpen(processed, self.sharpen_strength)
        
        return processed
    
    def update_settings(self, brightness=None, contrast=None, 
                       hist_eq=None, clahe=None,
                       denoise=None, sharpen=None):
        """
        Update preprocessing settings on the fly
        
        Args:
            brightness: New brightness value
            contrast: New contrast value
            hist_eq: Enable/disable histogram equalization
            clahe: Enable/disable CLAHE
            denoise: Enable/disable denoising
            sharpen: Enable/disable sharpening
        """
        if brightness is not None:
            self.brightness = brightness
        if contrast is not None:
            self.contrast = contrast
        if hist_eq is not None:
            self.hist_eq_enabled = hist_eq
        if clahe is not None:
            self.clahe_enabled = clahe
            # Recreate CLAHE object if enabled
            if clahe:
                self.clahe_obj = cv2.createCLAHE(
                    clipLimit=self.clahe_clip_limit,
                    tileGridSize=self.clahe_grid_size
                )
        if denoise is not None:
            self.denoise_enabled = denoise
        if sharpen is not None:
            self.sharpen_enabled = sharpen