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
    if model.lower().startswith("gpt"):
        return ChatOpenAI(
            temperature=temperature, 
            model=model, 
            api_key=os.environ.get('OPENAI_API_KEY'), 
            max_tokens=max_tokens
        )
    else:
        return ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            model=model, 
            temperature=temperature, 
            api_key=os.environ.get('OPENROUTER_API_KEY'), 
            max_tokens=max_tokens,
            default_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "MMSummary React"
            }
        )

# Map function for LLM chain
def map_function(llm, map_template=None):
    if not map_template:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(base_dir, "template", "map_template.txt")
        
        with open(template_path, "r", encoding="utf-8") as f:
            map_template = f.read()
            
    map_prompt = PromptTemplate.from_template(map_template)
    return LLMChain(llm=llm, prompt=map_prompt)

# Reduce function for LLM chain
def reduce_function(llm, reduce_template=None):
    if not reduce_template:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(base_dir, "template", "reduce_template.txt")

        with open(template_path, "r", encoding="utf-8") as f:
            reduce_template = f.read()

    reduce_prompt = PromptTemplate.from_template(reduce_template)
    return LLMChain(llm=llm, prompt=reduce_prompt)

def process_map_results(split_docs, model, map_template=None):
    temp = []
    map_chain = map_function(init_llm(0, model, 1000), map_template=map_template)

    for doc in split_docs:
        result = map_chain.invoke(doc)
        if isinstance(result, dict):
            content = result.get("text", result.get("output", result.get("output_text", str(result))))
        else:
            content = str(result)
        temp.append(content)
    
    return temp

def process_reduce_results(combined_map_results, token_max, model, reduce_template=None, reduce_temperature=0.0):
    reduce_chain = reduce_function(init_llm(reduce_temperature, model, 4000), reduce_template=reduce_template)

    prompt = PromptTemplate.from_template("折疊此內容: {docs}")
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
                     reduce_temperature: float = 0.0) -> str:
    
    if test_mode:
        return f"【測試模式】這是一段自動生成的摘要測試文字。\n\n*   模型：{model}\n*   輸入長度：{len(text)} 字\n*   這是為了確認資料庫儲存功能是否正常而生成的佔位符。"
    
    split_docs1 = split_text(text, chunk_size_1, chunk_overlap_1)
    split_docs2 = split_text(text, chunk_size_2, chunk_overlap_2)
    
    combined_map_results = []
    
    if use_map:
        map1_results = process_map_results(split_docs1, model, map_template=map_template)
        map2_results = process_map_results(split_docs2, model, map_template=map_template)
        combined_map_results = map1_results + map2_results
    else:
        combined_map_results = split_docs1 + split_docs2

    response = process_reduce_results(combined_map_results, token_max, model, 
                                      reduce_template=reduce_template, 
                                      reduce_temperature=reduce_temperature)
    return response
