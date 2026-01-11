import React, { useEffect, useState } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import {
  Box,
  Typography,
  Card,
  CardContent,
  IconButton,
  CircularProgress,
  Divider,
  Chip,
  Stack,
  Collapse,
  Button
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DownloadIcon from '@mui/icons-material/Download';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import HistoryIcon from '@mui/icons-material/History';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import { styled } from '@mui/material/styles';

const ExpandMore = styled((props) => {
  const { expand, ...other } = props;
  return <IconButton {...other} />;
})(({ theme, expand }) => ({
  transform: !expand ? 'rotate(0deg)' : 'rotate(180deg)',
  marginLeft: 'auto',
  transition: theme.transitions.create('transform', {
    duration: theme.transitions.duration.shortest,
  }),
}));

function HistoryPage({ t }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);

  const fetchHistory = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:8001/history');
      setHistory(response.data);
    } catch (err) {
      console.error("Failed to fetch history:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleDelete = async (id) => {
    if (!window.confirm(t.confirm_delete)) return;
    try {
      await axios.delete(`http://127.0.0.1:8001/history/${id}`);
      setHistory(history.filter(item => item.id !== id));
      alert(t.deleteSuccess);
    } catch (err) {
      console.error("Delete failed:", err);
      alert("Error deleting record");
    }
  };

  const handleExpandClick = (id) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const handleCopy = (id) => {
    const summary = history.find(item => item.id === id)?.summary;
    if (!summary) return;
    navigator.clipboard.writeText(summary);
    alert(t.copySuccess);
  };

  const handleDownload = (id) => {
    const summary = history.find(item => item.id === id)?.summary;
    if (!summary) return;
    const blob = new Blob([summary], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${t.downloadName}_${new Date().toLocaleDateString()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}>
        <CircularProgress sx={{ color: 'var(--primary)' }} />
      </Box>
    );
  }

  return (
    <Box className="history-container" sx={{ width: '100%', maxWidth: 800, mx: 'auto', p: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 4 }}>
        <HistoryIcon sx={{ fontSize: 32, color: 'var(--primary)' }} />
        <Typography variant="h4" sx={{ fontWeight: 800, background: 'linear-gradient(45deg, var(--primary), var(--secondary))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          {t.nav_history}
        </Typography>
      </Box>

      {history.length === 0 ? (
        <Box className="section" sx={{ textAlign: 'center', py: 8 }}>
          <Typography color="var(--text-main)">{t.noHistory}</Typography>
        </Box>
      ) : (
        <Stack spacing={2}>
          {history.map((item) => (
            <Card key={item.id} className="section" sx={{
              background: 'var(--bg-card)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255,255,255,0.05)',
              borderRadius: '20px',
              transition: 'transform 0.2s',
              '&:hover': { transform: 'translateY(-4px)' }
            }}>
              <CardContent>
                {/*上方資訊*/}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2  }}>
                  <Box>
                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.5)', display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
                      <AccessTimeIcon sx={{ fontSize: 14 }} />
                      {item.created_at}
                    </Typography>
                    <Stack direction="row" spacing={1}>
                      <Chip
                        label={item.model}
                        size="small"
                        sx={{ bgcolor: 'rgba(20, 21, 83, 0.1)', color: 'var(--primary)', border: '1px solid rgba(99, 102, 241, 0.2)' }}
                      />
                      <Chip
                        label={`${item.processing_time.toFixed(1)}s`}
                        size="small"
                        variant="outlined"
                        sx={{ color: 'rgba(255,255,255,0.6)', borderColor: 'rgba(255,255,255,0.1)' }}
                      />
                    </Stack>
                  </Box>
                  {/* 按鈕群組 */}
                  <Stack direction="row" spacing={0.5}>
                    <IconButton
                      size="small"
                      onClick={() => handleCopy(item.id)}
                      aria-label={t.copy}
                      sx={{ color: 'rgba(255,255,255,0.3)', '&:hover': { color: 'var(--primary)' } }}
                    >
                      <ContentCopyIcon fontSize="small" />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleDownload(item.id)}
                      aria-label={t.downloadName}
                      sx={{ color: 'rgba(255,255,255,0.3)', '&:hover': { color: 'var(--primary)' } }}
                    >
                      <DownloadIcon fontSize="small" />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleDelete(item.id)}
                      aria-label={t.delete}
                      sx={{ color: 'rgba(255,255,255,0.3)', '&:hover': { color: '#ef4444' } }}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Stack>
                </Box>

                {/*摘要*/}
                <Box
                  sx={{
                    color: 'var(--text-main)',
                    mb: 0,
                    display: '-webkit-box',
                    WebkitLineClamp: expandedId === item.id ? 'unset' : 2,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                    lineHeight: 1.4,
                    '& h1, & h2, & h3, & h4, & h5, & h6': { mb: 1 },
                    '& p': { mb: 1, mt: 0 },
                    '& ul, & ol': { pl: 3, mb: 1 },
                    '& li': { mb: 0.5 },
                    fontSize: '0.95rem'
                  }}
                >
                  <ReactMarkdown>{item.summary}</ReactMarkdown>
                </Box>


                {/*按鈕*/}
                <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <Button
                    size="small"
                    onClick={() => handleExpandClick(item.id)}
                    endIcon={<ExpandMoreIcon sx={{ transform: expandedId === item.id ? 'rotate(180deg)' : 'none', transition: '0.3s' }} />}
                    sx={{ color: 'var(--primary)', fontWeight: 600 }}
                  >
                    {expandedId === item.id ? t.collapse_content : t.expand_content}
                  </Button>
                </Box>

                {/*原始文本*/}
                <Collapse in={expandedId === item.id}>
                  <Divider sx={{ my: 2, borderColor: 'rgba(255,255,255,0.05)' }} />
                  <Typography variant="subtitle2" sx={{ color: 'var(--primary)', mb: 1, fontWeight: 700 }}>{t.originalText} (First 200 chars):</Typography>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.5)', fontStyle: 'italic', lineHeight: 1.5 }}>
                    {item.original_text.substring(0, 200)}...
                  </Typography>
                </Collapse>
              </CardContent>
            </Card>
          ))}
        </Stack>
      )}
    </Box>
  );
}

export default HistoryPage;