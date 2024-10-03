import React, { useEffect } from "react";
import {
  TextField,
  MenuItem,
  Grid,
  Checkbox,
  Container,
  FormControl,
  FormLabel,
  FormControlLabel,
  FormGroup,
  InputLabel,
  Select,
} from "@mui/material";
import { DateTimePicker } from "@mui/x-date-pickers/DateTimePicker";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { SelectChangeEvent } from '@mui/material';
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";

import { useEpochStore } from "../../State/state";
import { TaskConfig } from "../../State/types";
import { listClients, listSites } from "../../endpoints";

dayjs.extend(utc);

const TaskConfigForm = () => {
  const taskConfig = useEpochStore((state) => state.run.taskConfig);
  const setTaskConfig = useEpochStore((state) => state.setTaskConfig);
  const client_sites = useEpochStore((state) => state.global.client_sites);
  const setClientSites = useEpochStore((state) => state.setSites);
  const clients = useEpochStore((state) => state.global.clients);
  const setClients = useEpochStore((state) => state.setClients);

  const displayNames = {
    "capex": "CAPEX",
    "carbon_balance": "Carbon Balance",
    "cost_balance": "Cost Balance",
    "payback_horizon": "Payback Horizon",
    "annualised_cost": "Annualised Cost"
  }

  useEffect(() => {
    const fetchClients = async () => {
      const clientList = await listClients();
      setClients(clientList);
    };

    fetchClients();
  }, [setClients]);

  useEffect(() => {
    if (taskConfig.client_id) {
      const fetchSites = async () => {
        const sites = await listSites(taskConfig.client_id);
        setClientSites(sites);
      };

      fetchSites();
    }
  }, [taskConfig.client_id, setClientSites]);

  const handleChange = (field: keyof TaskConfig, value: any) => {
    setTaskConfig({ [field]: value });
  };

  const handleClientChange = async (event: SelectChangeEvent<string>)  => {
    const clientId = event.target.value;
    handleChange("client_id", clientId);
    handleChange("site_id", ""); // Reset site selection when client changes
  };

  const handleObjectiveChange = (event) => {
    const {name, checked} = event.target;
    handleChange("objectives", {
      ...taskConfig.objectives,
      [name]: checked,
    });
  }

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
            <FormControl fullWidth>
              <InputLabel id="client-select-label">Select Client</InputLabel>
              <Select
                labelId="client-select-label"
                id="client-select"
                value={taskConfig.client_id || ''}
                label="Select Client"
                onChange={handleClientChange}
                required
              >
                {clients.map((client) => (
                  <MenuItem key={client.client_id} value={client.client_id}>
                    {client.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              select
              label="Site"
              value={taskConfig.site_id}
              onChange={(e) => handleChange("site_id", e.target.value)}
              required
              disabled={!taskConfig.client_id}
            >
              {client_sites.map((site) => (
                <MenuItem value={site.site_id} key={site.site_id}>
                  {site.name}
                </MenuItem>
              ))}
            </TextField>
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              select
              label="Optimiser"
              value={taskConfig.optimiser}
              onChange={(e) => handleChange("optimiser", e.target.value)}
              required
            >
              <MenuItem value="GridSearch">Grid Search</MenuItem>
              <MenuItem value="NSGA2">Genetic Algorithm (Multi-Objective)</MenuItem>
              <MenuItem value="GeneticAlgorithm">Genetic Algorithm (Single-Objective)</MenuItem>
            </TextField>
          </Grid>

          <Grid item xs={6}>
            <LocalizationProvider dateAdapter={AdapterDayjs}>
              <DateTimePicker
                label="Start Date"
                value={dayjs(taskConfig.start_date).utc()}
                onChange={(date) =>
                  handleChange("start_date", date?.utc().toISOString())
                }
              />
            </LocalizationProvider>
          </Grid>

          <Grid item xs={6}>
            <TextField
              fullWidth
              select
              label="Timestep"
              value={taskConfig.timestep_minutes}
              onChange={(e) => handleChange("timestep_minutes", e.target.value)}
              required
            >
              <MenuItem value={60}>60 Minutes</MenuItem>
              <MenuItem value={30}>30 Minutes</MenuItem>
            </TextField>
          </Grid>

          <Grid item xs={12}>
            <FormGroup>
              <FormLabel component="legend" style={{textAlign: 'center', marginBottom: '8px'}}>Objectives</FormLabel>
              <Grid container spacing={2} justifyContent="center" alignItems="center">
                {Object.keys(taskConfig.objectives).map((objectiveKey) => (
                    <Grid item xs={4} key={objectiveKey} style={{display: 'flex', justifyContent: 'center'}}>
                      <FormControlLabel
                          control={
                            <Checkbox
                                checked={taskConfig.objectives[objectiveKey]}
                                onChange={handleObjectiveChange}
                                name={objectiveKey}
                            />
                          }
                          label={displayNames[objectiveKey]}
                      />
                    </Grid>
                ))}
              </Grid>
            </FormGroup>
          </Grid>
        </Grid>
      </form>
    </Container>
  );
};

export default TaskConfigForm;