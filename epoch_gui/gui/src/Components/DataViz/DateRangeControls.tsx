import React from "react";
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import {AdapterDayjs} from "@mui/x-date-pickers/AdapterDayjs";
import {Dayjs} from 'dayjs';
import 'dayjs/locale/en-gb';
import {Select, MenuItem, FormControl, InputLabel, Button} from '@mui/material';

import {daysOptions} from "./GraphConfig";

interface DateRangeControlProps {
    selectedStartDatetime: Dayjs | null;
    setSelectedStartDatetime: (date: Dayjs | null) => void;
    daysToKeep: number;
    setDaysToKeep: (days: number) => void;
}

export const DateRangeControls: React.FC<DateRangeControlProps> = ({
  selectedStartDatetime,
  setSelectedStartDatetime,
  daysToKeep,
  setDaysToKeep
}) => {
    return (
        <div id="range-picker-group" style={{//border: '2px dotted rgb(96 139 168)',
            display: 'flex', justifyContent: 'center', gap: '40px'
        }}
        >
            <div id="datepicker" style={{display: 'flex', alignItems: 'center', gap: '10px'}}
            >
                {/* Date Picker for Start Date */}
                <LocalizationProvider dateAdapter={AdapterDayjs} adapterLocale={"en-gb"}>
                    <DateTimePicker
                        label="Start Date & Time:"
                        value={selectedStartDatetime}
                        onChange={(date) => setSelectedStartDatetime(date)}
                    />
                </LocalizationProvider>
            </div>

            <div id="dropdown" style={{display: 'flex', alignItems: 'center', gap: '10px'}}
            >
                <FormControl>
                    <InputLabel id="days-label">Days</InputLabel>
                    <Select
                        labelId="days-label"
                        value={daysToKeep}
                        label="Number of Days"
                        onChange={(e) => setDaysToKeep(e.target.value as number)}
                    >
                        {daysOptions.map((option) => (
                            <MenuItem key={option.value} value={option.value}>
                                {option.label}
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>
            </div>
        </div>
    )
}
