import {ChangeEvent} from 'react';
import {
  Button,
  GridLegacy as Grid,
  Typography,
  CircularProgress
} from '@mui/material';
import {uploadPhpp} from '../../endpoints';
import {PhppMetadata} from "../../Models/Endpoints.ts";

interface UploadPhppFormProps {
  selectedClient: any;
  selectedSite: string;
  phppFile: File | null;
  setPhppFile: (file: File | null) => void;
  phppLoading: boolean;
  setPhppLoading: (value: boolean) => void;
  phppError: string | null;
  setPhppError: (value: string | null) => void;
  phppMetadata: PhppMetadata | null;
  setPhppMetadata: (value: PhppMetadata | null) => void;
  onSuccess: (message: string) => void;
}

const UploadPhppForm = ({
  selectedClient,
  selectedSite,
  phppFile,
  setPhppFile,
  phppLoading,
  setPhppLoading,
  phppError,
  setPhppError,
  phppMetadata,
  setPhppMetadata,
  onSuccess,
}: UploadPhppFormProps) => {

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setPhppFile(e.target.files[0]);
    } else {
      setPhppFile(null);
    }
  };

  const canSubmitPhpp = (): boolean => {
    return phppFile !== null && selectedClient !== null && selectedSite !== "" && !phppLoading;
  }

  const handlePhppUpload = async () => {
    if (!canSubmitPhpp()) {
      return;
    }

    setPhppLoading(true);
    setPhppError(null);
    setPhppMetadata(null);

    try {
      const res = await uploadPhpp(phppFile!, selectedSite);

      setPhppLoading(false);
      if (res.success) {
        setPhppError(null);
        setPhppMetadata(res.data ?? null);
        onSuccess("PHPP upload successfully!");
      } else {
        setPhppError(res.error ?? "Unknown Error");
      }
    } catch (error) {
      setPhppError("Unknown Error");
      setPhppLoading(false);
    }
  }

  return (
    <>
      <Typography variant="h5" gutterBottom mt={2}>
        Upload PHPP
      </Typography>

      <Grid container spacing={2}>
        <Grid item xs={12}>
          <Button variant="outlined" component="label" fullWidth>
            {phppFile ? `Selected: ${phppFile.name}` : 'Select a PHPP file'}
            <input
              type="file"
              hidden
              onChange={handleFileChange}
            />
          </Button>
        </Grid>

        {phppError && (
          <Grid item xs={12}>
            <Typography variant="body2" color="error">
              {phppError}
            </Typography>
          </Grid>
        )}

        {phppMetadata && (
          <Grid item xs={12}>
            <Typography variant="body2">
              Uploaded structure ID: {phppMetadata.structure_id}, floor area: {phppMetadata.floor_area} m²
            </Typography>
          </Grid>
        )}

        <Grid item xs={12}>
          <Button
              fullWidth
              variant="contained"
              color="primary"
              disabled={!canSubmitPhpp()}
              onClick={handlePhppUpload}
          >
            {phppLoading ? <CircularProgress size={24}/> : 'Upload PHPP'}
          </Button>
        </Grid>
      </Grid>
    </>
  );
};

export default UploadPhppForm;
