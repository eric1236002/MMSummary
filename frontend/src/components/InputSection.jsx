import React from 'react';

function InputSection({ onTextLoad }) {

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            const text = event.target.result;
            onTextLoad(text);
        };

        reader.readAsText(file);
        console.log("File selected:", file.name);
    };

    return (
        <div className="input-content-wrapper">
            <h2>上傳文件</h2>
            <input
                type="file"
                accept=".txt,.md"
                onChange={handleFileChange}
            />
            <p className="hint">僅支援 .txt 和 .md 檔案</p>
        </div>
    );
}

export default InputSection;
