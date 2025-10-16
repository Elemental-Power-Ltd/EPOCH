import { useEffect, useState } from 'react';

import DataVizContainer from '../src/Components/DataViz/DataViz';
import type { SimulationResult } from '../src/Models/Endpoints.ts';

import { CircularProgress, Alert, Box } from '@mui/material';

export function DataVizFileWrapper() {
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const params    = new URLSearchParams(window.location.search);
  const fileName  = params.get('data') ?? 'defaultData.json';   // Fallback

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
        console.error('Failed to load data', err);
        setError('Failed to load data. Check console logs for details.');
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
      <DataVizContainer result={result} isInformedEmbed={true} />
  );
}
