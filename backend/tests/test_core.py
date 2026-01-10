# tests/test_core.py
import pytest
from backend.core import split_text, init_llm, generate_summary, map_function, reduce_function, process_map_results, process_reduce_results


def test_init_llm():
    llm = init_llm(0, "google/gemma-3-27b-it:free", 1000)
    assert llm is not None

def test_map_function():
    llm = init_llm(0, "google/gemma-3-27b-it:free", 1000)
    map_results = map_function(llm)
    assert map_results is not None

def test_reduce_function():
    llm = init_llm(0, "google/gemma-3-27b-it:free", 1000)
    map_results = reduce_function(llm)
    assert map_results is not None

def test_process_map_results():
    model = "google/gemma-3-27b-it:free"
    map_results = process_map_results(split_text("This is a test text.", 1000, 0), model)
    assert map_results is not None

def test_process_reduce_results():
    model = "google/gemma-3-27b-it:free"
    split_docs = split_text("This is a test text.", 1000, 0)
    reduce_results = process_reduce_results(split_docs, 4000, model)
    assert reduce_results is not None

def test_split_text_logic():
    sample_text = "This is a test text."
    chunk_size = 2
    overlap = 2
    
    docs = split_text(sample_text, chunk_size, overlap)
    
    assert len(docs) > 0 
    assert hasattr(docs[0], 'page_content') 
    print(f"\nSuccessfully split into {len(docs)} chunks")

def test_generate_summary():
    model = "google/gemma-3-27b-it:free"
    text = "This is a test text."
    summary = generate_summary(
        text=text,
        model=model, 
        chunk_size_1=1000, 
        chunk_overlap_1=0,
        chunk_size_2=1000,
        chunk_overlap_2=0,
        token_max=4000, 
        use_map=True,
        test_mode=True
    )
    assert summary is not None
    print(f"\nGenerated summary: {summary}")
