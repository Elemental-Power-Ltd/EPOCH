import { useState } from 'react';
import {
  TextField,
  Button,
  Grid,
  Container,
  Typography,
  MenuItem,
  CircularProgress
} from '@mui/material';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs, {Dayjs} from 'dayjs';
import 'dayjs/locale/en-gb';
import utc from 'dayjs/plugin/utc';

import { useEpochStore } from '../State/Store';
import { generateAllData } from '../endpoints';

dayjs.extend(utc);

const DatasetGenerationContainer = () => {

  const selectedClient = useEpochStore((state) => state.global.selectedClient);
  const sites = useEpochStore((state) => state.global.client_sites);

  const [selectedSite, setSelectedSite] = useState('');
  const [startDate, setStartDate] = useState<Dayjs | null>(dayjs("2022-01-01T00:00:00Z"));
  const [endDate, setEndDate] = useState<Dayjs | null>(dayjs("2023-01-01T00:00:00Z"));
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationResult, setGenerationResult] = useState<any>(null);

  const handleGenerateDataset = async () => {
    setIsGenerating(true);
    setGenerationResult(null);
    try {
      const result = await generateAllData(
        selectedSite,
        startDate!.utc().format('YYYY-MM-DDTHH:mm:ss[Z]'),
        endDate!.utc().format('YYYY-MM-DDTHH:mm:ss[Z]')
      );
      setGenerationResult(result);
    } catch (error) {
      setGenerationResult({ error: 'Failed to generate dataset' });
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Typography variant="h4" gutterBottom>
        Generate Dataset
      </Typography>
      <Grid container spacing={2}>
        <Grid item xs={12}>
          <TextField
            fullWidth
            select
            label="Site"
            value={selectedSite}
            onChange={(e) => setSelectedSite(e.target.value)}
            disabled={!selectedClient}
          >
            {sites.map((site) => (
              <MenuItem key={site.site_id} value={site.site_id}>
                {site.name}
              </MenuItem>
            ))}
          </TextField>
        </Grid>
        <Grid item xs={6}>
          <LocalizationProvider dateAdapter={AdapterDayjs} adapterLocale={"en-gb"}>
            <DateTimePicker
              label="Start Date"
              value={startDate}
              onChange={(date) => setStartDate(date)}
            />
          </LocalizationProvider>
        </Grid>
        <Grid item xs={6}>
          <LocalizationProvider dateAdapter={AdapterDayjs}>
            <DateTimePicker
              label="End Date"
              value={endDate}
              onChange={(date) => setEndDate(date)}
            />
          </LocalizationProvider>
        </Grid>
        <Grid item xs={12}>
          <Button
            fullWidth
            variant="contained"
            color="primary"
            onClick={handleGenerateDataset}
            disabled={!selectedSite || isGenerating}
          >
            {isGenerating ? <CircularProgress size={24} /> : 'Generate Dataset'}
          </Button>
        </Grid>
        {generationResult && (
          <Grid item xs={12}>
            <Typography variant="body1">
              {generationResult.error
                ? `Error: ${generationResult.error}`
                : `Dataset generated successfully: ${JSON.stringify(generationResult)}`}
            </Typography>
          </Grid>
        )}
      </Grid>
    </Container>
  );
};

export default DatasetGenerationContainer;