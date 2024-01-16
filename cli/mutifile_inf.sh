#執行cli.py 並且輸入參數  
#參數1: 要執行的y 資料及名稱
folder=$1

#按照資料夾底下的檔案名稱執行
for file in $folder/*
do
    echo $file
    python3 cli.py \
    --key "" \
    --file $file \
    --model "gpt-4-1106-preview" \
    --chunk_size_1 16000 \
    --chunk_overlap_1 0 \
    --chunk_size_2 8000 \
    --chunk_overlap_2 0 \
    --token_max 16000 \
    --temperature 0 \
    --without_map \
    --output_dir "./cli/output"
done
