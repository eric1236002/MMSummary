# Cli interface
single file use cli interface
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
If you want to input multiple files, you can use the following command
```
bash mutifile_inf.sh /PATH/file folder
```

## Evaluation
```
python3 ./cli/eval.py \
    --orginal_file file \
    --summary_file file2 \
    --output_dir result_file
```

If you want to input multiple files, you can use the following command
```
bash mutifile_eval.sh /PATH/output folder
```