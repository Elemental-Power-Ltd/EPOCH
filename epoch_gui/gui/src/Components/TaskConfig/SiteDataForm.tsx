import React from "react";
import { Grid, TextField, MenuItem } from "@mui/material";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { DateTimePicker } from "@mui/x-date-pickers/DateTimePicker";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";

dayjs.extend(utc);

interface SiteDataFormProps {
  siteId: string;
  onSiteChange: (value: string) => void;
  startDate: string; // or null
  onStartDateChange: (value: string) => void;
  timestepMinutes: number;
  onTimestepChange: (value: number) => void;
  clientSites: { site_id: string; name: string }[];
}

const SiteDataForm: React.FC<SiteDataFormProps> = ({
  siteId,
  onSiteChange,
  startDate,
  onStartDateChange,
  timestepMinutes,
  onTimestepChange,
  clientSites,
}) => {
  return (
    <Grid container spacing={2}>
      {/* Site Select */}
      <Grid item xs={12}>
        <TextField
          fullWidth
          select
          label="Site"
          value={siteId}
          onChange={(e) => onSiteChange(e.target.value)}
          required
        >
          {clientSites.map((site) => (
            <MenuItem value={site.site_id} key={site.site_id}>
              {site.name}
            </MenuItem>
          ))}
        </TextField>
      </Grid>

      {/* Start Date */}
      <Grid item xs={6}>
        <LocalizationProvider dateAdapter={AdapterDayjs}>
          <DateTimePicker
            label="Start Date"
            value={startDate ? dayjs(startDate).utc() : null}
            onChange={(date) =>
              onStartDateChange(date?.utc().toISOString() ?? "")
            }
          />
        </LocalizationProvider>
      </Grid>

      {/* Timestep */}
      <Grid item xs={6}>
        <TextField
          fullWidth
          select
          label="Timestep"
          value={timestepMinutes}
          onChange={(e) => onTimestepChange(Number(e.target.value))}
          required
        >
          <MenuItem value={60}>60 Minutes</MenuItem>
          <MenuItem value={30}>30 Minutes</MenuItem>
        </TextField>
      </Grid>
    </Grid>
  );
};

export default SiteDataForm;
