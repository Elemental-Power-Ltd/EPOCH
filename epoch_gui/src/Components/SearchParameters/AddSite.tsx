import { useState, FC } from 'react';
import {
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
} from '@mui/material';
import { Site } from '../../State/types';
import {getSiteBaseline} from "../../endpoints.tsx";

interface AddSiteModalProps {
  open: boolean;
  onClose: () => void;
  availableSites: Site[];
  onAddSite: (siteId: string, baseline: any) => void;
}

const AddSiteModal: FC<AddSiteModalProps> = ({
  open,
  onClose,
  availableSites,
  onAddSite
}) => {
  const [selectedSite, setSelectedSite] = useState<string>(availableSites.length === 1 ? availableSites[0].site_id : '');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSelectChange = (event: SelectChangeEvent<string>) => {
    setSelectedSite(event.target.value);
    if (error) {
      setError(null);
    }
  };

  const handleConfirm = async () => {
    if (!selectedSite) return;
    try {
      setLoading(true);
      setError(null);

      const baselineResponse = await getSiteBaseline(selectedSite);

      if (baselineResponse.success) {
        onAddSite(selectedSite, baselineResponse.data);
        onClose();
      } else {
        setError(baselineResponse.error ?? "Unknown error");
      }
    } catch (err: any) {
      setError(err.message ?? "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={loading ? undefined : onClose}>
      <DialogTitle>Select a Site</DialogTitle>

      {/* When loading, show a spinner */}
      {loading ? (
        <DialogContent sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
          <CircularProgress />
        </DialogContent>
      ) : (
        <>
          <DialogContent>
            {error && <Alert severity="error">{error}</Alert>}

            <FormControl fullWidth>
              <InputLabel id="site-select-label">Site</InputLabel>
              <Select
                labelId="site-select-label"
                value={selectedSite}
                label="Site"
                onChange={handleSelectChange}
              >
                {availableSites.map(site => (
                  <MenuItem key={site.site_id} value={site.site_id}>
                    {site.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </DialogContent>
          <DialogActions>
            <Button onClick={onClose}>Cancel</Button>
            <Button
              onClick={handleConfirm}
              color="primary"
              variant="contained"
              disabled={!selectedSite}
            >
              {error ? "Retry" : "Confirm"}
            </Button>
          </DialogActions>
        </>
      )}
    </Dialog>
  );
};

export default AddSiteModal;
