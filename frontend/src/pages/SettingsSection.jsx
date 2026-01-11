import React from 'react';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Slider,
  Typography,
  Switch,
  FormControlLabel
} from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import SettingsIcon from '@mui/icons-material/Settings';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#6366f1' },
  },
});

function SettingsSection({ settings, onChange, t }) {
  const handleChange = (key, value) => {
    const newSettings = { ...settings, [key]: value };
    onChange(newSettings);
    console.log("Settings Updated:", newSettings);
  };

  return (
    <ThemeProvider theme={darkTheme}>
      <Box className="settings-container" sx={{ width: '100%', maxWidth: 800, mx: 'auto', p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 4 }}>
          <SettingsIcon sx={{ fontSize: 32, color: 'var(--primary)' }} />
          <Typography variant="h4" sx={{ fontWeight: 800, background: 'linear-gradient(45deg, var(--primary), var(--secondary))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            {t.title}
          </Typography>
        </Box>

        <Box className="section settings-section" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>

          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
            <FormControl fullWidth>
              <InputLabel id="language-select-label">{t.language}</InputLabel>
              <Select
                labelId="language-select-label"
                label={t.language}
                value={settings.language}
                onChange={(e) => handleChange('language', e.target.value)}
                sx={{ borderRadius: '12px' }}
              >
                <MenuItem value="zh">繁體中文</MenuItem>
                <MenuItem value="en">English</MenuItem>
              </Select>
            </FormControl>

            <FormControl fullWidth>
              <TextField
                label={t.model}
                type="text"
                value={settings.model}
                onChange={(e) => handleChange('model', e.target.value)}
                slotProps={{ input: { sx: { borderRadius: '12px' } } }}
              />
            </FormControl>
          </Box>

          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
            <TextField
              label={t.chunkSize1}
              type="number"
              value={settings.chunk_size_1}
              onChange={(e) => handleChange('chunk_size_1', parseInt(e.target.value) || 0)}
              slotProps={{ input: { sx: { borderRadius: '12px' } } }}
            />
            <TextField
              label={t.chunkSize2}
              type="number"
              value={settings.chunk_size_2}
              onChange={(e) => handleChange('chunk_size_2', parseInt(e.target.value) || 0)}
              slotProps={{ input: { sx: { borderRadius: '12px' } } }}
            />
          </Box>

          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr', gap: 2 }}>
            <TextField
              label={t.tokenMax}
              type="number"
              value={settings.token_max}
              onChange={(e) => handleChange('token_max', parseInt(e.target.value) || 0)}
              slotProps={{ input: { sx: { borderRadius: '12px' } } }}
            />
          </Box>

          <Box sx={{ px: 1 }}>
            <Typography gutterBottom variant="caption">{t.temperature}: {settings.temperature}</Typography>
            <Slider
              value={settings.temperature}
              min={0}
              max={2}
              step={0.1}
              marks
              valueLabelDisplay="auto"
              onChange={(e, val) => handleChange('temperature', val)}
            />
          </Box>

          <Box sx={{ px: 1 }}>
            <Typography gutterBottom variant="caption">{t.reduceTemperature}: {settings.reduce_temperature}</Typography>
            <Slider
              value={settings.reduce_temperature}
              min={0}
              max={2}
              step={0.1}
              marks
              valueLabelDisplay="auto"
              onChange={(e, val) => handleChange('reduce_temperature', val)}
            />
          </Box>

          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr', gap: 2 }}>
            <FormControl fullWidth>
              <InputLabel id="strategy-select-label">{t.strategy}</InputLabel>
              <Select
                labelId="strategy-select-label"
                label={t.strategy}
                value={settings.strategy}
                onChange={(e) => handleChange('strategy', e.target.value)}
                sx={{ borderRadius: '12px' }}
              >
                <MenuItem value="map">Map-Reduce</MenuItem>
                <MenuItem value="nomap">NoMap-Reduce</MenuItem>
                <MenuItem value="original">Original</MenuItem>
              </Select>
            </FormControl>
          </Box>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label={t.mapTemplate}
              multiline
              rows={4}
              value={settings.map_temple}
              onChange={(e) => handleChange('map_temple', e.target.value)}
              placeholder={t.placeholderTemplate}
              slotProps={{ input: { sx: { borderRadius: '12px' } } }}
            />
            <TextField
              label={t.reduceTemplate}
              multiline
              rows={4}
              value={settings.reduce_temple}
              onChange={(e) => handleChange('reduce_temple', e.target.value)}
              placeholder={t.placeholderTemplate}
              slotProps={{ input: { sx: { borderRadius: '12px' } } }}
            />
          </Box>

          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr', gap: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.test_mode}
                  onChange={(e) => handleChange('test_mode', e.target.checked)}
                  color="primary"
                />
              }
              label={
                <Box>
                  <Typography variant="body1" sx={{ color: 'var(--text-main)' }}>{t.testMode}</Typography>
                  <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.5)' }}>{t.testModeDesc}</Typography>
                </Box>
              }
            />
          </Box>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default SettingsSection;