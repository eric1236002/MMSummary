import time
import os
import argparse
import sys
from dotenv import load_dotenv
from langchain.chains import ReduceDocumentsChain
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI

load_dotenv()

# --- Core Logic (Independent Implementation) ---

def init_llm(temperature, model, max_tokens=1000):
    is_new_openai = "o1" in model.lower() or "gpt-5" in model.lower()
    
    # Base parameters
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
                "X-Title": "MMSummary CLI Evaluation"
            },
            **llm_params
        )

def split_text(text, chunk_size, chunk_overlap):
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
        separator=" ",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    file_content = text_splitter.create_documents([text])
    split_docs = text_splitter.split_documents(file_content) 
    return split_docs

def process_map_results(split_docs, model, map_template):
    temp = []
    map_prompt = PromptTemplate.from_template(map_template)
    map_chain = LLMChain(llm=init_llm(0, model, 1000), prompt=map_prompt)

    for doc in split_docs:
        result = map_chain.invoke(doc)
        content = result.get("text", result.get("output", str(result)))
        temp.append(content)
    return temp

def process_reduce_results(combined_map_results, token_max, model, reduce_template, reduce_temperature=0.0):
    reduce_prompt = PromptTemplate.from_template(reduce_template)
    reduce_chain = LLMChain(llm=init_llm(reduce_temperature, model, 4000), prompt=reduce_prompt)

    prompt = PromptTemplate.from_template("Please merge the following content while maintaining logical coherence: {docs}")
    llm_chain = LLMChain(llm=init_llm(0, model, 4000), prompt=prompt)

    collapse_documents_chain = StuffDocumentsChain(llm_chain=llm_chain, document_separator="\n\n")
    combine_documents_chain = StuffDocumentsChain(llm_chain=reduce_chain, document_variable_name="docs")
    reduce_documents_chain = ReduceDocumentsChain(
        combine_documents_chain=combine_documents_chain, 
        collapse_documents_chain=collapse_documents_chain, 
        token_max=token_max
    )
    
    documents = [Document(page_content=content) if isinstance(content, str) else content for content in combined_map_results]
    res = reduce_documents_chain.invoke(documents)
    
    if isinstance(res, dict):
        return res.get("output_text", res.get("text", str(res)))
    return res

# --- CLI ---

def load_template(path, default_content):
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return default_content

def process_file(args):
    if not os.path.exists(args.file):
        print(f"Error: File not found {args.file}")
        return None, None
        
    file_name = os.path.splitext(os.path.basename(args.file))[0]
    with open(args.file, "r", encoding="utf-8") as f:
        file_content = f.read()
    
    # Load Template
    map_template = load_template(args.map_template, "Please summarize the following content:\n\n{docs}")
    reduce_template = load_template(args.reduce_template, "Please integrate the following summaries into a complete conclusion:\n\n{docs}")

    print(f"Mode: {args.mode} | File: {file_name} | Length: {len(file_content)} chars")
    try:
        if args.mode == "direct":
            print("Executing [Direct LLM] mode (using Reduce Template)...")
            full_prompt = reduce_template.replace("{docs}", file_content)
            print(f"Calling model: {args.model} (expected to send {len(full_prompt)} chars)...")
            
            llm = init_llm(args.temperature, args.model, max_tokens=4000)
            response_obj = llm.invoke(full_prompt)
            
            if not response_obj or not response_obj.content:
                print("Error: Model returned empty content")
                return None, file_name
                
            print("Model response successful!")
            return response_obj.content, file_name

        # Split and process
        combined_results = []
        if args.mode in ["map_reduce", "dual_path", "dual_path_no_map"]:
            split_docs1 = split_text(file_content, args.chunk_size_1, args.chunk_overlap_1)
            
            if args.mode == "map_reduce":
                print(f"Executing [Original Map-Reduce] mode (Size: {args.chunk_size_1})...")
                combined_results = process_map_results(split_docs1, args.model, map_template)
            
            elif args.mode == "dual_path":
                print(f"Executing [Dual-Path Map-Reduce] mode (Size: {args.chunk_size_1} & {args.chunk_size_2})...")
                split_docs2 = split_text(file_content, args.chunk_size_2, args.chunk_overlap_2)
                res1 = process_map_results(split_docs1, args.model, map_template)
                res2 = process_map_results(split_docs2, args.model, map_template)
                combined_results = res1 + res2
                
            elif args.mode == "dual_path_no_map":
                print(f"Executing [Dual-Path Without Map] mode...")
                split_docs2 = split_text(file_content, args.chunk_size_2, args.chunk_overlap_2)
                combined_results = split_docs1 + split_docs2

        print(f"Synthesizing results (Reduce)... total {len(combined_results)} chunks")
        response = process_reduce_results(
            combined_results, 
            args.token_max, 
            args.model,
            reduce_template,
            reduce_temperature=args.temperature
        )
    except Exception as e:
        print(f"\n❌ LLM call failed!")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        return None, file_name
    return response, file_name

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, required=True, help="Path to the file to summarize")
    parser.add_argument("--mode", type=str, choices=["map_reduce", "dual_path", "dual_path_no_map", "direct","all"], 
                        default="all", help="Summarization mode")
    parser.add_argument("--model", type=str, default="google/gemini-2.5-flash-lite", help="Model to use")
    parser.add_argument("--map_template", type=str, default="template/booksum_map.txt", help="Path to Map stage template")
    parser.add_argument("--reduce_template", type=str, default="template/booksum_reduce.txt", help="Path to Reduce stage template")
    parser.add_argument("--chunk_size_1", type=int, default=8000, help="Path 1 chunk size")
    parser.add_argument("--chunk_overlap_1", type=int, default=2000, help="Path 1 overlap size")
    parser.add_argument("--chunk_size_2", type=int, default=4000, help="Path 2 chunk size")
    parser.add_argument("--chunk_overlap_2", type=int, default=0, help="Path 2 overlap size")
    parser.add_argument("--token_max", type=int, default=10000, help="Token limit")
    parser.add_argument("--temperature", type=float, default=0.0, help="Model temperature")
    parser.add_argument("--output_dir", type=str, default="./cli/output/", help="Output directory")
    args = parser.parse_args()

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    start_time = time.time()
    try:
        if args.mode == "all":
            for mode in ["map_reduce", "dual_path", "dual_path_no_map", "direct"]:
                args.mode = mode
                response, file_name = process_file(args)
                duration = time.time() - start_time
                if response:
                    output_file = os.path.join(args.output_dir, f"{file_name}_{args.mode}_{args.model.replace('/', '_')}.txt")
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(response)
                    print(f"\n✅ [{mode}] Processing complete! Duration: {round(duration, 1)}s | Saved")
                else:
                    print(f"\n❌ [{mode}] Processing failed, skipping save.")
        else:
            response, file_name = process_file(args)
            duration = time.time() - start_time
            if response:
                output_file = os.path.join(args.output_dir, f"{file_name}_{args.mode}_{args.model.replace('/', '_')}.txt")
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(response)
                print(f"\n✅ Processing complete! Duration: {round(duration, 1)}s | Result saved to: {output_file}")
            else:
                print(f"\n❌ Processing failed, no output generated.")
    except Exception as fatal_e:
        print(f"\n🚨 Fatal error occurred!")
        print(f"Error content: {str(fatal_e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
