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
import argparse
# Initialize the LLM chain
def init_llm(args,max_tokens=1000):
    if args.model=="gpt-4-1106-preview":
        return ChatOpenAI(temperature=args.temperature, model="gpt-4-1106-preview", api_key=args.key,max_tokens=max_tokens)
    else:
        return ChatOpenAI(openai_api_base="http://0.0.0.0:8000/v1",model=args.model,temperature=0,api_key=args.key,max_tokens=max_tokens)

# Map function for LLM chain
def map_function(llm):
    with open("/home/nips24/CCP/MMSummary/map_template2.txt", "r") as f:
        map_template = f.read()
    map_prompt = PromptTemplate.from_template(map_template)
    return LLMChain(llm=llm, prompt=map_prompt)

def reduce_function(llm):
    with open("/home/nips24/CCP/MMSummary/reduce_template.txt", "r") as f:
        reduce_template = f.read()
    reduce_prompt = PromptTemplate.from_template(reduce_template)
    return LLMChain(llm=llm, prompt=reduce_prompt)

def process_map_results(split_docs,args):
    temp=[]
    map_chain = map_function(init_llm(args,1000))
    for i, doc in enumerate(split_docs):
        temp.append(map_chain.run(doc))
    return temp

def process_reduce_results(combined_map_results,args):
    reduce_chain = reduce_function(init_llm(args,4000))
    prompt = PromptTemplate.from_template("折疊此內容: {docs}")
    llm_chain = LLMChain(llm=init_llm(args,4000), prompt=prompt)
    collapse_documents_chain = StuffDocumentsChain(llm_chain=llm_chain,   document_separator="docs")
    combine_documents_chain  = StuffDocumentsChain(llm_chain=reduce_chain, document_variable_name="docs")
    reduce_documents_chain = ReduceDocumentsChain(combine_documents_chain=combine_documents_chain,collapse_documents_chain=collapse_documents_chain,token_max=args.token_max)
    documents = [Document(page_content=str(content)) for content in combined_map_results]
    return reduce_documents_chain.run(documents)

# Split the text into chunks
def split_text(text, chunk_size, chunk_overlap):
    if chunk_size == 0:
        return []
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
        separator=" ",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    file_content=text_splitter.create_documents([text])
    split_docs = text_splitter.split_documents(file_content)
    return split_docs

# Process the file
def process_file(args):
    file_name = args.file.split(".")[0].split("/")[-1]
    #read file
    with open(args.file, "r",encoding="utf-8") as f:
        file_content = f.read()
    print(f"檔名:{file_name} 文件長度: {len(file_content)}")

    # First map stage
    split_docs1 = split_text(file_content, args.chunk_size_1, args.chunk_overlap_1)
    # Second map stage
    split_docs2 = split_text(file_content, args.chunk_size_2, args.chunk_overlap_2)
    if args.without_map==False:
        print(f"第一階段共{len(split_docs1)}個chunks")
        first_map_results = process_map_results(split_docs1,args)
        # print("Map 1:",first_map_results)

        print(f"第二階段共{len(split_docs2)}個chunks")
        second_map_results = process_map_results(split_docs2,args)
        # print("Map 2:",second_map_results)
        combined_map_results = first_map_results + second_map_results
    else:
        combined_map_results = split_docs1+split_docs2

    
    # Reduce stage
    response=process_reduce_results(combined_map_results,args)

    return response, file_name

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", type=str, default=None, help="OpenAI API key")
    parser.add_argument("--file", type=str, default=None, help="File to summarize")
    parser.add_argument("--model", type=str, default="gpt-4-1106-preview", help="Model to use")
    parser.add_argument("--chunk_size_1", type=int, default=16000, help="Chunk size 1")
    parser.add_argument("--chunk_overlap_1", type=int, default=4000, help="Chunk overlap 1")
    parser.add_argument("--chunk_size_2", type=int, default=8000, help="Chunk size 2")
    parser.add_argument("--chunk_overlap_2", type=int, default=0, help="Chunk overlap 2")
    parser.add_argument("--token_max", type=int, default=16000, help="Token max")
    parser.add_argument("--temperature", type=float, default=0, help="Temperature")
    parser.add_argument("--without_map", action='store_true', help="without use map method")
    parser.add_argument("--output_dir", type=str, default="./cli/output/", help="output path")
    args = parser.parse_args()
        
    if args.file:
        start = time.time()
        response, file_name= process_file(args)
        end=time.time()
        print(f"處理完成!耗時{round(end-start)}秒")

        if not args.without_map:
            file_name = f"{args.output_dir}{file_name}_output_{args.chunk_size_1}_{args.chunk_overlap_1}_{args.chunk_size_2}_{args.chunk_overlap_2}_{args.temperature}.txt"
        else:
            file_name = f"{args.output_dir}{file_name}_output_{args.chunk_size_1}_{args.chunk_overlap_1}_{args.chunk_size_2}_{args.chunk_overlap_2}_{args.temperature}_nomap.txt"
        print(f"輸出檔案: {file_name}")
        print(response)
        #save file
        with open(file_name, "w",encoding="utf-8") as f:
            f.write(response)
if __name__ == "__main__":
    main()
