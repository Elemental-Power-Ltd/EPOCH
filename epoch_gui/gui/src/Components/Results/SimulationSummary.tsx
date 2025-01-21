import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Grid,
  Box,
  Skeleton,
  Alert
} from '@mui/material';
import Co2Icon from '@mui/icons-material/Co2';
import PoundIcon from '@mui/icons-material/CurrencyPound';
import TimelineIcon from '@mui/icons-material/Timeline';

import {objectiveNames} from "../../util/displayNames";

import {
  formatPounds,
  formatCarbon,
  formatYears,
  formatCarbonCost,
} from '../../util/displayFunctions';

import { SimulationResult } from "../../Models/Endpoints";

interface SimulationSummaryProps {
  result: SimulationResult;
}

// A reusable component for displaying a single objective item
const ObjectiveItem: React.FC<{
  icon: React.ReactElement;
  label: string;
  value: string | number;
}> = ({ icon, label, value }) => (
  <Box display="flex" alignItems="center" justifyContent="center">
    <Box sx={{ fontSize: 40, mr: 2 }}>{icon}</Box>
    <Box>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        {label}
      </Typography>
      <Typography variant="h6" color="primary" sx={{ fontWeight: 'bold' }}>
        {value}
      </Typography>
    </Box>
  </Box>
);

const SimulationSummary: React.FC<SimulationSummaryProps> = ({ result }) => {

  const {
    carbon_balance_scope_1,
    carbon_balance_scope_2,
    carbon_cost,
    cost_balance,
    capex,
    payback_horizon,
    annualised_cost,
  } = result.objectives;

  // we split the objectives into two rows so that the card can be displayed nicely
  // this may need to change as we introduce more information
  const carbonObjectives = [
    {
      icon: <Co2Icon sx={{ fontSize: 40 }} color="action" />,
      label: objectiveNames["carbon_balance_scope_1"],
      value: formatCarbon(carbon_balance_scope_1),
    },
    {
      icon: <Co2Icon sx={{ fontSize: 40 }} color="action" />,
      label: objectiveNames["carbon_balance_scope_2"],
      value: formatCarbon(carbon_balance_scope_2),
    },
    {
      icon: <Co2Icon sx={{ fontSize: 40 }} color="action" />,
      label: objectiveNames["carbon_cost"],
      value: formatCarbonCost(carbon_cost),
    },
  ];

  const costObjectives = [
    {
      icon: <PoundIcon sx={{ fontSize: 40 }} color="action" />,
      label: objectiveNames["capex"],
      value: formatPounds(capex),
    },
    {
      icon: <PoundIcon sx={{ fontSize: 40 }} color="action" />,
      label: objectiveNames["cost_balance"],
      value: formatPounds(cost_balance),
    },
    {
      icon: <PoundIcon sx={{ fontSize: 40 }} color="action" />,
      label: objectiveNames["annualised_cost"],
      value: formatPounds(annualised_cost),
    },
    {
      icon: <TimelineIcon sx={{ fontSize: 40 }} color="action" />,
      label: objectiveNames["payback_horizon"],
      value: formatYears(payback_horizon),
    },
  ];

  const renderObjectives = (objectives) =>
    objectives.map((obj, index) => (
      <Grid item key={index}>
        <ObjectiveItem icon={obj.icon} label={obj.label} value={obj.value} />
      </Grid>
    ));

  return (
    <Card elevation={3} sx={{ margin: 2 }}>
      <CardContent>
        <Typography variant="h5" gutterBottom>
          {'Result Summary'}
        </Typography>

        <Grid container spacing={3}>
          <Grid container item xs={12} justifyContent="space-evenly" spacing={2}>
            {renderObjectives(carbonObjectives)}
          </Grid>

          <Grid container item xs={12} justifyContent="space-evenly" spacing={2}>
            {renderObjectives(costObjectives)}
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default SimulationSummary;


// A stateless component for the loading state, matching the card layout
export const LoadingSimulatingSummary: React.FC = () => {
  return (
    <Card elevation={3} sx={{ margin: 2 }}>
      <CardContent>
        <Typography variant="h5" gutterBottom>
          {'Result Summary'}
        </Typography>

        <Grid container spacing={3}>
          {/* Top row (3 placeholders, matching carbonObjectives count) */}
          <Grid container item xs={12} justifyContent="space-evenly" spacing={2}>
            <Grid item>
              <Box display="flex" alignItems="center" justifyContent="center">
                <Skeleton variant="rectangular" width={150} height={80} />
              </Box>
            </Grid>
            <Grid item>
              <Box display="flex" alignItems="center" justifyContent="center">
                <Skeleton variant="rectangular" width={150} height={80} />
              </Box>
            </Grid>
            <Grid item>
              <Box display="flex" alignItems="center" justifyContent="center">
                <Skeleton variant="rectangular" width={150} height={80} />
              </Box>
            </Grid>
          </Grid>

          {/* Bottom row (4 placeholders, matching costObjectives count) */}
          <Grid container item xs={12} justifyContent="space-evenly" spacing={2}>
            <Grid item>
              <Box display="flex" alignItems="center" justifyContent="center">
                <Skeleton variant="rectangular" width={150} height={80} />
              </Box>
            </Grid>
            <Grid item>
              <Box display="flex" alignItems="center" justifyContent="center">
                <Skeleton variant="rectangular" width={150} height={80} />
              </Box>
            </Grid>
            <Grid item>
              <Box display="flex" alignItems="center" justifyContent="center">
                <Skeleton variant="rectangular" width={150} height={80} />
              </Box>
            </Grid>
            <Grid item>
              <Box display="flex" alignItems="center" justifyContent="center">
                <Skeleton variant="rectangular" width={150} height={80} />
              </Box>
            </Grid>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

// A stateless component for the error state, matching the card layout
export const ErroredSimulationSummary: React.FC<{ error: string }> = ({ error }) => {
  return (
    <Card elevation={3} sx={{ margin: 2 }}>
      <CardContent>
        <Typography variant="h5" gutterBottom>
          {'Result Summary'}
        </Typography>

        <Grid container spacing={3}>
          <Grid container item xs={12} justifyContent="space-evenly" spacing={2}>
            <Grid item>
              <Alert severity="error">{error}</Alert>
            </Grid>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};
