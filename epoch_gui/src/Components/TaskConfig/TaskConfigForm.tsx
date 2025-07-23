import React from "react";

import {
  TextField,
  Grid,
  Checkbox,
  Container,
  FormLabel,
  FormControlLabel,
  FormGroup,
} from "@mui/material";
import { useEpochStore } from "../../State/Store";
import { TaskConfig } from "../../State/types";
import {metricDefs} from "../../util/MetricDefinitions.ts";

import TimeRangeForm from "./TimeRangeForm";
import HyperParamForm from "../HyperParams/OptimiserConfig.tsx";

const TaskConfigForm = () => {
  const taskConfig = useEpochStore((state) => state.optimise.taskConfig);
  const setTaskConfig = useEpochStore((state) => state.setTaskConfig);


  const handleChange = (field: keyof TaskConfig, value: any) => {
    setTaskConfig({ [field]: value });
  };

  const handleObjectiveChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const {name, checked} = event.target;
    handleChange("objectives", {
      ...taskConfig.objectives,
      [name]: checked,
    });
  };

  return (
    <Container maxWidth="sm">
      <form>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Task Name"
              value={taskConfig.task_name}
              onChange={(e) => handleChange("task_name", e.target.value)}
              required
            />
          </Grid>

          <Grid item xs={12}>
            <TimeRangeForm
              startDate={taskConfig.start_date}
              onStartDateChange={(val) => handleChange("start_date", val)}
              timestepMinutes={taskConfig.timestep_minutes}
              onTimestepChange={(val) => handleChange("timestep_minutes", val)}
            />
          </Grid>

          {/* Select hidden - the only valid option is NSGA2 */}
          {/*<Grid item xs={12}>*/}
          {/*  <TextField*/}
          {/*    fullWidth*/}
          {/*    select*/}
          {/*    label="Optimiser"*/}
          {/*    value={taskConfig.optimiser}*/}
          {/*    onChange={(e) => handleChange("optimiser", e.target.value)}*/}
          {/*    required*/}
          {/*  >*/}
          {/*    <MenuItem value="NSGA2">Genetic Algorithm</MenuItem>*/}
          {/*    <MenuItem disabled value="GridSearch">Grid Search</MenuItem>*/}
          {/*  </TextField>*/}
          {/*</Grid>*/}

          <Grid item xs={12}>
            <FormGroup>
              <FormLabel component="legend" style={{textAlign: 'center', marginBottom: '8px'}}>Objectives</FormLabel>
              <Grid container spacing={2} justifyContent="center" alignItems="center">
                {Object.keys(taskConfig.objectives).map((objectiveKey) => (
                    <Grid item xs={4} key={objectiveKey} style={{display: 'flex', justifyContent: 'center'}}>
                      <FormControlLabel
                          control={
                            <Checkbox
                                checked={taskConfig.objectives[objectiveKey as keyof typeof taskConfig.objectives]}
                                onChange={handleObjectiveChange}
                                name={objectiveKey}
                            />
                          }
                          label={metricDefs[objectiveKey as keyof typeof metricDefs].label}
                      />
                    </Grid>
                ))}
              </Grid>
            </FormGroup>
          </Grid>
        </Grid>
      </form>
      <HyperParamForm/>
    </Container>
  );
};

export default TaskConfigForm;
