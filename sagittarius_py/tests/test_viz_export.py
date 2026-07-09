"""
Unit tests for chart export utilities.

Tests the export_figure and export_from_result functions, including:
- Multi-format export (PNG, SVG, PDF)
- Metadata generation and validation
- Provenance tracking
- Error handling
"""

import pytest
import json
import os
import tempfile
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

@pytest.fixture(autouse=True)
def cleanup_matplotlib_figures():
    """Automatically close all figures after each test to prevent memory warnings."""
    yield
    plt.close('all')


class TestExportFigure:
    """Test suite for export_figure function."""
    
    def test_basic_png_export(self):
        """Test basic PNG export with metadata."""
        from sagittarius.viz.export import export_figure
        
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 9])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_plot")
            paths = export_figure(fig, output_path, formats=['png'])
            
            assert 'png' in paths
            assert os.path.exists(paths['png'])
            assert paths['png'].endswith('.png')
        
        plt.close()
    
    def test_multi_format_export(self):
        """Test export to multiple formats."""
        from sagittarius.viz.export import export_figure
        
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 9])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_plot")
            paths = export_figure(fig, output_path, formats=['png', 'svg', 'pdf'])
            
            assert 'png' in paths
            assert 'svg' in paths
            assert 'pdf' in paths
            
            for fmt in ['png', 'svg', 'pdf']:
                assert os.path.exists(paths[fmt])
        
        plt.close()
    
    def test_metadata_json_generation(self):
        """Test that metadata JSON is generated correctly."""
        from sagittarius.viz.export import export_figure
        
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 9])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_plot")
            paths = export_figure(
                fig, 
                output_path, 
                formats=['png'],
                artifact_id='test_artifact_001',
                plot_function='test_plot_func',
                plot_params={'param1': 'value1'},
            )
            
            assert 'json' in paths
            assert os.path.exists(paths['json'])
            
            # Validate metadata content
            with open(paths['json'], 'r') as f:
                metadata = json.load(f)
            
            assert metadata['schema_version'] == 'chart-export/v1'
            assert metadata['provenance']['artifact_id'] == 'test_artifact_001'
            assert metadata['plotting']['function'] == 'test_plot_func'
            assert metadata['plotting']['parameters']['param1'] == 'value1'
            assert 'export_timestamp' in metadata
            assert 'disclaimer' in metadata
        
        plt.close()
    
    def test_invalid_format_raises_error(self):
        """Test that invalid format raises ValueError."""
        from sagittarius.viz.export import export_figure
        
        fig, ax = plt.subplots()
        
        with pytest.raises(ValueError, match="Invalid formats"):
            export_figure(fig, "test", formats=['invalid_fmt'])
        
        plt.close()
    
    def test_custom_dpi_for_png(self):
        """Test custom DPI setting for PNG export."""
        from sagittarius.viz.export import export_figure
        
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 9])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_plot")
            paths = export_figure(fig, output_path, formats=['png'], dpi=150)
            
            # File should exist and be reasonable size
            assert os.path.exists(paths['png'])
            file_size = os.path.getsize(paths['png'])
            assert file_size > 1000  # At least 1KB
        
        plt.close()
    
    def test_no_metadata_option(self):
        """Test disabling metadata JSON generation."""
        from sagittarius.viz.export import export_figure
        
        fig, ax = plt.subplots()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_plot")
            paths = export_figure(fig, output_path, formats=['png'], save_metadata=False)
            
            assert 'png' in paths
            assert 'json' not in paths
            assert not os.path.exists(output_path + '.metadata.json')
        
        plt.close()


class TestBuildProvenanceMetadata:
    """Test suite for _build_provenance_metadata function."""
    
    def test_basic_metadata_structure(self):
        """Test basic metadata structure without result object."""
        from sagittarius.viz.export import _build_provenance_metadata
        
        metadata = _build_provenance_metadata(
            artifact_id='test_001',
            plot_function='test_func',
            plot_params={'key': 'value'},
        )
        
        assert metadata['schema_version'] == 'chart-export/v1'
        assert metadata['provenance']['artifact_id'] == 'test_001'
        assert metadata['plotting']['function'] == 'test_func'
        assert metadata['plotting']['parameters']['key'] == 'value'
        assert 'environment' in metadata
        assert 'disclaimer' in metadata
    
    def test_metadata_with_result_object(self):
        """Test metadata extraction from result object."""
        from sagittarius.viz.export import _build_provenance_metadata
        
        # Create mock result
        class MockResult:
            def __init__(self):
                self.manifest = {'artifact_id': 'result_001'}
                self.mode_version = 'v1.0'
                self.schema_version = 'result/v1'
                self.backend = 'julia'
                self.seed = 42
        
        result = MockResult()
        metadata = _build_provenance_metadata(result=result)
        
        assert metadata['provenance']['artifact_id'] == 'result_001'
        assert metadata['provenance']['mode_version'] == 'v1.0'
        assert metadata['provenance']['backend_type'] == 'julia'
        assert metadata['provenance']['random_seed'] == 42
    
    def test_extra_metadata_merge(self):
        """Test merging extra metadata."""
        from sagittarius.viz.export import _build_provenance_metadata
        
        extra = {'custom_field': 'custom_value', 'another': 123}
        metadata = _build_provenance_metadata(extra_metadata=extra)
        
        assert metadata['custom_field'] == 'custom_value'
        assert metadata['another'] == 123


class TestExportFromResult:
    """Test suite for export_from_result convenience function."""
    
    def test_export_with_synthetic_result(self):
        """Test export using synthetic result object."""
        from sagittarius.viz.export import export_from_result
        
        # Create mock result and plot function
        class MockResult:
            def __init__(self):
                self.manifest = {'artifact_id': 'synthetic_001'}
                self.mode_version = 'v1.0'
        
        def mock_plot(result, ax, **kwargs):
            ax.plot([1, 2, 3], label='Mock Data')
            ax.set_title(kwargs.get('title', 'Mock Plot'))
            ax.legend()
            return ax
        
        result = MockResult()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_export")
            paths = export_from_result(
                result=result,
                plot_func=mock_plot,
                output_path=output_path,
                formats=['png'],
                plot_args={'title': 'Test Title'},
            )
            
            assert 'png' in paths
            assert 'json' in paths
            assert os.path.exists(paths['png'])
            
            # Verify metadata includes result info
            with open(paths['json'], 'r') as f:
                metadata = json.load(f)
            
            assert metadata['provenance']['artifact_id'] == 'synthetic_001'
        
        plt.close('all')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])