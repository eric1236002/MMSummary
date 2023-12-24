import streamlit as st
import time
from langchain.chains import MapReduceDocumentsChain, ReduceDocumentsChain
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.document_loaders import TextLoader
from langchain_core.documents import Document
import os

# Initialize the LLM chain
def init_llm(temperature):
    return ChatOpenAI(temperature=temperature, model="gpt-4-1106-preview", api_key=os.environ['OPENAI_API_KEY'])

# Map function for LLM chain
def map_function(llm):
    map_template = """您是專業的會議總結助理。您唯一的任務是為給定的會議記錄提供簡潔的摘要。確保最終總結和行動項目被翻譯成繁體中文，並且不包含任何個人意見或解釋。
                    以下是會議內容逐字稿參考以上輸出格式來總結會議內容逐字稿，切記總結的內容要真實不可幻想，尤其是行動項目的部分
                    '{docs}'
                    """
    map_prompt = PromptTemplate.from_template(map_template)
    return LLMChain(llm=llm, prompt=map_prompt)

# Reduce function for LLM chain
def reduce_function(llm):
    reduce_template ="""您是專業的會議總結助理。您唯一的任務是為給定的會議記錄提供簡潔的摘要。以下是一些規則：
                        <規則>
                        1.摘要應根據不同的主題分為不同的部分，每個部分都應以要點的形式來回答。
                        2. 如果適用，您還應該列出行動項目，包括任務所有者和截止日期。
                        3. 確保最終總結和行動項目被翻譯成繁體中文，並且不包含任何個人意見或解釋。

                        這是輸出的參考的格式:
                        ## 主題1

                        - point 1
                        - point 2
                        ...
                        - point N

                        ## 主題2

                        - point 1
                        - point 2
                        ...
                        - point N

                        ## 主題3
                        - point 1
                        - point 2
                        ...
                        - point N
                        .
                        .
                        .
                        ## 主題N
                        - point 1
                        - point 2
                        ...
                        - point N

                        ## 行動項目

                        - 負責人1: 任務名 
                        - 負責人2: 任務名 
                        ...
                        - 負責人N: 任務名 

                        以下是會議內容參考以上輸出格式來總結會議內容，切記總結的內容要真實不可幻想，尤其是行動項目的部分

                        {docs}
                        """
    reduce_prompt = PromptTemplate.from_template(reduce_template)
    return LLMChain(llm=llm, prompt=reduce_prompt)

def map_reduce_function(token_max, map_chain, reduce_chain):
    combine_documents_chain = StuffDocumentsChain(llm_chain=reduce_chain, document_variable_name="docs")
    reduce_documents_chain = ReduceDocumentsChain(
        combine_documents_chain=combine_documents_chain,
        collapse_documents_chain=combine_documents_chain,
        token_max=token_max,
    )
    return MapReduceDocumentsChain(
        llm_chain=map_chain,
        reduce_documents_chain=reduce_documents_chain,
        document_variable_name="docs",
        return_intermediate_steps=False,
    )

def process_map_results(file_content, llm, chunk_size,chunk_overlap):
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    file_content=text_splitter.create_documents([file_content])
    split_docs = text_splitter.split_documents(file_content)
    map_chain = map_function(llm)
    return [map_chain.run(doc) for doc in split_docs]

# Process the file
def process_file(uploaded_file, chunk_size_1, chunk_overlap_1, chunk_size_2, chunk_overlap_2, temperature, token_max):
    file_name = uploaded_file.name.split(".")[0]
    file_content = uploaded_file.getvalue().decode("utf-8")
    # text_splitter = CharacterTextSplitter.from_tiktoken_encoder(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    # file_content=text_splitter.create_documents([file_content])
    # split_docs = text_splitter.split_documents(file_content)

    llm = init_llm(temperature)

    # 第一階段映射
    first_map_results = process_map_results(file_content,llm, chunk_size_1, chunk_overlap_1)
    st.text_area("Map 1:",first_map_results[0], height=200)
    # 第二階段映射
    second_map_results = process_map_results(file_content,llm, chunk_size_2, chunk_overlap_2)
    st.text_area("Map 2:",second_map_results[0], height=200)
    # 組合映射結果
    combined_map_results = first_map_results + second_map_results

    # 縮減階段
    reduce_chain = reduce_function(llm)

    combine_documents_chain = StuffDocumentsChain(llm_chain=reduce_chain, document_variable_name="docs")
    reduce_documents_chain = ReduceDocumentsChain(combine_documents_chain=combine_documents_chain,collapse_documents_chain=combine_documents_chain,token_max=token_max,)
    documents = [Document(page_content=content) for content in combined_map_results]
    # combined_result, extra_info = reduce_documents_chain.combine_docs(documents)
    response = reduce_documents_chain.run(documents)
    # reduce_chain = reduce_function(llm)
    # map_reduce_chain = map_reduce_function(token_max, map_chain, reduce_chain)
    # response = map_reduce_chain.run(split_docs)
    return response, file_name

# Main function to run the Streamlit app
def main():
    st.title("Meeting minutes Summary 💬")
    if 'response' not in st.session_state:
        st.session_state['response'] = None
        st.session_state['file_name'] = ""

    tab1, tab2 = st.tabs(["GPT-4-16k", "參數調整"])
    with tab2:
        chunk_size_1 = st.number_input("Chunk size 1", value=4000, min_value=1, max_value=10000, step=100)
        chunk_overlap_1 = st.number_input("Chunk overlap 1", value=1000, min_value=0, max_value=10000, step=100)
        chunk_size_2 = st.number_input("Chunk size 2", value=2000, min_value=1, max_value=10000, step=100)
        chunk_overlap_2 = st.number_input("Chunk overlap 2", value=0, min_value=0, max_value=10000, step=100)
        token_max = st.number_input("Token max", value=16000, min_value=1, max_value=100000, step=100, help="將Map生成的內容長度再次進行分割，避免超過LLM的長度限制")
        temperature = st.slider('Temperature', 0.0, 2.0, step=0.1)

    with tab1:
        uploaded_file = st.file_uploader("選擇文件", type=["txt"])
        if uploaded_file is not None and (uploaded_file.name.split(".")[0] != st.session_state['file_name']):
            with st.spinner("處理中..."):
                start = time.time()
                st.session_state['response'], st.session_state['file_name'] = process_file(uploaded_file, chunk_size_1, chunk_overlap_1, chunk_size_2, chunk_overlap_2, temperature, token_max)
                end=time.time()
                st.success(f"處理完成!{round(end-start)}")

        if st.session_state['response']:
            st.text_area("Summary", st.session_state['response'], height=300)
            st.download_button(
                label="下載摘要",
                data=st.session_state['response'],
                file_name=f"{st.session_state['file_name']}_output_{chunk_size_1}_{chunk_overlap_1}_{chunk_size_2}_{chunk_overlap_2}_{temperature}.txt",
                mime="text/plain",
            )

if __name__ == "__main__":
    main()
