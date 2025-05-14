"""
recipe.py - Recipe Module for VHS Coffeeman

This module manages drink recipes for the VHS Coffeeman system.
It provides a class for storing and executing drink recipes.

Classes:
    Recipe: Stores and manages a drink recipe

The Recipe class is responsible for:
    - Storing a recipe ID and list of ingredients
    - Adding ingredients to the recipe
    - Validating the recipe format
    - Executing the recipe using the pump controller

Usage:
    from recipe import Recipe
    from pump_controller import PumpController
    
    # Initialize the pump controller
    pump_controller = PumpController()
    
    # Create a new recipe
    recipe = Recipe(id="12345")
    
    # Add ingredients to the recipe
    recipe.add_ingredient(pump_index=0, amount_oz=1.5)
    recipe.add_ingredient(pump_index=3, amount_oz=1.1)
    
    # Execute the recipe
    recipe.execute(pump_controller)

The Recipe class handles validation of ingredient specifications, ensuring that
pump indices are valid and amounts are within reasonable ranges.

The execute method runs through each ingredient in sequence, using the pump controller
to dispense the specified amounts.

This module depends on:
    - config.py for validation constants
    - pump_controller.py for dispensing operations
"""

from config import constants

class Recipe:
    """Stores and manages a drink recipe."""
    
    def __init__(self, id):
        """
        Initialize a new recipe.
        
        Args:
            id: A unique identifier for the recipe.
        """
        self.id = id
        self.ingredients = []
    
    def add_ingredient(self, pump_index, amount_oz):
        """
        Add an ingredient to the recipe.
        
        Args:
            pump_index: The index of the pump to use for this ingredient.
            amount_oz: The amount to dispense in fluid ounces.
            
        Returns:
            bool: True if the ingredient was added successfully, False otherwise.
            
        Raises:
            ValueError: If the pump index or amount is invalid.
        """
        # Validate pump index
        if pump_index < 0 or pump_index >= constants.NUM_PUMPS:
            error_msg = f"Invalid pump index: {pump_index}. Must be between 0 and {constants.NUM_PUMPS - 1}"
            print(error_msg)
            raise ValueError(error_msg)
        
        # Validate amount
        if amount_oz < constants.MIN_PUMP_OZ or amount_oz > constants.MAX_PUMP_OZ:
            error_msg = f"Invalid amount: {amount_oz} oz. Must be between {constants.MIN_PUMP_OZ} and {constants.MAX_PUMP_OZ} oz"
            print(error_msg)
            raise ValueError(error_msg)
        
        # Add the ingredient to the recipe
        self.ingredients.append((pump_index, amount_oz))
        return True
    
    def add_ingredients(self, ingredients):
        """
        Add multiple ingredients to the recipe.
        
        Args:
            ingredients: A list of (pump_index, amount_oz) tuples.
            
        Returns:
            bool: True if all ingredients were added successfully, False otherwise.
        """
        try:
            for pump_index, amount_oz in ingredients:
                self.add_ingredient(pump_index, amount_oz)
            return True
        except Exception as e:
            print(f"Error adding ingredients: {e}")
            return False
    
    def execute(self, pump_controller):
        """
        Execute the recipe by dispensing each ingredient in sequence.
        
        Args:
            pump_controller: A PumpController instance to use for dispensing.
            
        Returns:
            bool: True if the recipe was executed successfully, False otherwise.
        """
        print(f"Executing recipe {self.id} with {len(self.ingredients)} ingredients")
        
        for index, (pump_index, amount_oz) in enumerate(self.ingredients):
            print(f"Dispensing ingredient {index + 1}/{len(self.ingredients)}: Pump {pump_index}, {amount_oz} oz")
            
            # Dispense the ingredient
            success = pump_controller.dispense(pump_index, amount_oz)
            
            # If dispensing failed, stop execution
            if not success:
                print(f"Failed to dispense ingredient {index + 1}")
                return False
        
        print(f"Recipe {self.id} executed successfully")
        return True
    
    def from_command(command):
        """
        Create a Recipe object from a parsed command.
        
        Args:
            command: A parsed command object with 'id' and 'ingredients' fields.
            
        Returns:
            Recipe: A Recipe object if created successfully, None otherwise.
        """
        try:
            # Create a new recipe with the specified ID
            recipe = Recipe(command.get('id'))
            
            # Add ingredients from the command
            ingredients = command.get('ingredients', [])
            if recipe.add_ingredients(ingredients):
                return recipe
            return None
            
        except Exception as e:
            print(f"Error creating recipe from command: {e}")
            return None