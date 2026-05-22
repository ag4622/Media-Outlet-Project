"""Sets up the testing environment for pipeline tests."""
import sys
from pathlib import Path

# Add pipeline and dashboard directories to path so tests can import modules
pipeline_path = Path(__file__).parent.parent / 'pipeline'
dashboard_path = Path(__file__).parent.parent / 'dashboard'
sys.path.insert(0, str(pipeline_path))
sys.path.insert(0, str(dashboard_path))