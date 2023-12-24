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
    with open("MMSummary/map_template.txt", "r") as f:
        map_template = f.read()
    map_prompt = PromptTemplate.from_template(map_template)
    return LLMChain(llm=llm, prompt=map_prompt)

# Reduce function for LLM chain
def reduce_function(llm):
    with open("MMSummary/reduce_template.txt", "r") as f:
        reduce_template = f.read()
    reduce_prompt = PromptTemplate.from_template(reduce_template)
    return LLMChain(llm=llm, prompt=reduce_prompt)

# Process the map
def process_map_results(split_docs, llm):
    map_chain = map_function(llm)
    return [map_chain.run(doc) for doc in split_docs]

# Process the reduce
def process_reduce_results(combined_map_results, llm,token_max):
    reduce_chain = reduce_function(llm)
    combine_documents_chain = StuffDocumentsChain(llm_chain=reduce_chain, document_variable_name="docs")
    reduce_documents_chain = ReduceDocumentsChain(combine_documents_chain=combine_documents_chain,collapse_documents_chain=combine_documents_chain,token_max=token_max)
    documents = [Document(page_content=content) for content in combined_map_results]
    return reduce_documents_chain.run(documents)

# Split the text into chunks
def split_text(text, chunk_size, chunk_overlap):
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    file_content=text_splitter.create_documents([text])
    split_docs = text_splitter.split_documents(file_content)
    return split_docs

# Process the file
def process_file(uploaded_file, chunk_size_1, chunk_overlap_1, chunk_size_2, chunk_overlap_2, temperature, token_max):
    file_name = uploaded_file.name.split(".")[0]
    file_content = uploaded_file.getvalue().decode("utf-8")

    llm = init_llm(temperature)

    # First map stage
    split_docs = split_text(file_content, chunk_size_1, chunk_overlap_1)
    first_map_results = process_map_results(split_docs,llm)
    st.text_area("Map 1:",first_map_results[0], height=200)

    # Second map stage
    split_docs = split_text(file_content, chunk_size_2, chunk_overlap_2)
    second_map_results = process_map_results(split_docs,llm)
    st.text_area("Map 2:",second_map_results[0], height=200)
    # Merge map results
    combined_map_results = first_map_results + second_map_results

    # Reduce stage
    response=process_reduce_results(combined_map_results, llm,token_max)

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
                st.success(f"處理完成!耗時{round(end-start)}秒")

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
