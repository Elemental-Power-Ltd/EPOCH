import {ChangeEvent} from 'react';
import {
  TextField,
  Button,
  Grid,
  Typography,
  MenuItem,
  CircularProgress
} from '@mui/material';
import {FuelType} from "../../Models/Endpoints.ts";
import {uploadMeterFile} from '../../endpoints';

interface UploadMeterFileSectionProps {
  selectedClient: any;
  selectedSite: string;
  fuelType: FuelType;
  setFuelType: (value: FuelType) => void;
  file: File | null;
  setFile: (file: File | null) => void;
  meterFileLoading: boolean;
  setMeterFileLoading: (value: boolean) => void;
  meterFileError: string | null;
  setMeterFileError: (value: string | null) => void;
}

const UploadMeterFileForm = ({
  selectedClient,
  selectedSite,
  fuelType,
  setFuelType,
  file,
  setFile,
  meterFileLoading,
  setMeterFileLoading,
  meterFileError,
  setMeterFileError
}: UploadMeterFileSectionProps) => {

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    } else {
      setFile(null);
    }
  };

  const canSubmitMeterFile = (): boolean => {
    return file !== null && selectedClient !== null && selectedSite !== "";
  }

  const handleMeterFileUpload = async () => {
    if (!canSubmitMeterFile()) {
      return;
    }

    setMeterFileLoading(true);
    setMeterFileError(null);

    try {
      const res = await uploadMeterFile(file!, selectedSite, fuelType);

      setMeterFileLoading(false);
      if (res.success) {
        setMeterFileError(null);
      } else {
        setMeterFileError(res.error ?? "Unknown Error");
      }

    } catch (error) {
      setMeterFileError("Unknown Error");
      setMeterFileLoading(false);
    }
  }

  return (
    <>
      <Typography variant="h5" gutterBottom mt={2}>
        Upload Meter File
      </Typography>

      <Grid container spacing={2}>
        <Grid item xs={12}>
          <TextField
              fullWidth
              select
              label="Fuel Type"
              value={fuelType}
              onChange={(e) => setFuelType(e.target.value as FuelType)}
          >
            <MenuItem value="">
              <em>Select fuel type</em>
            </MenuItem>
            <MenuItem value="gas">Gas</MenuItem>
            <MenuItem value="elec">Elec</MenuItem>
          </TextField>
        </Grid>

        <Grid item xs={12}>
          <Button variant="outlined" component="label" fullWidth>
            {file ? `Selected: ${file.name}` : 'Select a file'}
            <input
              type="file"
              hidden
              onChange={handleFileChange}
            />
          </Button>
        </Grid>
      </Grid>

      <Grid item xs={12}>
        <Button
            fullWidth
            variant="contained"
            color="primary"
            disabled={!canSubmitMeterFile()}
            onClick={handleMeterFileUpload}
        >
          {meterFileLoading ? <CircularProgress size={24}/> : 'Upload'}
        </Button>
      </Grid>

      {meterFileError && (
          <Grid item xs={12}>
            <Typography variant="body2" color="error">
              {meterFileError}
            </Typography>
          </Grid>
      )}

    </>
  );
};

export default UploadMeterFileForm;
