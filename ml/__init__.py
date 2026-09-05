"""
ML package for anti-poaching system.
Contains model training and prediction modules.
"""

from .features import extract_training_features
from .predict import PoachingPredictor

__all__ = ['extract_training_features', 'PoachingPredictor']