"""Sets up the testing environment for pipeline tests."""
import sys
from pathlib import Path
import pandas as pd
import pytest

# Add pipeline, dashboard, and tabs directories to path so tests can import modules
pipeline_path = Path(__file__).parent.parent / 'pipeline'
dashboard_path = Path(__file__).parent.parent / 'dashboard'
tabs_path = Path(__file__).parent.parent / 'dashboard' / 'tabs'
sys.path.insert(0, str(pipeline_path))
sys.path.insert(0, str(dashboard_path))
sys.path.insert(0, str(tabs_path))


# Fixtures for test_dashboard.py
@pytest.fixture
def filter_data_sample_df():
    """Create sample trial data for filter_data tests."""
    return pd.DataFrame({
        'conditions': [
            ['cancer', 'diabetes'],
            ['asthma'],
            ['diabetes']
        ],
        'interventions': [
            ['drug'],
            ['surgery'],
            ['drug']
        ],
        'sponsors': [
            ['pharma_co'],
            ['hospital'],
            ['pharma_co']
        ],
        'trial_id': ['T1', 'T2', 'T3']
    })


@pytest.fixture
def filter_create_sample_data():
    """Create sample data for create_filters tests."""
    return (
        pd.DataFrame({
            'conditions': [['cancer'], ['diabetes']],
            'interventions': [['drug'], ['surgery']],
            'sponsors': [['pharma'], ['hospital']]
        }),
        ['cancer', 'diabetes'],
        ['drug', 'surgery'],
        ['pharma', 'hospital']
    )


# Fixtures for test_dashboard_tabs.py
@pytest.fixture
def sponsors_sample_df():
    """Create sample sponsor data for sponsor filter tests."""
    return pd.DataFrame({
        'Sponsors': ['Harvard University', 'Pfizer Inc', 'Johns Hopkins Medical Center'],
        'Trial Count': [10, 20, 15]
    })


@pytest.fixture
def interventions_sample_df():
    """Create sample intervention data for intervention filter tests."""
    return pd.DataFrame({
        'Interventions': ['Drug therapy', 'Surgical procedure', 'Dietary supplement'],
        'Trial Count': [50, 30, 20]
    })
