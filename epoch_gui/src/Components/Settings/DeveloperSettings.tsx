import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormGroup,
  FormControlLabel,
  Switch,
  Stack,
  Typography,
  Button,
} from '@mui/material';

type Props = {
  open: boolean;
  onClose: () => void;
  isDarkMode: boolean;
  setIsDarkMode: (value: boolean) => void;
  isInformedEmbed: boolean;
  setIsInformedEmbed: (value: boolean) => void;
};

export default function DeveloperSettings({
  open,
  onClose,
  isDarkMode,
  setIsDarkMode,
  isInformedEmbed,
  setIsInformedEmbed,
}: Props) {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle>Developer Settings</DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2}>
          <Typography variant="body2" color="text.secondary">
            Toggle runtime flags for theming and embed mode.
          </Typography>
          <FormGroup>
            <FormControlLabel
              control={
                <Switch
                  checked={isDarkMode}
                  onChange={(e) => setIsDarkMode(e.target.checked)}
                />
              }
              label="Dark mode"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={isInformedEmbed}
                  onChange={(e) => setIsInformedEmbed(e.target.checked)}
                />
              }
              label="Informed mode"
            />
          </FormGroup>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}
