import React from "react";
import dayjs, { Dayjs } from "dayjs";
import { Grid, Button, Tooltip, Typography } from "@mui/material";
import { DayOfInterest } from "../../Models/Endpoints";

interface DayOfInterestSelectorProps {
  daysOfInterest: DayOfInterest[];
  setSelectedStartDatetime: (date: Dayjs | null) => void;
  setDaysToKeep: (days: number) => void;
  title?: string;
}

export const DayOfInterestSelector: React.FC<DayOfInterestSelectorProps> = ({
  daysOfInterest,
  setSelectedStartDatetime,
  setDaysToKeep,
  title = "Days of Interest",
}) => {
  const handleClick = (start_ts: string) => {
    setSelectedStartDatetime(dayjs(start_ts));
    setDaysToKeep(1);
  };

  if (!daysOfInterest?.length) return null;

  return (
    <Grid container direction="column" spacing={1}>
      <Grid item>
        <Typography variant="subtitle2">{title}</Typography>
      </Grid>

      <Grid>
        <Grid container spacing={1} wrap="wrap" justifyContent="center" sx={{px: '2em'}}>
          {daysOfInterest.map((d) => {
            return (
              <Grid item key={`${d.day_type}-${d.start_ts}`}>
                <Tooltip
                  title={`${d.name}: ${dayjs(d.start_ts).format("DD-MM-YYYY")} → ${dayjs(d.end_ts).format("DD-MM-YYYY")}`}
                >
                  <span>
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={() => handleClick(d.start_ts)}
                    aria-label={`Select ${d.name}`}
                  >
                    {d.name}
                  </Button>
                  </span>
                </Tooltip>
              </Grid>
            );
          })}
        </Grid>
      </Grid>
    </Grid>
  );
};
