from pathlib import Path

from src.pipeline.data_ingestion import read_data

class MockBucket:
    def __init__(self, exception=False):
        self.exception = exception

def test_read_data_with_json_files(tmpdir):
    """Test reading data from a directory with JSON files."""
    data = '{"key": ["value1", "value2"]}'
    for i in range(2):
        with open(Path(tmpdir) / f"test_{i}.json", 'w', encoding='utf-8') as f:
            f.write(data)
    result = read_data.fn(tmpdir.strpath)
    assert len(result) == 4  # 2 files with 2 rows each


def test_read_data_no_json_files(tmpdir):
    """Test reading data from a directory without JSON files."""
    with open(Path(tmpdir) / "test.txt", 'w', encoding='utf-8') as f:
        f.write("This is not a json file.")
    result = read_data.fn(tmpdir.strpath)
    assert result.empty


def test_read_data_nonexistent_directory():
    """Test reading data from a nonexistent directory."""
    try:
        read_data.fn("/nonexistent/directory")
    except Exception as e:
        assert isinstance(e, FileNotFoundError)
