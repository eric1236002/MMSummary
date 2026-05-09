import pytest
from backend.core import split_text, init_llm, process_map_results, process_reduce_results, generate_summary
from unittest.mock import MagicMock, patch

def test_split_text():
    text = "This is a very long text that needs to be split into multiple chunks for processing."
    chunks = split_text(text, chunk_size=10, chunk_overlap=0)
    assert len(chunks) > 1
    assert len(chunks[0].page_content) > 0


def test_split_text_chunk_size_zero_disables_split():
    chunks = split_text("hello world", chunk_size=0, chunk_overlap=0)
    assert chunks == []

def test_init_llm():
    # OpenAI API Key validation is skipped during init in many versions of langchain_openai
    # unless Sk- is missing, but with conftest.py mocking it should pass
    llm = init_llm(0, "google/gemma-3-27b-it:free", 1000)
    assert llm is not None

@patch('langchain.chains.base.Chain.invoke')
def test_process_map_results(mock_invoke):
    mock_invoke.return_value = {"output": "Mocked Map Result"}
    model = "google/gemma-3-27b-it:free"
    # Ensure some text to split
    split_docs = split_text("This is test content", 100, 0)
    results = process_map_results(split_docs, model)
    assert len(results) > 0

@patch('langchain.chains.base.Chain.invoke')
def test_process_reduce_results(mock_invoke):
    mock_invoke.return_value = {"output": "Mocked Reduce Result"}
    model = "google/gemma-3-27b-it:free"
    split_docs = split_text("Test content for reduce", 100, 0)
    summary = process_reduce_results(split_docs, 4000, model)
    assert summary == "Mocked Reduce Result"


def test_generate_summary_original_mode_no_split():
    with patch("backend.core.process_reduce_results") as mock_reduce:
        mock_reduce.return_value = "OK"
        out = generate_summary(
            text="some text",
            model="google/gemma-3-27b-it:free",
            chunk_size_1=0,
            chunk_overlap_1=0,
            chunk_size_2=0,
            chunk_overlap_2=0,
            token_max=4000,
            use_map=False,
            test_mode=False,
        )
    assert out == "OK"
