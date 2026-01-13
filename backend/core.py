import os
import time
from langchain.chains import MapReduceDocumentsChain, ReduceDocumentsChain
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

def init_llm(temperature, model, max_tokens=1000):
    is_new_openai = "o1" in model.lower() or "gpt-5" in model.lower()
    
    llm_params = {
        "model": model,
    }
    
    if is_new_openai:
        llm_params["temperature"] = 1
    else:
        llm_params["temperature"] = temperature
    
    if is_new_openai:
        llm_params["model_kwargs"] = {"max_completion_tokens": max_tokens}
    else:
        llm_params["max_tokens"] = max_tokens

    if model.lower().startswith("gpt"):
        return ChatOpenAI(
            api_key=os.environ.get('OPENAI_API_KEY'), 
            **llm_params
        )
    else:
        return ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ.get('OPENROUTER_API_KEY'), 
            default_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "MMSummary React"
            },
            **llm_params
        )

# Map function for LLM chain
def map_function(llm, map_template=None, language="Traditional Chinese"):
    if not map_template:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(base_dir, "template", "map_template.txt")
        
        with open(template_path, "r", encoding="utf-8") as f:
            map_template = f.read()
            

    map_template = map_template.replace("{language}", language)
    map_prompt = PromptTemplate.from_template(map_template)
    return LLMChain(llm=llm, prompt=map_prompt)

# Reduce function for LLM chain
def reduce_function(llm, reduce_template=None, language="Traditional Chinese"):
    if not reduce_template:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(base_dir, "template", "reduce_template.txt")

        with open(template_path, "r", encoding="utf-8") as f:
            reduce_template = f.read()

    reduce_template = reduce_template.replace("{language}", language)
    reduce_prompt = PromptTemplate.from_template(reduce_template)
    return LLMChain(llm=llm, prompt=reduce_prompt)

def process_map_results(split_docs, model, map_template=None, language="Traditional Chinese"):
    temp = []
    map_chain = map_function(init_llm(0, model, 1000), map_template=map_template, language=language)

    for doc in split_docs:
        result = map_chain.invoke(doc)
        if isinstance(result, dict):
            content = result.get("text", result.get("output", result.get("output_text", str(result))))
        else:
            content = str(result)
        temp.append(content)
    
    return temp

def process_reduce_results(combined_map_results, token_max, model, reduce_template=None, language="Traditional Chinese", reduce_temperature=0.0):
    reduce_chain = reduce_function(init_llm(reduce_temperature, model, 4000), reduce_template=reduce_template, language=language)

    prompt = PromptTemplate.from_template("Collapse the following content: {docs}")
    llm_chain = LLMChain(llm=init_llm(0, model, 4000), prompt=prompt)

    collapse_documents_chain = StuffDocumentsChain(llm_chain=llm_chain, document_separator="docs")
    combine_documents_chain = StuffDocumentsChain(llm_chain=reduce_chain, document_variable_name="docs")
    reduce_documents_chain = ReduceDocumentsChain(combine_documents_chain=combine_documents_chain, collapse_documents_chain=collapse_documents_chain, token_max=token_max)
    
    documents = []
    for content in combined_map_results:
        if isinstance(content, str):
            documents.append(Document(page_content=content))
        else:
            documents.append(content)
            
    res = reduce_documents_chain.invoke(documents)
        # Extract string from result dict if necessary
    if isinstance(res, dict):
        return res.get("output_text", res.get("text", res.get("output", str(res))))
    return res

def split_text(text, chunk_size, chunk_overlap):
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
        separator=" ",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    file_content = text_splitter.create_documents([text])
    split_docs = text_splitter.split_documents(file_content) 
    return split_docs

def generate_summary(text: str, model: str, chunk_size_1: int, chunk_overlap_1: int, 
                     chunk_size_2: int, chunk_overlap_2: int, token_max: int, 
                     use_map: bool, test_mode: bool = False, 
                     map_template: str = None, reduce_template: str = None,
                     reduce_temperature: float = 0.0, language: str = "Traditional Chinese") -> str:
    
    if test_mode:
        return f"【Test Mode】This is a test summary generated by the system.\n\n*    Model: {model}\n*    Target Language: {language}\n*    Input Length: {len(text)} characters\n*    This is a placeholder generated to ensure the database storage function is working properly."
    
    split_docs1 = split_text(text, chunk_size_1, chunk_overlap_1)
    split_docs2 = split_text(text, chunk_size_2, chunk_overlap_2)
    
    combined_map_results = []
    
    if use_map:
        map1_results = process_map_results(split_docs1, model, map_template=map_template, language=language)
        map2_results = process_map_results(split_docs2, model, map_template=map_template, language=language)
        combined_map_results = map1_results + map2_results
    else:
        combined_map_results = split_docs1 + split_docs2

    response = process_reduce_results(combined_map_results, token_max, model, 
                                      reduce_template=reduce_template, 
                                      language=language,
                                      reduce_temperature=reduce_temperature)
    return response
