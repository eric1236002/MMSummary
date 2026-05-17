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
    # 這個函式統一建立 LLM 物件，避免不同路徑各自組裝 provider 參數。
    # 這樣做的好處是：模型名稱、API key、temperature 與 token 上限的規則只要改一處。
    model_lower = (model or "").lower()

    def _uses_max_completion_tokens(model_name: str) -> bool:
        # Some newer OpenAI models (e.g. GPT-5 family) reject `max_tokens` and require
        # `max_completion_tokens` instead.
        return model_name.startswith("gpt-5")

    def _restricts_temperature(model_name: str) -> bool:
        # Some models only support the provider default temperature.
        return model_name.startswith("gpt-5")

    if model_lower.startswith("gpt"):
        kwargs = {
            "model": model,
            "api_key": os.environ.get("OPENAI_API_KEY"),
        }
        if _restricts_temperature(model_lower):
            kwargs["temperature"] = 1
        else:
            kwargs["temperature"] = temperature
        if max_tokens is not None:
            if _uses_max_completion_tokens(model_lower):
                kwargs["model_kwargs"] = {"max_completion_tokens": max_tokens}
            else:
                kwargs["max_tokens"] = max_tokens
        return ChatOpenAI(**kwargs)
    else:
        # 非 OpenAI 模型走 OpenRouter，讓同一套摘要流程可以支援多個供應商。
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
    # Map 階段的責任：把每個 chunk 各自摘要，之後再交給 reduce 彙整。
    # 若外部沒有傳入自訂模板，就讀取預設模板檔，確保行為一致。
    if not map_template:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(base_dir, "template", "map_template.txt")
        
        with open(template_path, "r", encoding="utf-8") as f:
            map_template = f.read()
            
    map_prompt = PromptTemplate.from_template(map_template)
    return LLMChain(llm=llm, prompt=map_prompt)

# Reduce function for LLM chain
def reduce_function(llm, reduce_template=None):
    # Reduce 階段負責把 map 的片段結果再合併成最後摘要。
    # 同樣支援預設模板與自訂模板，讓流程可配置但不必改程式碼。
    if not reduce_template:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(base_dir, "template", "reduce_template.txt")

        with open(template_path, "r", encoding="utf-8") as f:
            reduce_template = f.read()

    reduce_prompt = PromptTemplate.from_template(reduce_template)
    return LLMChain(llm=llm, prompt=reduce_prompt)

def process_map_results(split_docs, model, map_template=None):
    # 對每個切片逐一執行 map chain，收集各 chunk 的中間摘要結果。
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
    # 把 map 階段的輸出轉成 Documents，再交給 ReduceDocumentsChain 做合併。
    # 這裡同時處理「縮減」與「必要時多輪折疊」的邏輯，以避免超過 token 上限。
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
    # 先把原文切成多個 chunk，供 map-reduce 或直接後續處理使用。
    # 若 chunk_size 無效，直接回傳空列表，讓上層可以決定 fallback 行為。
    if chunk_size is None or int(chunk_size) <= 0:
        return []
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
                     direct_mode: bool = False,
                     map_template: str = None, reduce_template: str = None,
                     reduce_temperature: float = 0.0) -> str:
    # 這是摘要流程的主入口：依據模式選擇 test / direct / map-reduce 三條路徑。
    # - test_mode：回傳固定文字，方便驗證 API 與資料庫流程。
    # - direct_mode：不切 chunk，直接把全文送進 reduce prompt。
    # - 預設：先切分，再決定要 map 還是直接帶 chunk 給 reduce。
    if test_mode:
        return f"【測試模式】這是一段自動生成的摘要測試文字。\n\n*   模型：{model}\n*   輸入長度：{len(text)} 字\n*   這是為了確認資料庫儲存功能是否正常而生成的佔位符。"
        
    if direct_mode:
        # direct_mode 適合短文本或想跳過 map 成本的情境。
        llm = init_llm(reduce_temperature, model, max_tokens=token_max)
        reduce_chain = reduce_function(llm, reduce_template=reduce_template)
        res = reduce_chain.invoke({"docs": text})
        if isinstance(res, dict):
            return res.get("text", res.get("output_text", res.get("output", str(res))))
        return str(res)
    
    split_docs1 = split_text(text, chunk_size_1, chunk_overlap_1)
    split_docs2 = split_text(text, chunk_size_2, chunk_overlap_2)
    
    combined_map_results = []
    
    if not split_docs1 and not split_docs2:
        # 如果兩組切分都失敗，就退回把全文當成單一 Document，避免流程直接中斷。
        combined_map_results = [Document(page_content=text)]
    elif use_map:
        # use_map=True 時，先對 chunk 做 map，再把 map 結果交給 reduce。
        map1_results = process_map_results(split_docs1, model, map_template=map_template) if split_docs1 else []
        map2_results = process_map_results(split_docs2, model, map_template=map_template) if split_docs2 else []
        combined_map_results = map1_results + map2_results
    else:
        # use_map=False 時，略過 map，直接把切片交給 reduce。
        combined_map_results = split_docs1 + split_docs2

    response = process_reduce_results(combined_map_results, token_max, model, 
                                      reduce_template=reduce_template, 
                                      reduce_temperature=reduce_temperature)
    return response
