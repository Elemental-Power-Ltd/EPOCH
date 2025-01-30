import React, {useState, FC} from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    SelectChangeEvent
} from '@mui/material';
import {Site} from "../../State/types";

interface AddSiteModalProps {
  open: boolean;
  onClose: () => void;
  availableSites: Site[];
  onAddSite: (siteId: string) => void;
}

const AddSiteModal: FC<AddSiteModalProps> = ({
  open,
  onClose,
  availableSites,
  onAddSite
}) => {
  const [selectedSite, setSelectedSite] = useState<string>('');

  const handleSelectChange = (event: SelectChangeEvent<string>) => {
    setSelectedSite(event.target.value);
  };

  const handleConfirm = () => {
    if (selectedSite) {
      onAddSite(selectedSite);
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>Select a Site</DialogTitle>
      <DialogContent>
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
          Confirm
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AddSiteModal;
