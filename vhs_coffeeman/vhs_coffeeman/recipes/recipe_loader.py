"""
recipe_loader.py - Recipe Management Module for VHS Coffeeman

This module provides recipe loading and management functionality for the VHS Coffeeman system.
It defines interfaces and basic infrastructure for recipe management that can be extended
with specific recipe formats later.

Classes:
    RecipeLoader: Abstract interface for recipe loading
    BasicRecipeLoader: Simple implementation for basic recipe support
    Recipe: Generic recipe representation

The RecipeLoader interface handles:
    - Loading recipes by RFID tag ID
    - Caching and performance optimization
    - Error handling for missing or invalid recipes
    - Directory management for recipe files

Usage:
    from recipes.recipe_loader import BasicRecipeLoader
    
    loader = BasicRecipeLoader()
    recipe = loader.get_recipe_by_tag("12345678")
    if recipe:
        print(f"Found recipe: {recipe['name']}")
"""

import os
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from utils.logger import get_logger

logger = get_logger(__name__)


class RecipeLoader(ABC):
    """Abstract interface for recipe loading."""
    
    @abstractmethod
    def get_recipe_by_tag(self, tag_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a recipe by RFID tag ID.
        
        Args:
            tag_id: The RFID tag identifier
            
        Returns:
            Recipe dictionary or None if not found
        """
        pass
    
    @abstractmethod
    def list_available_tags(self) -> List[str]:
        """
        List all available RFID tag IDs.
        
        Returns:
            List of tag ID strings
        """
        pass
    
    @abstractmethod
    def reload_recipes(self):
        """Force reload of all recipes."""
        pass


class BasicRecipeLoader(RecipeLoader):
    """Basic implementation of recipe loading with file-based storage."""
    
    def __init__(self, recipes_directory: str = None):
        """
        Initialize the recipe loader.
        
        Args:
            recipes_directory: Directory containing recipe files
        """
        if recipes_directory is None:
            # Default to recipes directory relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            recipes_directory = os.path.join(current_dir, "data")
        
        self.recipes_directory = recipes_directory
        self.recipes_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_timestamp: float = 0
        self.cache_ttl: float = 300  # 5 minutes cache TTL
        
        logger.info(f"Recipe loader initialized with directory: {recipes_directory}")
        
        # Create recipes directory if it doesn't exist
        self._ensure_directory_exists()
        
        # Create default recipe if no recipes exist
        self._ensure_default_recipes()
    
    def _ensure_directory_exists(self):
        """Ensure the recipes directory exists."""
        if not os.path.exists(self.recipes_directory):
            try:
                os.makedirs(self.recipes_directory, exist_ok=True)
                logger.info(f"Created recipes directory: {self.recipes_directory}")
            except Exception as e:
                logger.error(f"Failed to create recipes directory: {e}")
    
    def _ensure_default_recipes(self):
        """Create default fallback recipes if none exist."""
        try:
            # Check if any recipe files exist
            if os.path.exists(self.recipes_directory):
                existing_files = [f for f in os.listdir(self.recipes_directory) if f.endswith('.json')]
                if existing_files:
                    logger.debug(f"Found {len(existing_files)} existing recipe files")
                    return
            
            # Create a default recipe file
            default_recipe = {
                "name": "Default Test Recipe",
                "tag_id": "DEFAULT",
                "description": "Fallback recipe for testing",
                "ingredients": [
                    {"pump": 0, "name": "Ingredient A", "amount": 1.0},
                    {"pump": 1, "name": "Ingredient B", "amount": 0.5}
                ]
            }
            
            default_file = os.path.join(self.recipes_directory, "default.json")
            with open(default_file, 'w') as f:
                json.dump(default_recipe, f, indent=2)
            
            logger.info("Created default recipe file")
            
        except Exception as e:
            logger.error(f"Error creating default recipes: {e}")
    
    def _load_recipe_from_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Load a recipe from a file.
        
        Args:
            file_path: Path to the recipe file
            
        Returns:
            Recipe dictionary or None if loading failed
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Basic validation - ensure required fields exist
            if not self._validate_recipe_data(data):
                logger.error(f"Recipe validation failed for {file_path}")
                return None
            
            logger.debug(f"Loaded recipe: {data.get('name', 'Unknown')} from {file_path}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading recipe from {file_path}: {e}")
            return None
    
    def _validate_recipe_data(self, data: Dict[str, Any]) -> bool:
        """
        Basic validation of recipe data.
        
        Args:
            data: Recipe data dictionary
            
        Returns:
            True if valid, False otherwise
        """
        # Check for required fields
        required_fields = ['name', 'tag_id', 'ingredients']
        for field in required_fields:
            if field not in data:
                logger.error(f"Recipe missing required field: {field}")
                return False
        
        # Check ingredients structure
        ingredients = data.get('ingredients', [])
        if not isinstance(ingredients, list) or len(ingredients) == 0:
            logger.error("Recipe has no ingredients or invalid ingredients format")
            return False
        
        # Basic ingredient validation
        for ing in ingredients:
            if not isinstance(ing, dict):
                logger.error("Invalid ingredient format")
                return False
            if 'pump' not in ing or 'amount' not in ing:
                logger.error("Ingredient missing pump or amount")
                return False
        
        return True
    
    def _refresh_cache(self):
        """Refresh the recipes cache from disk."""
        current_time = time.time()
        
        # Check if cache is still valid
        if (current_time - self.cache_timestamp) < self.cache_ttl and self.recipes_cache:
            return
        
        logger.debug("Refreshing recipes cache...")
        self.recipes_cache.clear()
        
        if not os.path.exists(self.recipes_directory):
            logger.warning(f"Recipes directory does not exist: {self.recipes_directory}")
            return
        
        # Load all JSON files in the recipes directory
        try:
            for filename in os.listdir(self.recipes_directory):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.recipes_directory, filename)
                    recipe = self._load_recipe_from_file(file_path)
                    
                    if recipe:
                        tag_id = recipe['tag_id']
                        self.recipes_cache[tag_id] = recipe
                        logger.debug(f"Cached recipe {recipe['name']} for tag {tag_id}")
            
            self.cache_timestamp = current_time
            logger.info(f"Loaded {len(self.recipes_cache)} recipes into cache")
            
        except Exception as e:
            logger.error(f"Error refreshing recipes cache: {e}")
    
    def get_recipe_by_tag(self, tag_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a recipe by RFID tag ID.
        
        Args:
            tag_id: The RFID tag identifier
            
        Returns:
            Recipe dictionary or None if not found
        """
        # Refresh cache if needed
        self._refresh_cache()
        
        recipe = self.recipes_cache.get(tag_id)
        if recipe:
            logger.info(f"Found recipe '{recipe['name']}' for tag {tag_id}")
            return recipe
        else:
            logger.warning(f"No recipe found for tag {tag_id}")
            
            # Try to return default recipe as fallback
            default_recipe = self.recipes_cache.get("DEFAULT")
            if default_recipe:
                logger.info("Using default recipe as fallback")
                # Create a copy and update the tag_id for this request
                fallback = default_recipe.copy()
                fallback['tag_id'] = tag_id
                fallback['name'] = f"Fallback Recipe ({tag_id})"
                return fallback
            
            return None
    
    def list_available_tags(self) -> List[str]:
        """
        List all available RFID tag IDs.
        
        Returns:
            List of tag ID strings
        """
        self._refresh_cache()
        return list(self.recipes_cache.keys())
    
    def reload_recipes(self):
        """Force reload of all recipes from disk."""
        logger.info("Force reloading recipes...")
        self.cache_timestamp = 0  # Force cache refresh
        self._refresh_cache()
    
    def get_all_recipes(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all loaded recipes.
        
        Returns:
            Dictionary mapping tag IDs to recipe dictionaries
        """
        self._refresh_cache()
        return self.recipes_cache.copy()
    
    def get_recipes_directory(self) -> str:
        """Get the recipes directory path."""
        return self.recipes_directory
    
    def create_test_recipe(self, tag_id: str, name: str) -> Dict[str, Any]:
        """
        Create a test recipe for development/testing.
        
        Args:
            tag_id: RFID tag ID
            name: Recipe name
            
        Returns:
            Recipe dictionary
        """
        return {
            "name": name,
            "tag_id": tag_id,
            "description": f"Test recipe for {name}",
            "ingredients": [
                {"pump": 0, "name": "Test Ingredient 1", "amount": 1.0},
                {"pump": 1, "name": "Test Ingredient 2", "amount": 0.5}
            ]
        }