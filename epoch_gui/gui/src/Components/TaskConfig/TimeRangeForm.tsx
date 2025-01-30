/**
 * Form components to express the length and granularity of a simulation
 */

import React from "react";
import { Grid, TextField, MenuItem } from "@mui/material";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { DateTimePicker } from "@mui/x-date-pickers/DateTimePicker";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";

dayjs.extend(utc);

interface TimeRangeFormProps {
  startDate: string;
  onStartDateChange: (value: string) => void;
  timestepMinutes: number;
  onTimestepChange: (value: number) => void;
}

const TimeRangeForm: React.FC<TimeRangeFormProps> = ({
  startDate,
  onStartDateChange,
  timestepMinutes,
  onTimestepChange,
}) => {
  return (
    <Grid container spacing={2}>
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
          <MenuItem value={30}>30 Minutes</MenuItem>
          <MenuItem value={60}>60 Minutes</MenuItem>
        </TextField>
      </Grid>
    </Grid>
  );
};

export default TimeRangeForm;
