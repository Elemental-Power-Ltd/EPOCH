import React from "react";
import { Grid, TextField, MenuItem } from "@mui/material";
import dayjs, {Dayjs} from "dayjs";
import 'dayjs/locale/en-gb';
import utc from "dayjs/plugin/utc";
import TimeRangeForm from "./TimeRangeForm";

dayjs.extend(utc);

interface SiteDataFormProps {
  siteId: string;
  onSiteChange: (value: string) => void;
  startDate: Dayjs | null
  onStartDateChange: (value: Dayjs | null) => void;
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
