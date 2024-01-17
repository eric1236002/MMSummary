# MMSummary

In this project, three different methods can be used to extract article abstracts. 

For example, frist we cut the document using two different chunk sizes, merge the results into a single file, and then use the reduce chain for output.

Secondly, we use the file's map chain twice to extract each chunck's summary and then use the reduce chain to output.

Finally, we use the file's map chain once to extract the summary of the entire file and then use the reduce chain to output.


<!-- 插入圖片LLM.png -->

![struct](jpg/LLM.png)

## Environment
Install requirements
```
conda create -n MMSummary python=3.10
conda activate MMSummary
pip install -r requirements.txt
```

create .env file in the directory
```
OPENAI_API_KEY=<Your_API_KEY>
```

## Prompt file

map_template and reduce_template is the prompt template file for the LLM.

## Run
```
streamlit run ./web.py
```

![web](jpg/web.jpg)
## Command-Line Interface
If you want to use cli, you can use the following command
```
python3 ./cli/cli.py \
    --key "" \ opai key
    --file <your file name> \
    --model "gpt-4-1106-preview" \
    --chunk_size_1 16000 \
    --chunk_overlap_1 0 \
    --chunk_size_2 8000 \
    --chunk_overlap_2 0 \
    --token_max 16000 \
    --temperature 0 \
    --without_map \
    --output_dir "./cli/output/"
```
## Command-Line Interface Evaluation
``` 
python3 ./cli/eval.py \
    --orginal_file file \
    --summary_file file2 \
    --output_dir result_file