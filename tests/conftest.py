"""Sets up the testing environment for pipeline tests."""
import sys
from pathlib import Path

# Add pipeline directory to path so tests can import pipeline modules
pipeline_path = Path(__file__).parent.parent / 'pipeline'
sys.path.insert(0, str(pipeline_path))
