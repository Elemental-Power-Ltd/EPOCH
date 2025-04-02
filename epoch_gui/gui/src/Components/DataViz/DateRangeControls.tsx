import React from "react";
import {DateTimePicker} from '@mui/x-date-pickers/DateTimePicker';
import {LocalizationProvider} from '@mui/x-date-pickers/LocalizationProvider';
import {AdapterDayjs} from "@mui/x-date-pickers/AdapterDayjs";
import {Dayjs} from 'dayjs';
import 'dayjs/locale/en-gb';

import {
    Grid,
    FormControl,
    InputLabel,
    MenuItem,
    Select,
    IconButton, Tooltip
} from '@mui/material';

import KeyboardDoubleArrowLeftIcon from '@mui/icons-material/KeyboardDoubleArrowLeft';
import ArrowLeftIcon from '@mui/icons-material/ArrowLeft';
import ArrowRightIcon from '@mui/icons-material/ArrowRight';
import KeyboardDoubleArrowRightIcon from '@mui/icons-material/KeyboardDoubleArrowRight';

import {daysOptions} from "./GraphConfig";

interface DateRangeControlProps {
    selectedStartDatetime: Dayjs | null;
    setSelectedStartDatetime: (date: Dayjs | null) => void;
    daysToKeep: number;
    setDaysToKeep: (days: number) => void;
    minDateTime: Dayjs;
    maxDateTime: Dayjs;
}

export const DateRangeControls: React.FC<DateRangeControlProps> = (
    {
        selectedStartDatetime,
        setSelectedStartDatetime,
        daysToKeep,
        setDaysToKeep,
        minDateTime,
        maxDateTime,
    }) => {

    // We don't want to allow the user to select the actual maxDateTime as this should be exclusive
    // as a hacky way to do this, we can just subtract 1 minute
    const inclusiveMaxDatetime = maxDateTime.subtract(1, 'minute');

    // Compute the candidate dates
    const nextSubtractMonth = selectedStartDatetime?.subtract(1, 'month') || null;
    const nextSubtractDay = selectedStartDatetime?.subtract(1, 'day') || null;
    const nextAddDay = selectedStartDatetime?.add(1, 'day') || null;
    const nextAddMonth = selectedStartDatetime?.add(1, 'month') || null;

    // Determine if they're out of range
    const disableSubtractMonth = !nextSubtractMonth || nextSubtractMonth.isBefore(minDateTime);
    const disableSubtractDay = !nextSubtractDay || nextSubtractDay.isBefore(minDateTime);
    const disableAddDay = !nextAddDay || nextAddDay.isAfter(inclusiveMaxDatetime);
    const disableAddMonth = !nextAddMonth || nextAddMonth.isAfter(inclusiveMaxDatetime);

    return (
        <Grid container justifyContent="center" alignItems="center" spacing={2}>
            <Grid item>
                <LocalizationProvider dateAdapter={AdapterDayjs} adapterLocale="en-gb">
                    <DateTimePicker
                        label="Start Date & Time:"
                        value={selectedStartDatetime}
                        onChange={(date) => setSelectedStartDatetime(date)}
                        minDateTime={minDateTime}
                        maxDateTime={inclusiveMaxDatetime}
                    />
                </LocalizationProvider>
            </Grid>

            <Grid item>
                <FormControl>
                    <InputLabel id="days-label">Days</InputLabel>
                    <Select
                        labelId="days-label"
                        value={daysToKeep}
                        label="Number of Days"
                        onChange={e => setDaysToKeep(e.target.value as number)}
                    >
                        {daysOptions.map((option) => (
                            <MenuItem key={option.value} value={option.value}>
                                {option.label}
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>
            </Grid>

            {/* Buttons to add/subtract 1 day/month */}
            <Grid item xs={12}>
                <Tooltip title="Back 1 Month">
                    <IconButton
                        aria-label="subtract-month"
                        onClick={() => setSelectedStartDatetime(nextSubtractMonth)}
                        disabled={disableSubtractMonth}
                    >
                        <KeyboardDoubleArrowLeftIcon/>
                    </IconButton>
                </Tooltip>
                <Tooltip title="Back 1 Day">
                    <IconButton
                        aria-label="subtract-day"
                        onClick={() => setSelectedStartDatetime(nextSubtractDay)}
                        disabled={disableSubtractDay}
                    >
                        <ArrowLeftIcon/>
                    </IconButton>
                </Tooltip>
                <Tooltip title="Forward 1 Day">
                    <IconButton
                        aria-label="add-day"
                        onClick={() => setSelectedStartDatetime(nextAddDay)}
                        disabled={disableAddDay}
                    >
                        <ArrowRightIcon/>
                    </IconButton>
                </Tooltip>
                <Tooltip title="Forward 1 Month">
                    <IconButton
                        aria-label="add-month"
                        onClick={() => setSelectedStartDatetime(nextAddMonth)}
                        disabled={disableAddMonth}
                    >
                        <KeyboardDoubleArrowRightIcon/>
                    </IconButton>
                </Tooltip>
            </Grid>
        </Grid>
    );
};
