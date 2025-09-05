import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom/client';

import DataVizContainer from '../src/Components/DataViz/DataViz';
import type { SimulationResult } from '../src/Models/Endpoints.ts';
import AppTheme from "../src/AppTheme";

import { CircularProgress, Alert, Box } from '@mui/material';

function DataVizFileWrapper() {
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const params    = new URLSearchParams(window.location.search);
  const fileName  = params.get('data') ?? 'defaultData.json';   // Fallback


  // query param for the theme
  const mode = params.get('mode') ?? '0';

  // 0 - isInformedEmbed, isDarkMode
  // 1 - isInformedEmbed, !isDarkMode
  // 2 - !isInformedEmbed, isDarkMode
  // 3 - !isInformedEmbed, !isDarkMode
  const isDarkMode = mode === '0' || mode === '2';
  const isInformedTheme = mode === '0' || mode === '1';

  useEffect(() => {
    setLoading(true);
    setError(null);

    fetch(fileName)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setResult)
      .catch(err => {
        console.error('Failed to load file', err);
        setError('Failed to load file. Check console logs for details.');
      })
      .finally(() => setLoading(false));
  }, [fileName]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error || !result) {
    return (
      <Box m={2}>
        <Alert severity="error">{error ?? 'No data found'}</Alert>
      </Box>
    );
  }

  return (
      <AppTheme isDarkMode={isDarkMode} isInformedEmbed={isInformedTheme}>
          <DataVizContainer result={result} isInformedEmbed={true} />
      </AppTheme>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <DataVizFileWrapper />
    </React.StrictMode>
);
