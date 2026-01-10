import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Box, Typography, Chip, Divider, CircularProgress, Button, IconButton } from '@mui/material';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import TimerIcon from '@mui/icons-material/Timer';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DownloadIcon from '@mui/icons-material/Download';

function ResultSection({ result, loading }) {
    const { summary, processing_time } = result;

    const handleCopy = () => {
        if (!summary) return;
        navigator.clipboard.writeText(summary);
        alert("摘要已複製到剪貼簿");
    };

    const handleDownload = () => {
        if (!summary) return;
        const blob = new Blob([summary], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `摘要_${new Date().toLocaleDateString()}.md`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    if (loading) {
        return (
            <div className="section result-section loading">
                <CircularProgress size={40} sx={{ color: 'var(--primary)', mb: 2 }} />
                <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.7)', fontWeight: 500 }}>
                    正在努力生成摘要中...
                </Typography>
                <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.4)', mt: 1 }}>
                    這通常需要 10-20 秒，請稍候
                </Typography>
            </div>
        );
    }

    return (
        <div className="section result-section">
            {/*標題*/}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <AutoAwesomeIcon sx={{ color: 'var(--primary)', fontSize: 24 }} />
                    <Typography variant="h6" sx={{ color: 'var(--text-main)', fontWeight: 700 }}>摘要結果</Typography>
                </Box>
                {processing_time > 0 && (
                    <Chip 
                        icon={<TimerIcon style={{ color: 'var(--primary)', fontSize: 16 }} />}
                        label={`${processing_time.toFixed(1)}s`} 
                        size="small"
                        sx={{ 
                            background: 'rgba(99, 102, 241, 0.1)', 
                            color: 'rgba(255,255,255,0.7)',
                            border: '1px solid rgba(99, 102, 241, 0.2)'
                        }} 
                    />
                )}
                <Box sx={{ display: 'flex', gap: 1 }}>
                    <IconButton 
                        size="small" 
                        onClick={handleCopy} 
                        disabled={!summary}
                        sx={{ color: 'rgba(255,255,255,0.3)', '&:hover': { color: 'var(--primary)' } }}
                    >
                        <ContentCopyIcon fontSize="small" />
                    </IconButton>
                    <Button 
                        size="small" 
                        variant="outlined"
                        startIcon={<DownloadIcon />}
                        onClick={handleDownload}
                        disabled={!summary}
                        sx={{ 
                            borderRadius: '12px',
                            color: 'var(--primary)', 
                            borderColor: 'rgba(99, 102, 241, 0.3)',
                            fontWeight: 600, 
                            '&:hover': { 
                                borderColor: 'var(--primary)',
                                backgroundColor: 'rgba(99, 102, 241, 0.1)'
                            }
                        }}
                    >
                        儲存摘要 (.md)
                    </Button>
                </Box>
            </Box>
            {/*分隔線*/}
            <Divider sx={{ mb: 0, borderColor: 'rgba(255,255,255,0.05)' }} />

            {/*摘要內容*/}
            <div className="result-content markdown-body">
                {summary ? (
                    <ReactMarkdown>{summary}</ReactMarkdown>
                ) : (
                    <Box sx={{ py: 20, textAlign: 'center' }}>
                        <Typography className="placeholder">
                            請在左側上傳文件並點擊按鈕開始...
                        </Typography>
                    </Box>
                )}
            </div>

            {/*樣式*/}
            <style>{`
                .markdown-body {
                    color: var(--text-main);
                    line-height:1.3;
                    font-size: 1rem;
                }
                .markdown-body h1, .markdown-body h2, .markdown-body h3 {
                    color: var(--primary);
                    margin-top: 0rem;
                    margin-bottom: -2rem;
                }
                .markdown-body ul, .markdown-body ol {
                    padding-left: 2rem;
                    margin-bottom: 0rem;
                }
                .markdown-body li {
                    margin-bottom: 0rem;
                }
                .markdown-body blockquote {
                    border-left: 4px solid var(--primary);
                    padding-left: 1rem;
                    margin-left: 0;
                    color: rgba(255,255,255,0.6);
                }
            `}</style>
        </div>
    );
}

export default ResultSection;
