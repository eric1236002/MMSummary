#執行eval.py 並且輸入參數  
#參數1: 要執行的y 資料及名稱
orginal=$1
summary=$2
output=$3
#按照資料夾底下的檔案名稱執行
for file in $orginal/*
do
    # 從完整路徑中取出檔案名稱並移除副檔名
    basefile=$(basename "$file")
    filename="${basefile%.*}"
    #找出folder2中開頭file.split('/')[-1].split('.')[0]的檔案
    for file2 in $summary/*
    do
        # 從完整路徑中取出檔案名稱
        basefile2=$(basename "$file2")
        if [[ $basefile2 == $filename* ]]
        then
            echo $file
            echo $file2
            python3 eval.py \
            --orginal_file $file \
            --summary_file $file2 \
            --output_dir $output 
        fi
    done
done