import {
  TextField,
  Button,
  GridLegacy as Grid,
  Typography,
  MenuItem,
  CircularProgress
} from '@mui/material';
import {ChangeEvent} from 'react';
import {MountType, SolarLocation} from "../../Models/Endpoints.ts";
import {addSolarLocation} from "../../endpoints";

interface AddSolarLocationSectionProps {
  selectedSite: string;
  solarName: string;
  setSolarName: (value: string) => void;
  solarAzimuth: number | null;
  setSolarAzimuth: (value: number | null) => void;
  solarTilt: number | null;
  setSolarTilt: (value: number | null) => void;
  solarMaxPower: number | null;
  setSolarMaxPower: (value: number | null) => void;
  solarMountingType: MountType;
  setSolarMountingType: (value: MountType) => void;
  solarLoading: boolean;
  setSolarLoading: (value: boolean) => void;
  solarError: string | null;
  setSolarError: (value: string | null) => void;
  onSuccess: (message: string) => void;
}

const AddSolarLocationForm = ({
  selectedSite,
  solarName,
  setSolarName,
  solarAzimuth,
  setSolarAzimuth,
  solarTilt,
  setSolarTilt,
  solarMaxPower,
  setSolarMaxPower,
  solarMountingType,
  setSolarMountingType,
  solarLoading,
  setSolarLoading,
  solarError,
  setSolarError,
  onSuccess
}: AddSolarLocationSectionProps) => {

  const handleNumberChange = (setter: (value: number | null) => void) => (e: ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    if (value === "") {
      setter(null);
    } else {
      setter(Number(value));
    }
  };

  const canSubmitSolarLocation = (): boolean => {
    return !!selectedSite && !!solarName && solarMaxPower !== null && !solarLoading;
  }

  const handleAddSolarLocation = async () => {
    if (!canSubmitSolarLocation()) {
      return;
    }

    setSolarLoading(true);
    setSolarError(null);

    const generatedID = selectedSite + "_" + solarName.toLowerCase();

    const solarInfo: SolarLocation = {
      site_id: selectedSite,
      renewables_location_id: generatedID,
      name: solarName,
      azimuth: solarAzimuth,
      tilt: solarTilt,
      maxpower: solarMaxPower,
      mounting_type: solarMountingType
    };

    try {
      const res = await addSolarLocation(solarInfo);

      setSolarLoading(false);
      if (res.success) {
        setSolarError(null);
        const name = res.data!.name;
        onSuccess(`${name} successfully added`);
      } else {
        setSolarError(res.error ?? "Unknown Error");
      }
    } catch (error) {
      setSolarError("Unknown Error");
      setSolarLoading(false);
    }
  }

  return (
    <>
      <Typography variant="h5" gutterBottom mt={2}>
        Add Solar Location
      </Typography>

      <Grid container spacing={2}>
        <Grid item xs={12}>
          <TextField
              fullWidth
              label="Name"
              value={solarName}
              onChange={(e) => setSolarName(e.target.value)}
          />
        </Grid>

        <Grid item xs={12}>
          <TextField
              fullWidth
              label="Azimuth (°)"
              type="number"
              value={solarAzimuth ?? ""}
              onChange={handleNumberChange(setSolarAzimuth)}
          />
        </Grid>

        <Grid item xs={12}>
          <TextField
              fullWidth
              label="Tilt (°)"
              type="number"
              value={solarTilt ?? ""}
              onChange={handleNumberChange(setSolarTilt)}
          />
        </Grid>

        <Grid item xs={12}>
          <TextField
              fullWidth
              label="Max Power (kW)"
              type="number"
              value={solarMaxPower ?? ""}
              onChange={handleNumberChange(setSolarMaxPower)}
          />
        </Grid>

        <Grid item xs={12}>
          <TextField
              fullWidth
              select
              label="Mounting Type"
              value={solarMountingType}
              onChange={(e) => setSolarMountingType(e.target.value as MountType)}
          >
            <MenuItem value="building-integrated">Building integrated</MenuItem>
            <MenuItem value="free">Free</MenuItem>
          </TextField>
        </Grid>

        {solarError && (
          <Grid item xs={12}>
            <Typography variant="body2" color="error">
              {solarError}
            </Typography>
          </Grid>
        )}

        <Grid item xs={12}>
          <Button
              fullWidth
              variant="contained"
              color="primary"
              disabled={!canSubmitSolarLocation()}
              onClick={handleAddSolarLocation}
          >
            {solarLoading ? <CircularProgress size={24}/> : 'Add Solar Location'}
          </Button>
        </Grid>
      </Grid>
    </>
  );
};

export default AddSolarLocationForm;
