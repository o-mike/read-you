import os
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from src.readme_generator import ReadmeGenerator

@pytest.fixture
def mock_openai_response():
    return Mock(choices=[Mock(message=Mock(content="# Test README\nThis is a test README."))])

@pytest.fixture
def sample_repo(tmp_path):
    # Create a temporary repository structure
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    
    # Create some sample files
    (repo_dir / "src").mkdir()
    (repo_dir / "src" / "main.py").write_text("def main():\n    print('Hello')")
    (repo_dir / "src" / "utils.py").write_text("def helper():\n    return True")
    
    return repo_dir

def test_analyze_directory(sample_repo):
    generator = ReadmeGenerator()
    results = generator.analyze_directory(sample_repo)
    
    assert '.py' in results
    assert len(results['.py']) == 2
    assert 'def main():' in results['.py'][0] or results['.py'][1]

@patch('openai.OpenAI')
def test_generate_readme_non_verbose(mock_openai, sample_repo, mock_openai_response):
    mock_openai.return_value.chat.completions.create.return_value = mock_openai_response
    
    generator = ReadmeGenerator()
    content = generator.generate_readme(str(sample_repo), verbose=False)
    
    assert content == "# Test README\nThis is a test README."
    
    # Verify that the OpenAI API was called with non-verbose prompt
    call_args = mock_openai.return_value.chat.completions.create.call_args[1]
    assert "concise README" in call_args['messages'][1]['content']
    assert call_args['max_tokens'] == 1000

@patch('openai.OpenAI')
def test_generate_readme_verbose(mock_openai, sample_repo, mock_openai_response):
    mock_openai.return_value.chat.completions.create.return_value = mock_openai_response
    
    generator = ReadmeGenerator()
    content = generator.generate_readme(str(sample_repo), verbose=True)
    
    assert content == "# Test README\nThis is a test README."
    
    # Verify that the OpenAI API was called with verbose prompt
    call_args = mock_openai.return_value.chat.completions.create.call_args[1]
    assert "comprehensive README" in call_args['messages'][1]['content']
    assert call_args['max_tokens'] == 2000

def test_save_readme(sample_repo):
    generator = ReadmeGenerator()
    content = "# Test README\nThis is a test content."
    generator.save_readme(str(sample_repo), content)
    
    readme_path = sample_repo / "README.md"
    assert readme_path.exists()
    assert readme_path.read_text() == content

def test_save_readme_dry_run(sample_repo, capsys):
    generator = ReadmeGenerator()
    content = "# Test README\nThis is a test content."
    generator.save_readme(str(sample_repo), content, dry_run=True)
    
    # Check that file was not created
    readme_path = sample_repo / "README.md"
    assert not readme_path.exists()
    
    # Check console output
    captured = capsys.readouterr()
    assert "# Test README" in captured.out
    assert "This is a test content" in captured.out
