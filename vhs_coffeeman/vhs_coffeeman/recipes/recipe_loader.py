"""
recipe_loader.py - Recipe Management Module for VHS Coffeeman

This module provides recipe loading and management functionality for the VHS Coffeeman system.
It implements a three-file JSON system for human-friendly recipe management.

Classes:
    RecipeLoader: New implementation using tapes.json, ingredients.json, and recipes.json
    BasicRecipeLoader: Legacy implementation (kept for compatibility)

The new RecipeLoader uses three separate JSON files:
    - tapes.json: Maps RFID tag IDs to movie names
    - ingredients.json: Maps ingredient names to pump numbers  
    - recipes.json: Maps movie names to ingredient recipes

Usage:
    from recipes.recipe_loader import RecipeLoader
    
    loader = RecipeLoader()
    recipe = loader.get_recipe_by_tag_id("12345678")
    if recipe:
        print(f"Recipe: {recipe}")  # [(pump_number, amount), ...]
"""

import os
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from utils.logger import setup_logger

logger = setup_logger(__name__)


class RecipeLoader:
    """
    Three-file JSON recipe management system.
    
    Uses separate JSON files for human-friendly recipe management:
    - tapes.json: Maps RFID tag IDs to movie names
    - ingredients.json: Maps ingredient names to pump numbers
    - recipes.json: Maps movie names to ingredient recipes
    """
    
    def __init__(self, tapes_file: str = "recipes/tapes.json", 
                 ingredients_file: str = "recipes/ingredients.json", 
                 recipes_file: str = "recipes/recipes.json"):
        """
        Initialize the recipe loader.
        
        Args:
            tapes_file: Path to tapes mapping file
            ingredients_file: Path to ingredients mapping file  
            recipes_file: Path to recipes file
        """
        # Convert relative paths to absolute paths based on this file's location
        if not os.path.isabs(tapes_file):
            # For relative paths, use the directory containing this recipe_loader.py file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.tapes_file = os.path.join(current_dir, tapes_file.replace("recipes/", ""))
        else:
            self.tapes_file = tapes_file
            
        if not os.path.isabs(ingredients_file):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.ingredients_file = os.path.join(current_dir, ingredients_file.replace("recipes/", ""))
        else:
            self.ingredients_file = ingredients_file
            
        if not os.path.isabs(recipes_file):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.recipes_file = os.path.join(current_dir, recipes_file.replace("recipes/", ""))
        else:
            self.recipes_file = recipes_file
        
        # Data storage
        self.tapes: Dict[str, str] = {}
        self.ingredients: Dict[str, int] = {}
        self.recipes: Dict[str, Dict[str, float]] = {}
        
        logger.info(f"RecipeLoader initialized with files:")
        logger.info(f"  Tapes: {self.tapes_file}")
        logger.info(f"  Ingredients: {self.ingredients_file}")
        logger.info(f"  Recipes: {self.recipes_file}")
        
        # Load all data
        self.reload_files()
    
    def _load_json_file(self, file_path: str, description: str) -> Dict[str, Any]:
        """
        Load a JSON file with error handling.
        
        Args:
            file_path: Path to the JSON file
            description: Description for logging
            
        Returns:
            Dictionary data or empty dict if file missing/invalid
        """
        try:
            if not os.path.exists(file_path):
                logger.warning(f"{description} file not found: {file_path}")
                return {}
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            logger.info(f"Loaded {description}: {len(data)} entries")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {description} file {file_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading {description} file {file_path}: {e}")
            return {}
    
    def reload_files(self):
        """Reload all JSON files."""
        logger.info("Reloading recipe files...")
        
        self.tapes = self._load_json_file(self.tapes_file, "tapes")
        self.ingredients = self._load_json_file(self.ingredients_file, "ingredients")
        self.recipes = self._load_json_file(self.recipes_file, "recipes")
        
        logger.info(f"Recipe system loaded: {len(self.tapes)} tapes, {len(self.ingredients)} ingredients, {len(self.recipes)} recipes")
    
    def get_recipe_by_tag_id(self, tag_id: str) -> Optional[List[Tuple[int, float]]]:
        """
        Main method: converts tag_id to final recipe format.
        
        Args:
            tag_id: RFID tag identifier
            
        Returns:
            List of (pump_number, amount) tuples or None if any step fails
        """
        try:
            logger.info(f"Looking up recipe for tag ID: {tag_id}")
            
            # Step 1: Get movie name from tag ID
            movie_name = self.get_movie_name(tag_id)
            if movie_name is None:
                logger.warning(f"No movie found for tag ID: {tag_id}")
                return None
            
            logger.info(f"Tag {tag_id} maps to movie: {movie_name}")
            
            # Step 2: Get recipe for movie
            if movie_name not in self.recipes:
                logger.warning(f"No recipe found for movie: {movie_name}")
                return None
            
            recipe_ingredients = self.recipes[movie_name].get('ingredients', {})
            if not recipe_ingredients:
                logger.warning(f"Recipe for {movie_name} has no ingredients")
                return None
            
            # Step 3: Validate recipe before translation
            is_valid, missing = self.validate_recipe(movie_name)
            if not is_valid:
                logger.error(f"Recipe for {movie_name} has missing ingredients: {missing}")
                return None
            
            # Step 4: Translate ingredients to pump numbers
            pump_list = []
            for ingredient_name, amount in recipe_ingredients.items():
                if ingredient_name in self.ingredients:
                    pump_number = self.ingredients[ingredient_name]
                    pump_list.append((pump_number, amount))
                    logger.debug(f"  {ingredient_name} -> pump {pump_number}, amount {amount}")
                else:
                    # This shouldn't happen due to validation, but safety check
                    logger.error(f"Ingredient {ingredient_name} not found in ingredients map")
                    return None
            
            logger.info(f"Recipe for {movie_name}: {len(pump_list)} ingredients")
            return pump_list
            
        except Exception as e:
            logger.error(f"Error getting recipe for tag {tag_id}: {e}")
            return None
    
    def get_movie_name(self, tag_id: str) -> Optional[str]:
        """
        Get movie name for a tag ID.
        
        Args:
            tag_id: RFID tag identifier
            
        Returns:
            Movie name string or None if tag not found
        """
        return self.tapes.get(tag_id)
    
    def validate_recipe(self, movie_name: str) -> Tuple[bool, List[str]]:
        """
        Check if all recipe ingredients exist in ingredients.json.
        
        Args:
            movie_name: Name of the movie to validate
            
        Returns:
            Tuple of (is_valid: bool, missing_ingredients: list)
        """
        if movie_name not in self.recipes:
            return False, [f"Recipe not found: {movie_name}"]
        
        recipe_ingredients = self.recipes[movie_name].get('ingredients', {})
        missing_ingredients = []
        
        for ingredient_name in recipe_ingredients.keys():
            if ingredient_name not in self.ingredients:
                missing_ingredients.append(ingredient_name)
        
        is_valid = len(missing_ingredients) == 0
        return is_valid, missing_ingredients
    
    def get_available_movies(self) -> List[str]:
        """
        Get list of movies that have both tape mapping and valid recipes.
        
        Returns:
            List of movie names
        """
        available_movies = []
        
        # Get all movies that have tape mappings
        mapped_movies = set(self.tapes.values())
        
        # Check which ones also have valid recipes
        for movie_name in mapped_movies:
            is_valid, _ = self.validate_recipe(movie_name)
            if is_valid:
                available_movies.append(movie_name)
        
        return sorted(available_movies)


class LegacyRecipeLoader(ABC):
    """Abstract interface for legacy recipe loading (for backward compatibility)."""
    
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


class BasicRecipeLoader(LegacyRecipeLoader):
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