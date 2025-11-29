import os
import json
from typing import Dict, List

class ModelsManager:
    """
    Manages loading and caching of AI/ML models.
    """
    def __init__(self, models_dir: str = "models"):
        self.models_dir = models_dir
        self.loaded_models = {}
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load model configuration."""
        config_path = os.path.join(self.models_dir, "model_config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            # Default config
            return {
                "landuse": {
                    "file": "landuse_segmentation.pt",
                    "input_size": [256, 256],
                    "description": "Land-use change detection"
                },
                "deforestation": {
                    "file": "deforestation_detector.pt",
                    "input_size": [256, 256],
                    "description": "Forest cover change detection"
                },
                "water": {
                    "file": "water_change_detector.pt",
                    "input_size": [256, 256],
                    "description": "Water body expansion/retraction"
                },
                "structures": {
                    "file": "structure_detector.pt",
                    "input_size": [256, 256],
                    "description": "New building/infrastructure detection"
                },
                "disaster": {
                    "file": "disaster_damage_detector.pt",
                    "input_size": [256, 256],
                    "description": "Disaster damage assessment"
                }
            }
    
    def get_available_models(self) -> List[Dict]:
        """Get list of available models."""
        return [
            {
                "type": model_type,
                "description": config["description"],
                "loaded": model_type in self.loaded_models
            }
            for model_type, config in self.config.items()
        ]
    
    def load_model(self, model_type: str):
        """
        Load a model. For MVP, this is a placeholder.
        In production, load actual PyTorch/TensorFlow models.
        """
        if model_type in self.loaded_models:
            return self.loaded_models[model_type]
        
        if model_type not in self.config:
            raise ValueError(f"Unknown model type: {model_type}")
        
        model_path = os.path.join(self.models_dir, self.config[model_type]["file"])
        
        # Placeholder: In production, load actual model
        # model = torch.load(model_path)
        # self.loaded_models[model_type] = model
        
        # For now, just mark as loaded
        self.loaded_models[model_type] = f"Placeholder for {model_type}"
        
        return self.loaded_models[model_type]
    
    def unload_model(self, model_type: str):
        """Unload a model to free memory."""
        if model_type in self.loaded_models:
            del self.loaded_models[model_type]

# Global instance
_models_manager = None

def get_models_manager() -> ModelsManager:
    """Get the global models manager instance."""
    global _models_manager
    if _models_manager is None:
        _models_manager = ModelsManager()
    return _models_manager
