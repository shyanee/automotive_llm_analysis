import pytest
import os
from pathlib import Path
from datetime import datetime


@pytest.fixture
def report_builder():
    """Fixture to create a ReportBuilder instance."""
    from src.report_builder import ReportBuilder
    return ReportBuilder(output_dir="test_output")


def test_output_directory_creation(report_builder):
    """Test if the output directory is created upon instantiation."""
    output_dir = report_builder.output_dir
    assert output_dir.exists()
    assert output_dir.is_dir(), f"Expected directory {output_dir} to exist."


def test_build_html_report(report_builder):
    """Test HTML report generation with markdown and plots."""
    narrative = "# Report Title\nThis is a **test** narrative with *markdown*."
    plots = {
        "plot1": "<div>Plot1 HTML</div>",
        "plot2": "<div>Plot2 HTML</div>"
    }
    metadata = {
        'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'model': 'TestModel',
        'data_source': 'TestDataSource'
    }

    # Generate the report
    report_path = report_builder.build_html_report(narrative, plots, metadata)

    # Check if the report was created
    assert Path(report_path).exists(), f"Report file {report_path} was not created."
    with open(report_path, 'r', encoding='utf-8') as file:
        content = file.read()

        # Check if the narrative content is correctly rendered as HTML
        assert "<h1>Report Title</h1>" in content, "Narrative title not found in report."
        assert "This is a <strong>test</strong> narrative" in content, "Narrative content not found in report."

        # Check if plot containers are embedded
        assert '<div class="plot-container">' in content, "Plot containers not found in report."

        # Check if the metadata section is present
        assert '<div class="metadata">' in content, "Metadata section not found in report."

        # Check for individual metadata fields
        assert "Report Generated:" in content, "Generation time not found in metadata."
        assert "AI Model:" in content, "AI Model label not found in metadata."
        assert "TestModel" in content, "Model information not found in metadata."
        assert "Data Source:" in content, "Data source label not found in metadata."
        assert "TestDataSource" in content, "Data source information not found in metadata."


def test_build_html_report_default_filename(report_builder):
    """Test HTML report generation with the default filename."""
    narrative = "# Default Report"
    plots = {}

    report_path = report_builder.build_html_report(narrative, plots)

    assert Path(report_path).name == "report.html", f"Expected report filename to be 'report.html', but got {Path(report_path).name}."


def test_save_markdown(report_builder):
    """Test saving raw markdown."""
    narrative = "# Markdown Report\nThis is a **test** markdown."

    report_path = report_builder.save_markdown(narrative)

    assert Path(report_path).exists(), f"Markdown file {report_path} was not created."
    with open(report_path, 'r', encoding='utf-8') as file:
        content = file.read()
        assert "# Markdown Report" in content, "Markdown title not found in saved file."
        assert "This is a **test** markdown." in content, "Markdown content not found in saved file."


def test_report_output_is_html(report_builder):
    """Test if the generated report is a valid HTML file."""
    narrative = "# HTML Report"
    plots = {"plot1": "<div>Plot1 HTML</div>"}

    report_path = report_builder.build_html_report(narrative, plots)

    assert report_path.endswith(".html"), f"Expected report to be an HTML file, but got {report_path}."
    with open(report_path, 'r', encoding='utf-8') as file:
        content = file.read()

        # Check that the <html> tag is in the content
        assert "<html lang=\"en\">" in content, "Expected <html> tag in the report."
        assert "</html>" in content, "Expected </html> tag in the report."


@pytest.mark.parametrize(
    "metadata, expected_time_format",
    [
        (
            {"generation_time": "2025-11-28 10:00:00", 
            "model": "AI_Model", 
            "data_source": "SampleData"
          }, 
         "%Y-%m-%d %H:%M:%S"),
        (None, "%Y-%m-%d %H:%M:%S")  # Test with missing metadata
    ]
)
def test_metadata_section(report_builder, metadata, expected_time_format):
    """Test the generation of the metadata section in the report."""
    narrative = "# Metadata Report"
    plots = {}

    report_path = report_builder.build_html_report(narrative, plots, metadata)

    with open(report_path, 'r', encoding='utf-8') as file:
        content = file.read()

        # Check if the generation time matches the format
        assert "Report Generated:" in content, "Generation time header not found."
        if metadata:
            assert metadata['generation_time'][:10] in content, "Generation time does not match expected format."
        else:
            assert datetime.now().strftime(expected_time_format)[:10] in content, "Expected default generation time format not found."


@pytest.fixture(scope="module", autouse=True)
def cleanup_test_output():
    """Fixture to clean up the test output directory after tests."""
    yield
    # Clean up the output directory after tests run
    for file in Path("test_output").glob("*"):
        file.unlink()
    os.rmdir("test_output")
