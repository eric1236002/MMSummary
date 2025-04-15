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
import eval
# Initialize the LLM chain
def init_llm(temperature,model,max_tokens=1000):
    if model=="gpt-4-1106-preview":
        return ChatOpenAI(temperature=temperature, model=model, api_key=os.environ['OPENAI_API_KEY'],max_tokens=max_tokens)
    else:
        return ChatOpenAI(openai_api_base="http://0.0.0.0:8000/v1",model=model,temperature=0,api_key=os.environ['OPENAI_API_KEY'],max_tokens=max_tokens)


# Map function for LLM chain
def map_function(llm):
    with open("./map_template2.txt", "r") as f:
        map_template = f.read()
    map_prompt = PromptTemplate.from_template(map_template)
    return LLMChain(llm=llm, prompt=map_prompt)

# Reduce function for LLM chain
def reduce_function(llm):
    with open("./reduce_template.txt", "r") as f:
        reduce_template = f.read()
    reduce_prompt = PromptTemplate.from_template(reduce_template)
    return LLMChain(llm=llm, prompt=reduce_prompt)

# Process the map
def process_map_results(split_docs,model):
    temp=[]
    start = time.time()
    # map_chain = map_function(llm)
    map_chain = map_function(init_llm(0,model,1000))

    st.write(f"共{len(split_docs)}個chunks")
    bar = st.progress(0, text=" ")
    for i, doc in enumerate(split_docs):
        temp.append(map_chain.run(doc))
        bar.progress((i+1)/len(split_docs)*0.99, text=f"完成第{i+1}個chunks 耗時{round(time.time()-start)}秒")
    bar.empty()

    return temp

# Process the reduce
def process_reduce_results(combined_map_results,token_max,model):
    reduce_chain = reduce_function(init_llm(0,model,4000))

    prompt = PromptTemplate.from_template("折疊此內容: {docs}")
    llm_chain = LLMChain(llm=init_llm(0,model,4000), prompt=prompt)

    collapse_documents_chain = StuffDocumentsChain(llm_chain=llm_chain,   document_separator="docs")
    combine_documents_chain  = StuffDocumentsChain(llm_chain=reduce_chain, document_variable_name="docs")
    reduce_documents_chain = ReduceDocumentsChain(combine_documents_chain=combine_documents_chain,collapse_documents_chain=collapse_documents_chain,token_max=token_max)
    documents = [Document(page_content=str(content)) for content in combined_map_results]
    return reduce_documents_chain.run(documents)

# Split the text into chunks
def split_text(text, chunk_size, chunk_overlap):
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
        separator=" ",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    file_content=text_splitter.create_documents([text])
    split_docs = text_splitter.split_documents(file_content)
    return split_docs

# Process the file
def process_file(button,model,uploaded_file, chunk_size_1, chunk_overlap_1, chunk_size_2, chunk_overlap_2, temperature, token_max):
    file_name = uploaded_file.name.split(".")[0]
    file_content = uploaded_file.getvalue().decode("utf-8")
    st.write(f"文件長度: {len(file_content)}")
    

    # First map stage
    split_docs1 = split_text(file_content, chunk_size_1, chunk_overlap_1)
    # Second map stage
    split_docs2 = split_text(file_content, chunk_size_2, chunk_overlap_2)
    if button==False:
        first_map_results = process_map_results(split_docs1,model)
        st.text_area("Map 1:",first_map_results, height=200)

        second_map_results = process_map_results(split_docs2,model)
        st.text_area("Map 2:",second_map_results, height=200)
        combined_map_results = first_map_results + second_map_results
    else:
        combined_map_results = split_docs1+split_docs2
    # st.write(len(combined_map_results))

    # Reduce stage
    response=process_reduce_results(combined_map_results,token_max,model)

    return response, file_name

# Main function to run the Streamlit app
def main():
    st.title("Meeting minutes Summary 💬")
    if 'response' not in st.session_state:
        st.session_state['response'] = None
        st.session_state['file_name'] = ""
    
    tab1, tab2,tab3 = st.tabs(["Summary", "Settings","Evaluation"])
    with tab3:
        eval.main()
    with tab2:
        button=st.checkbox("不使用Map",value=False,help="不使用Map，將所有chunck合併直接使用Reduce")
        model=st.selectbox("Choose model",["gpt-4-1106-preview","Taiwan-LLM-7B-v2.1-chat","openbuddy-deepseek-67b-v15.2"])
        openai_api_key = st.text_input("OpenAI API key", type="password", value=os.environ.get('OPENAI_API_KEY', ''), help="請填入OpenAI API key")
        if openai_api_key:
            os.environ['OPENAI_API_KEY'] = openai_api_key
        chunk_size_1 = st.number_input("Chunk size 1", value=16000, min_value=0, max_value=100000, step=100)
        chunk_overlap_1 = st.number_input("Chunk overlap 1", value=4000, min_value=0, max_value=100000, step=100)
        chunk_size_2 = st.number_input("Chunk size 2", value=8000, min_value=0, max_value=100000, step=100, help="Chunk size  0 為不使用")
        chunk_overlap_2 = st.number_input("Chunk overlap 2", value=0, min_value=0, max_value=100000, step=100)
        token_max = st.number_input("Token max", value=16000, min_value=1, max_value=100000, step=100, help="將Map生成的內容長度再次進行分割，避免超過LLM的長度限制")
        temperature = st.slider('Temperature', 0.0, 2.0, step=0.1)

    with tab1:
        uploaded_file = st.file_uploader("選擇文件", type=["txt"])
        if uploaded_file is not None and (uploaded_file.name.split(".")[0] != st.session_state['file_name']):
            with st.spinner("處理中..."):
                start = time.time()
                st.session_state['response'], st.session_state['file_name'] = process_file(button,model,uploaded_file, chunk_size_1, chunk_overlap_1, chunk_size_2, chunk_overlap_2, temperature, token_max)
                end=time.time()
                st.success(f"處理完成!耗時{round(end-start)}秒")

        if st.session_state['response']:
            st.text_area("Summary", st.session_state['response'], height=300)
            if not button:
                file_name = f"{st.session_state['file_name']}_output_{chunk_size_1}_{chunk_overlap_1}_{chunk_size_2}_{chunk_overlap_2}_{temperature}.txt"
            else:
                file_name = f"{st.session_state['file_name']}_output_{chunk_size_1}_{chunk_overlap_1}_{chunk_size_2}_{chunk_overlap_2}_{temperature}_nomap.txt"
            st.download_button(
                label="下載摘要",
                data=st.session_state['response'],
                file_name=file_name,
                mime="text/plain",
            )
if __name__ == "__main__":
    main()
