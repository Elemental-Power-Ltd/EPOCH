import { FC } from "react";
import {
  Alert,
  Box,
  Button,
  Paper,
  Stack,
  Typography,
} from "@mui/material";

import { CostModelResponse } from "../../Models/Endpoints.ts"

// Splash screens to indicate success & error for the cost model


type SuccessScreenProps = {
  model: CostModelResponse;
  onBack: () => void;
};

export const CostModelSaveSuccess: FC<SuccessScreenProps> = ({ model, onBack }) => {
  return (
    <Paper variant="outlined" sx={{ p: 3 }}>
      <Stack spacing={2} alignItems="flex-start">
        <Typography variant="h5">Cost Model Saved</Typography>
        <Typography variant="body1" color="text.secondary">
          Saved <strong>{model.model_name ?? "(Unnamed)"}</strong>
        </Typography>

        <Box>
          <Button variant="outlined" onClick={onBack}>
            Back
          </Button>
        </Box>
      </Stack>
    </Paper>
  );
};

type ErrorScreenProps = {
  error: string;
  onBack: () => void;
};

export const CostModelSaveError: FC<ErrorScreenProps> = ({ error, onBack }) => {
  return (
    <Paper variant="outlined" sx={{ p: 3 }}>
      <Stack spacing={2} alignItems="flex-start">
        <Typography variant="h5">Save Failed</Typography>
        <Alert severity="error">{error}</Alert>

        <Box>
          <Button variant="outlined" onClick={onBack}>
            Back
          </Button>
        </Box>
      </Stack>
    </Paper>
  );
};