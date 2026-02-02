import { useEffect, useState } from 'react';

import {SiteDataViewer} from "../src/Components/SiteData/SiteDataViewer";
import {SiteDataWithHints} from "../src/Models/Endpoints";

import { CircularProgress, Alert, Box } from '@mui/material';

export function SiteDataFileWrapper() {
  const [site, setSite] = useState<SiteDataWithHints | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const params    = new URLSearchParams(window.location.search);
  const fileName  = params.get('site') ?? 'defaultSite.json';   // Fallback

  useEffect(() => {
    setLoading(true);
    setError(null);

    fetch(fileName)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setSite)
      .catch(err => {
        console.error('Failed to load site', err);
        setError('Failed to load site. Check console logs for details.');
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

  if (error || !site) {
    return (
      <Box m={2}>
        <Alert severity="error">{error ?? 'No data found'}</Alert>
      </Box>
    );
  }

  return (
      <SiteDataViewer siteData={site.siteData} hints={site.hints}/>
  );
}
