import React from "react";
import { Grid, TextField, MenuItem } from "@mui/material";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { DateTimePicker } from "@mui/x-date-pickers/DateTimePicker";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";
import TimeRangeForm from "./TimeRangeForm";

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

      <Grid item xs={12}>
        <TimeRangeForm
          startDate={startDate}
          onStartDateChange={onStartDateChange}
          timestepMinutes={timestepMinutes}
          onTimestepChange={onTimestepChange}
        />
      </Grid>
    </Grid>

  );
};

export default SiteDataForm;
