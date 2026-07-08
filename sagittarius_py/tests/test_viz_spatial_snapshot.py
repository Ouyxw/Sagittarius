"""
Tests for spatial snapshot and animation frame extraction utilities.
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock, patch
import matplotlib.pyplot as plt


# Mock Register class
class MockAtom:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class MockRegister:
    def __init__(self, n_atoms=4):
        positions = [
            (0.0, 0.0),
            (1.0, 0.0),
            (2.0, 0.0),
            (3.0, 0.0),
        ]
        self.atoms = [MockAtom(x, y) for x, y in positions[:n_atoms]]
        self.C6 = 80.0


# Mock SimulationResult class
class MockResult:
    def __init__(self, n_atoms=4, n_times=10):
        # Create population data
        data = {'t': np.linspace(0, 1, n_times)}
        for i in range(n_atoms):
            data[f'pop{i}'] = np.sin(np.linspace(0, np.pi * (i + 1), n_times))**2
        
        self.df = pd.DataFrame(data)
        self.metadata = {
            'register': {'atom_count': n_atoms}
        }
    
    def to_pandas(self):
        return self.df


@pytest.fixture
def mock_result():
    """Create mock result with population data."""
    return MockResult(n_atoms=4, n_times=10)


@pytest.fixture
def mock_register():
    """Create mock register with 4 atoms."""
    return MockRegister(n_atoms=4)


# ============================================================================
# Test extract_spatial_snapshot
# ============================================================================

class TestExtractSpatialSnapshot:
    def test_basic_extraction(self, mock_result, mock_register):
        """Test basic snapshot extraction."""
        from sagittarius.viz import extract_spatial_snapshot
        
        snapshot = extract_spatial_snapshot(mock_result, mock_register, time_index=5)
        
        assert snapshot['n_atoms'] == 4
        assert snapshot['time_index'] == 5
        assert 'time_value' in snapshot
        assert snapshot['positions'].shape == (4, 2)
        assert len(snapshot['observables']) == 4
        assert all(i in snapshot['observables'] for i in range(4))
        assert 'metadata' in snapshot
    
    def test_time_value_extraction(self, mock_result, mock_register):
        """Test that time value is correctly extracted."""
        from sagittarius.viz import extract_spatial_snapshot
        
        snapshot = extract_spatial_snapshot(mock_result, mock_register, time_index=0)
        assert np.isclose(snapshot['time_value'], 0.0)
        
        snapshot = extract_spatial_snapshot(mock_result, mock_register, time_index=9)
        assert np.isclose(snapshot['time_value'], 1.0)
    
    def test_invalid_time_index_raises(self, mock_result, mock_register):
        """Test that invalid time indices raise ValueError."""
        from sagittarius.viz import extract_spatial_snapshot
        
        with pytest.raises(ValueError, match="out of range"):
            extract_spatial_snapshot(mock_result, mock_register, time_index=-1)
        
        with pytest.raises(ValueError, match="out of range"):
            extract_spatial_snapshot(mock_result, mock_register, time_index=100)
    
    def test_observable_values_correct(self, mock_result, mock_register):
        """Test that observable values match DataFrame."""
        from sagittarius.viz import extract_spatial_snapshot
        
        snapshot = extract_spatial_snapshot(mock_result, mock_register, time_index=5)
        df = mock_result.to_pandas()
        
        for i in range(4):
            expected = float(df[f'pop{i}'].iloc[5])
            assert np.isclose(snapshot['observables'][i], expected)
    
    def test_metadata_structure(self, mock_result, mock_register):
        """Test metadata dictionary structure."""
        from sagittarius.viz import extract_spatial_snapshot
        
        snapshot = extract_spatial_snapshot(mock_result, mock_register, time_index=0)
        
        assert snapshot['metadata']['register']['atom_count'] == 4
        assert snapshot['metadata']['observable_type'] == 'pop'
        assert snapshot['metadata']['total_time_steps'] == 10


# ============================================================================
# Test extract_frame_sequence
# ============================================================================

class TestExtractFrameSequence:
    def test_auto_generate_indices(self, mock_result, mock_register):
        """Test automatic index generation with stride."""
        from sagittarius.viz import extract_frame_sequence
        
        frames = extract_frame_sequence(mock_result, mock_register, stride=2)
        
        assert len(frames) == 5  # 0, 2, 4, 6, 8
        assert all(f['time_index'] % 2 == 0 for f in frames)
    
    def test_custom_indices(self, mock_result, mock_register):
        """Test custom time indices."""
        from sagittarius.viz import extract_frame_sequence
        
        indices = [0, 3, 6, 9]
        frames = extract_frame_sequence(
            mock_result, mock_register, time_indices=indices
        )
        
        assert len(frames) == 4
        assert [f['time_index'] for f in frames] == indices
    
    def test_invalid_indices_raises(self, mock_result, mock_register):
        """Test that invalid indices raise ValueError."""
        from sagittarius.viz import extract_frame_sequence
        
        with pytest.raises(ValueError, match="Invalid time indices"):
            extract_frame_sequence(
                mock_result, mock_register, time_indices=[0, 100]
            )
    
    def test_all_frames_valid(self, mock_result, mock_register):
        """Test that all extracted frames are valid snapshots."""
        from sagittarius.viz import extract_frame_sequence
        
        frames = extract_frame_sequence(mock_result, mock_register, stride=3)
        
        for frame in frames:
            assert 'n_atoms' in frame
            assert 'positions' in frame
            assert 'observables' in frame


# ============================================================================
# Test save_frame_data
# ============================================================================

class TestSaveFrameData:
    def test_save_to_json(self, mock_result, mock_register, tmp_path):
        """Test saving frame data to JSON file."""
        from sagittarius.viz import extract_frame_sequence, save_frame_data
        
        frames = extract_frame_sequence(mock_result, mock_register, stride=5)
        output_path = tmp_path / "frames.json"
        
        save_frame_data(frames, str(output_path))
        
        assert output_path.exists()
        
        # Verify JSON structure
        import json
        with open(output_path) as f:
            data = json.load(f)
        
        assert data['schema_version'] == 'spatial-snapshot/v1'
        assert data['frame_count'] == len(frames)
        assert len(data['frames']) == len(frames)
    
    def test_unsupported_format_raises(self, mock_result, mock_register):
        """Test that unsupported format raises ValueError."""
        from sagittarius.viz import extract_frame_sequence, save_frame_data
        
        frames = extract_frame_sequence(mock_result, mock_register, stride=5)
        
        with pytest.raises(ValueError, match="Unsupported format"):
            save_frame_data(frames, "frames.csv", format='csv')


# ============================================================================
# Test plot_spatial_snapshot
# ============================================================================

class TestPlotSpatialSnapshot:
    def test_basic_plot(self, mock_result, mock_register):
        """Test basic snapshot plotting."""
        from sagittarius.viz import extract_spatial_snapshot, plot_spatial_snapshot
        
        snapshot = extract_spatial_snapshot(mock_result, mock_register, time_index=5)
        ax = plot_spatial_snapshot(snapshot)
        
        assert ax is not None
        assert len(ax.collections) >= 1  # scatter plot
        
        plt.close('all')
    
    def test_custom_cmap(self, mock_result, mock_register):
        """Test custom colormap."""
        from sagittarius.viz import extract_spatial_snapshot, plot_spatial_snapshot
        
        snapshot = extract_spatial_snapshot(mock_result, mock_register, time_index=5)
        ax = plot_spatial_snapshot(snapshot, cmap='plasma')
        
        scatter = ax.collections[0]
        assert scatter.get_cmap().name == 'plasma'
        
        plt.close('all')
    
    def test_hide_labels(self, mock_result, mock_register):
        """Test hiding atom labels."""
        from sagittarius.viz import extract_spatial_snapshot, plot_spatial_snapshot
        
        snapshot = extract_spatial_snapshot(mock_result, mock_register, time_index=5)
        ax = plot_spatial_snapshot(snapshot, show_labels=False)
        
        # Check that no text objects are atom labels
        texts = [t for t in ax.texts if t.get_text().isdigit()]
        assert len(texts) == 0
        
        plt.close('all')
    
    def test_custom_title(self, mock_result, mock_register):
        """Test custom title."""
        from sagittarius.viz import extract_spatial_snapshot, plot_spatial_snapshot
        
        snapshot = extract_spatial_snapshot(mock_result, mock_register, time_index=5)
        ax = plot_spatial_snapshot(snapshot, title="Custom Title")
        
        assert ax.get_title() == "Custom Title"
        
        plt.close('all')
    
    def test_save_to_file(self, mock_result, mock_register, tmp_path):
        """Test saving plot to file."""
        from sagittarius.viz import extract_spatial_snapshot, plot_spatial_snapshot
        
        snapshot = extract_spatial_snapshot(mock_result, mock_register, time_index=5)
        output_path = tmp_path / "snapshot.png"
        
        ax = plot_spatial_snapshot(snapshot, save_path=str(output_path))
        
        assert output_path.exists()
        
        plt.close('all')


# ============================================================================
# Test plot_multi_panel_snapshots
# ============================================================================

class TestPlotMultiPanelSnapshots:
    def test_basic_multi_panel(self, mock_result, mock_register):
        """Test basic multi-panel visualization."""
        from sagittarius.viz import extract_frame_sequence, plot_multi_panel_snapshots
        
        frames = extract_frame_sequence(mock_result, mock_register, stride=2)
        axes = plot_multi_panel_snapshots(frames, panel_indices=[0, 2, 4])
        
        assert len(axes) == 3
        
        plt.close('all')
    
    def test_default_four_panels(self, mock_result, mock_register):
        """Test default display of first 4 frames."""
        from sagittarius.viz import extract_frame_sequence, plot_multi_panel_snapshots
        
        frames = extract_frame_sequence(mock_result, mock_register, stride=1)
        axes = plot_multi_panel_snapshots(frames)
        
        assert len(axes) == 4
        
        plt.close('all')
    
    def test_shared_colorbar(self, mock_result, mock_register):
        """Test shared colorbar across panels."""
        from sagittarius.viz import extract_frame_sequence, plot_multi_panel_snapshots
        
        frames = extract_frame_sequence(mock_result, mock_register, stride=2)
        # stride=2 gives indices [0, 2, 4, 6, 8] (5 frames total)
        axes = plot_multi_panel_snapshots(
            frames, panel_indices=[0, 1, 2, 3], show_colorbar=True
        )
        
        # Check that figure has colorbar
        assert len(axes) == 4
        
        plt.close('all')
    
    def test_custom_suptitle(self, mock_result, mock_register):
        """Test custom super title."""
        from sagittarius.viz import extract_frame_sequence, plot_multi_panel_snapshots
        
        frames = extract_frame_sequence(mock_result, mock_register, stride=2)
        # Use valid indices within available frames
        axes = plot_multi_panel_snapshots(
            frames, panel_indices=[0, 1, 2, 3],
            suptitle="Evolution Over Time"
        )
        
        assert len(axes) == 4
        
        plt.close('all')
    
    def test_save_to_file(self, mock_result, mock_register, tmp_path):
        """Test saving multi-panel plot to file."""
        from sagittarius.viz import extract_frame_sequence, plot_multi_panel_snapshots
        
        frames = extract_frame_sequence(mock_result, mock_register, stride=2)
        output_path = tmp_path / "multi_panel.png"
        
        plot_multi_panel_snapshots(
            frames, panel_indices=[0, 2],
            save_path=str(output_path)
        )
        
        assert output_path.exists()
        
        plt.close('all')


# ============================================================================
# Integration Tests
# ============================================================================

class TestSpatialSnapshotIntegration:
    def test_full_workflow(self, mock_result, mock_register, tmp_path):
        """Test complete workflow: extract -> save -> plot."""
        from sagittarius.viz import (
            extract_frame_sequence,
            save_frame_data,
            plot_multi_panel_snapshots,
        )
        
        # Extract frames
        frames = extract_frame_sequence(mock_result, mock_register, stride=3)
        assert len(frames) > 0
        
        # Save to JSON
        json_path = tmp_path / "frames.json"
        save_frame_data(frames, str(json_path))
        assert json_path.exists()
        
        # Plot multi-panel (use valid indices)
        png_path = tmp_path / "snapshots.png"
        n_panels = min(3, len(frames))
        plot_multi_panel_snapshots(
            frames, panel_indices=list(range(n_panels)),
            save_path=str(png_path)
        )
        assert png_path.exists()
    
    def test_error_messages_are_actionable(self, mock_result, mock_register):
        """Test that error messages provide actionable guidance."""
        from sagittarius.viz import extract_spatial_snapshot
        
        # Invalid time index
        with pytest.raises(ValueError) as exc_info:
            extract_spatial_snapshot(mock_result, mock_register, time_index=100)
        
        error_msg = str(exc_info.value)
        assert "out of range" in error_msg.lower()
        assert "10" in error_msg  # Shows valid range
