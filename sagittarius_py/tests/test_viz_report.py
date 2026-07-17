"""
Unit tests for lightweight report generation.

Tests the ReportGenerator class and generate_quick_report function, including:
- HTML and Markdown report generation
- Result summary addition
- Chart embedding
- Classification distinction (exploratory vs benchmark)
- Manifest linking
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


class TestReportGenerator:
    """Test suite for ReportGenerator class."""
    
    def test_basic_html_report(self):
        """Test basic HTML report generation."""
        from sagittarius.viz.report import ReportGenerator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            reporter = ReportGenerator(output_dir=tmpdir, report_type='html', title='Test Report')
            report_path = reporter.generate('test_report.html')
            
            assert os.path.exists(report_path)
            assert report_path.endswith('.html')
            
            # Check HTML content
            with open(report_path, 'r') as f:
                content = f.read()
            
            assert '<!DOCTYPE html>' in content
            assert 'Test Report' in content
    
    def test_basic_markdown_report(self):
        """Test basic Markdown report generation."""
        from sagittarius.viz.report import ReportGenerator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            reporter = ReportGenerator(output_dir=tmpdir, report_type='markdown', title='Test MD Report')
            report_path = reporter.generate('test_report.md')
            
            assert os.path.exists(report_path)
            assert report_path.endswith('.md')
            
            # Check Markdown content
            with open(report_path, 'r') as f:
                content = f.read()
            
            assert '# Test MD Report' in content
    
    def test_add_result_summary_exploratory(self):
        """Test adding exploratory result summary."""
        from sagittarius.viz.report import ReportGenerator
        
        class MockResult:
            def __init__(self):
                self.manifest = {'artifact_id': 'expl_001'}
                self.mode_version = 'v1.0'
                self.backend = 'julia'
                self.seed = 42
        
        result = MockResult()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            reporter = ReportGenerator(output_dir=tmpdir, title='Test')
            reporter.add_result_summary(result, classification='exploratory')
            report_path = reporter.generate('test.html')
            
            with open(report_path, 'r') as f:
                content = f.read()
            
            assert 'EXPLORATORY VISUALIZATION' in content or 'exploratory' in content.lower()
            assert 'expl_001' in content
    
    def test_add_result_summary_benchmark(self):
        """Test adding benchmark evidence result summary."""
        from sagittarius.viz.report import ReportGenerator
        
        class MockResult:
            def __init__(self):
                self.manifest = {'artifact_id': 'bench_001'}
                self.mode_version = 'v1.0'
        
        result = MockResult()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            reporter = ReportGenerator(output_dir=tmpdir, title='Test')
            reporter.add_result_summary(result, classification='benchmark_evidence')
            report_path = reporter.generate('test.html')
            
            with open(report_path, 'r') as f:
                content = f.read()
            
            assert 'BENCHMARK EVIDENCE' in content or 'benchmark' in content.lower()
            assert 'bench_001' in content
    
    def test_invalid_classification_raises_error(self):
        """Test that invalid classification raises ValueError."""
        from sagittarius.viz.report import ReportGenerator
        
        class MockResult:
            def __init__(self):
                self.manifest = {}
        
        reporter = ReportGenerator(title='Test')
        
        with pytest.raises(ValueError, match="Invalid classification"):
            reporter.add_result_summary(MockResult(), classification='invalid')
    
    def test_add_chart_with_classification(self):
        """Test adding chart with classification."""
        from sagittarius.viz.report import ReportGenerator
        
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 9])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            reporter = ReportGenerator(output_dir=tmpdir, title='Test')
            reporter.add_chart(
                fig=fig,
                title='Test Chart',
                description='A test chart',
                classification='exploratory',
            )
            report_path = reporter.generate('test.html')
            
            # Check that chart file was saved
            chart_files = [f for f in os.listdir(tmpdir) if f.startswith('chart_')]
            assert len(chart_files) > 0
            
            # Check report references chart
            with open(report_path, 'r') as f:
                content = f.read()
            
            assert 'Test Chart' in content
            assert any(cf in content for cf in chart_files)
        
        plt.close()
    
    def test_add_manifest_link(self):
        """Test adding manifest file link."""
        from sagittarius.viz.report import ReportGenerator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a dummy manifest
            manifest_path = os.path.join(tmpdir, 'manifest.json')
            with open(manifest_path, 'w') as f:
                json.dump({'artifact_id': 'test'}, f)
            
            reporter = ReportGenerator(output_dir=tmpdir, title='Test')
            reporter.add_manifest_link(manifest_path, 'Test manifest')
            report_path = reporter.generate('test.html')
            
            with open(report_path, 'r') as f:
                content = f.read()
            
            assert 'manifest.json' in content
            assert 'Test manifest' in content
    
    def test_method_chaining(self):
        """Test that methods support chaining."""
        from sagittarius.viz.report import ReportGenerator
        
        class MockResult:
            def __init__(self):
                self.manifest = {'artifact_id': 'chain_001'}
        
        result = MockResult()
        fig, ax = plt.subplots()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            reporter = ReportGenerator(output_dir=tmpdir, title='Test')
            
            # Chain multiple calls
            reporter.add_result_summary(result, 'exploratory') \
                   .add_chart(fig, 'Chart', classification='exploratory') \
                   .generate('test.html')
            
            assert os.path.exists(os.path.join(tmpdir, 'test.html'))
        
        plt.close()
    
    def test_custom_metrics_in_summary(self):
        """Test adding custom metrics to result summary."""
        from sagittarius.viz.report import ReportGenerator
        
        class MockResult:
            def __init__(self):
                self.manifest = {'artifact_id': 'metrics_001'}
        
        result = MockResult()
        custom_metrics = {
            'accuracy': 0.95,
            'runtime': 1.23,
            'memory_mb': 256,
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            reporter = ReportGenerator(output_dir=tmpdir, title='Test')
            reporter.add_result_summary(result, 'exploratory', custom_metrics=custom_metrics)
            report_path = reporter.generate('test.html')
            
            with open(report_path, 'r') as f:
                content = f.read()
            
            assert 'accuracy' in content
            assert '0.95' in content
    
    def test_auto_generated_filename(self):
        """Test auto-generated filename when not specified."""
        from sagittarius.viz.report import ReportGenerator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            reporter = ReportGenerator(output_dir=tmpdir, title='Test')
            report_path = reporter.generate()  # No filename specified
            
            assert os.path.exists(report_path)
            assert 'report_' in os.path.basename(report_path)
    
    def test_multiple_results_mixed_classification(self):
        """Test report with multiple results of different classifications."""
        from sagittarius.viz.report import ReportGenerator
        
        class MockResult:
            def __init__(self, aid):
                self.manifest = {'artifact_id': aid}
        
        results = [MockResult('expl_001'), MockResult('bench_001')]
        classifications = ['exploratory', 'benchmark_evidence']
        
        with tempfile.TemporaryDirectory() as tmpdir:
            reporter = ReportGenerator(output_dir=tmpdir, title='Mixed Report')
            
            for result, classification in zip(results, classifications):
                reporter.add_result_summary(result, classification)
            
            report_path = reporter.generate('mixed.html')
            
            with open(report_path, 'r') as f:
                content = f.read()
            
            assert 'expl_001' in content
            assert 'bench_001' in content
            # Should have both exploratory and benchmark sections
            assert content.count('section') >= 2


class TestGenerateQuickReport:
    """Test suite for generate_quick_report convenience function."""
    
    def test_basic_quick_report(self):
        """Test basic quick report generation."""
        from sagittarius.viz.report import generate_quick_report
        
        class MockResult:
            def __init__(self, aid):
                self.manifest = {'artifact_id': aid}
        
        results = [MockResult('qr_001'), MockResult('qr_002')]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = generate_quick_report(
                results=results,
                output_dir=tmpdir,
                title='Quick Report',
            )
            
            assert os.path.exists(report_path)
            assert '.html' in report_path
    
    def test_custom_classifications(self):
        """Test quick report with custom classifications."""
        from sagittarius.viz.report import generate_quick_report
        
        class MockResult:
            def __init__(self, aid):
                self.manifest = {'artifact_id': aid}
        
        results = [MockResult('expl_001'), MockResult('bench_001')]
        classifications = ['exploratory', 'benchmark_evidence']
        
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = generate_quick_report(
                results=results,
                output_dir=tmpdir,
                classifications=classifications,
            )
            
            with open(report_path, 'r') as f:
                content = f.read()
            
            assert 'expl_001' in content
            assert 'bench_001' in content
    
    def test_mismatched_lengths_raises_error(self):
        """Test that mismatched results/classifications raises error."""
        from sagittarius.viz.report import generate_quick_report
        
        class MockResult:
            def __init__(self):
                self.manifest = {}
        
        results = [MockResult(), MockResult()]
        classifications = ['exploratory']  # Only one for two results
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="same length"):
                generate_quick_report(results, tmpdir, classifications=classifications)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])