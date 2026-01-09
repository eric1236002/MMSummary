import React from 'react';
import ReactMarkdown from 'react-markdown'; // 如果你想支援 Markdown 顯示 (需安裝: npm install react-markdown)

function ResultSection({ content, loading }) {

    if (loading) {
        return (
            <div className="section result-section loading">
                <div className="spinner"></div>
                <p>正在努力生成摘要中...</p>
            </div>
        );
    }

    return (
        <div className="section result-section">
            <h2>摘要結果</h2>
            <div className="result-content">
                {content ? (
                    <pre>{content}</pre>
                ) : (
                    <p className="placeholder">結果將顯示於此...</p>
                )}
            </div>
        </div>
    );
}

export default ResultSection;
