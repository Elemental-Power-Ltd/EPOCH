import React from "react";
import {
  TextField,
  MenuItem,
  Button,
  Grid,
  Container,
  Typography,
  FormGroup,
  FormControlLabel,
  Checkbox,
} from "@mui/material";
import { DateTimePicker } from "@mui/x-date-pickers/DateTimePicker";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";

import {useEpochStore} from "../../State/state";
import {TaskConfig, TaskObjectives} from "../../State/types";

dayjs.extend(utc);

const TaskConfigForm = () => {

  const taskConfig = useEpochStore((state) => state.run.taskConfig);
  const setTaskConfig = useEpochStore((state) => state.setTaskConfig);

  const client_sites = useEpochStore((state) => state.global.client_sites);

  const handleChange = (field: keyof TaskConfig, value: any) => {
    setTaskConfig({[field]: value});
  };


  return (
      <Container maxWidth="sm">
        <form>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                  fullWidth label="Task Name" value={taskConfig.task_name}
                  onChange={(e) => handleChange("task_name", e.target.value)}
                  required
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                  fullWidth select label="Optimiser" value={taskConfig.optimiser}
                  onChange={(e) => handleChange("optimiser", e.target.value)}
                  required
              >
                <MenuItem value="GridSearch">Grid Search</MenuItem>
                <MenuItem value="GeneticAlgorithm">Genetic Algorithm</MenuItem>
              </TextField>
            </Grid>

            <Grid item xs={12}>
              <TextField
                  fullWidth select label="Site" value={taskConfig.site_id}
                  onChange={(e) => handleChange("site_id", e.target.value)}
                  required
              >
                {client_sites.map((site) => (
                    <MenuItem value={site.site_id} key={site.site_id}>{site.name}</MenuItem>
                ))}
              </TextField>
            </Grid>

            <Grid item xs={6}>
              <LocalizationProvider dateAdapter={AdapterDayjs}>
                <DateTimePicker
                    label="Start Date" value={dayjs(taskConfig.start_date).utc()}
                    onChange={(date) =>
                        handleChange("start_date", date?.utc().toISOString())
                    }
                />
              </LocalizationProvider>
            </Grid>

            <Grid item xs={6}>
              <TextField
                  fullWidth select label="Timestep" value={taskConfig.timestep_minutes}
                  onChange={(e) => handleChange("timestep_minutes", e.target.value)}
                  required
              >
                <MenuItem value={60}>60 Minutes</MenuItem>
                <MenuItem value={30}>30 Minutes</MenuItem>
              </TextField>
            </Grid>

          </Grid>
        </form>
      </Container>
  );
};

export default TaskConfigForm;
