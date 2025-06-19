import React, {ReactElement} from 'react';
import {
  Card,
  CardContent,
  Typography,
  Grid,
  Box,
  Skeleton,
  Alert,
  Tabs,
  Tab
} from '@mui/material';
import BoltIcon from '@mui/icons-material/Bolt';
import Co2Icon from '@mui/icons-material/Co2';
import FireIcon from '@mui/icons-material/LocalFireDepartment';
import PoundIcon from '@mui/icons-material/CurrencyPound';
import TimelineIcon from '@mui/icons-material/Timeline';

import {objectiveNames} from "../../util/displayNames";

import {
  formatPounds,
  formatCarbon,
  formatYears,
  formatCarbonCost,
  formatEnergy
} from '../../util/displayFunctions';

import {SimulationResult} from "../../Models/Endpoints";


interface SimulationSummaryProps {
  result: SimulationResult | null;
  isLoading: boolean;
  error: string | null;
}

export interface MetricDisplay {
  icon: ReactElement;
  label: string;
  value: string;
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

const SimulationSummary: React.FC<SimulationSummaryProps> = ({ result, isLoading, error }) => {

  const [tabValue, setTabValue] = React.useState(0);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };


  const getContent = () => {
    if (error) {
      return (<ErrorSummaryBox error={error} />)
    } else if (isLoading) {
      return (<LoadingSummaryBox/>)
    } else {

      const {
        carbon_balance_scope_1,
        carbon_balance_scope_2,
        carbon_cost,
        cost_balance,
        npv_balance,
        capex,
        payback_horizon,
        annualised_cost,
        total_gas_used,
        total_electricity_imported,
        total_electricity_generated,
        total_electricity_exported,
        total_electrical_shortfall,
        total_heat_shortfall,
        total_gas_import_cost,
        total_electricity_import_cost,
        total_electricity_export_gain
      } = result!.metrics;


      // we split the objectives into two rows so that the card can be displayed nicely
      // this may need to change as we introduce more information
      const carbonObjectives: MetricDisplay[] = [
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

      const costObjectives: MetricDisplay[] = [
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
          label: objectiveNames["npv_balance"],
          value: formatPounds(npv_balance),
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

      const usageTotals: MetricDisplay[] = [
        {
          icon: <FireIcon sx={{fontSize: 40}} color="action"/>,
          label: objectiveNames["total_gas_used"],
          value: formatEnergy(total_gas_used, 100),
        },
        {
          icon: <BoltIcon sx={{fontSize: 40}} color="action"/>,
          label: objectiveNames["total_electricity_imported"],
          value: formatEnergy(total_electricity_imported, 100),
        },
        {
          icon: <BoltIcon sx={{fontSize: 40}} color="action"/>,
          label: objectiveNames["total_electricity_generated"],
          value: formatEnergy(total_electricity_generated, 100),
        },
        {
          icon: <BoltIcon sx={{fontSize: 40}} color="action"/>,
          label: objectiveNames["total_electricity_exported"],
          value: formatEnergy(total_electricity_exported, 100),
        },
      ]

      const shortfallTotals: MetricDisplay[] = [
        {
          icon: <BoltIcon sx={{fontSize: 40}} color={(total_electrical_shortfall ?? 0) > 0 ? "error" : "action"}/>,
          label: objectiveNames["total_electrical_shortfall"],
          value: formatEnergy(total_electrical_shortfall, 100),
        },
        {
          icon: <FireIcon sx={{fontSize: 40}} color={(total_heat_shortfall ?? 0) > 0 ? "error" : "action"}/>,
          label: objectiveNames["total_heat_shortfall"],
          value: formatEnergy(total_heat_shortfall, 100),
        },
      ]

      const costTotals: MetricDisplay[] = [
        {
          icon: <PoundIcon sx={{fontSize: 40}} color="action"/>,
          label: objectiveNames["total_gas_import_cost"],
          value: formatPounds(total_gas_import_cost),
        },
        {
          icon: <PoundIcon sx={{fontSize: 40}} color="action"/>,
          label: objectiveNames["total_electricity_import_cost"],
          value: formatPounds(total_electricity_import_cost),
        },
        {
          icon: <PoundIcon sx={{fontSize: 40}} color="action"/>,
          label: objectiveNames["total_electricity_export_gain"],
          value: formatPounds(total_electricity_export_gain),
        },
      ]

      const renderObjectives = (objectives: MetricDisplay[]) =>
        objectives.map((obj, index) => (
          <Grid item key={index}>
            <ObjectiveItem icon={obj.icon} label={obj.label} value={obj.value} />
          </Grid>
        ));


      return (
        <Box>
          {tabValue === 0 && (
            <Grid container spacing={3}>
              <Grid container item xs={12} justifyContent="space-evenly" spacing={2}>
                {renderObjectives(carbonObjectives)}
              </Grid>

              <Grid container item xs={12} justifyContent="space-evenly" spacing={2}>
                {renderObjectives(costObjectives)}
              </Grid>
            </Grid>
          )}

          {tabValue === 1 && (
            <Grid container spacing={3}>
              <Grid container item xs={12} justifyContent="space-evenly" spacing={2}>
                {renderObjectives(usageTotals)}
              </Grid>

              <Grid container item xs={12} justifyContent="space-evenly" spacing={2}>
                {/* place the shortfall and cost totals in the same row to keep it to two rows*/}
                {renderObjectives(shortfallTotals)}
                {renderObjectives(costTotals)}
              </Grid>

            </Grid>
          )}
        </Box>
      )
    }
  }

  return (
    <Card elevation={3} sx={{ margin: 2 }}>
      <CardContent>
        <Typography variant="h5" gutterBottom>
          {'Result Summary'}
        </Typography>

        <Tabs value={tabValue} onChange={handleTabChange} sx={{ mb: 2 }}>
          <Tab label={"Overview"}/>
          <Tab label={"Totals"}/>
        </Tabs>
        {getContent()}
      </CardContent>
    </Card>
  );
};

export default SimulationSummary;


// A stateless component for the loading state
export const LoadingSummaryBox: React.FC = () => {
  return (
      <Box>
        <Grid container spacing={3}>
          {/* Top row (3 placeholders, matching carbonObjectives count) */}
          <Grid container item xs={12} justifyContent="space-evenly" spacing={2}>
            <Grid item>
              <Box display="flex" alignItems="center" justifyContent="center">
                <Skeleton variant="rectangular" width={150} height={80}/>
              </Box>
            </Grid>
            <Grid item>
              <Box display="flex" alignItems="center" justifyContent="center">
                <Skeleton variant="rectangular" width={150} height={80}/>
              </Box>
            </Grid>
            <Grid item>
              <Box display="flex" alignItems="center" justifyContent="center">
                <Skeleton variant="rectangular" width={150} height={80}/>
              </Box>
            </Grid>
          </Grid>

          {/* Bottom row (4 placeholders, matching costObjectives count) */}
          <Grid container item xs={12} justifyContent="space-evenly" spacing={2}>
            <Grid item>
              <Box display="flex" alignItems="center" justifyContent="center">
                <Skeleton variant="rectangular" width={150} height={80}/>
              </Box>
            </Grid>
            <Grid item>
              <Box display="flex" alignItems="center" justifyContent="center">
                <Skeleton variant="rectangular" width={150} height={80}/>
              </Box>
            </Grid>
            <Grid item>
              <Box display="flex" alignItems="center" justifyContent="center">
                <Skeleton variant="rectangular" width={150} height={80}/>
              </Box>
            </Grid>
            <Grid item>
              <Box display="flex" alignItems="center" justifyContent="center">
                <Skeleton variant="rectangular" width={150} height={80}/>
              </Box>
            </Grid>
          </Grid>
        </Grid>
      </Box>
  );
};

// A stateless component for the error state
export const ErrorSummaryBox: React.FC<{ error: string }> = ({ error }) => {
  return (
    <Box>
      <Grid container spacing={3}>
        <Grid container item xs={12} justifyContent="space-evenly" spacing={2}>
          <Grid item>
            <Alert severity="error">{error}</Alert>
          </Grid>
        </Grid>
      </Grid>
    </Box>
  );
};
