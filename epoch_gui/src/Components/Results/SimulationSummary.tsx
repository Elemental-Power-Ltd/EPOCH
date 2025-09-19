import React from 'react';
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


import {SimulationResult} from "../../Models/Endpoints";
import {TaskData} from "../TaskDataViewer/TaskData.ts";
import { TaskDataViewer } from '../TaskDataViewer/TaskDataViewer.tsx';
import { MetricKey } from '../../util/MetricDefinitions.ts';
import {Metric} from "./Metric.tsx";
import {CostInfoTree} from "./CostInfoTree";

interface SimulationSummaryProps {
  result: SimulationResult | null;
  baseline: TaskData | null;
  scenario: TaskData | null;
  isLoading: boolean;
  error: string | null;
}


const SimulationSummary: React.FC<SimulationSummaryProps> = ({ result, scenario, baseline, isLoading, error }) => {

  const [tabValue, setTabValue] = React.useState(0);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };


  const getContent = () => {
    if (error) {
      return (<ErrorSummaryBox error={error} />)
    } else if (isLoading) {
      return (<LoadingSummaryBox/>)
    } else if (!result) {
      return <ErrorSummaryBox error={"No Results"} />
    } else {

      const overviewCarbon: MetricKey[] = [
        "carbon_balance_scope_1",
        "carbon_balance_scope_2",
        "carbon_balance_total",
        "carbon_cost",
      ];

      const overviewFinancial: MetricKey[] = [
          "operating_balance",
          "npv_balance",
          "capex",
          "payback_horizon",
          "return_on_investment"
      ]

      const overviewShortfall: MetricKey[] = [
          "total_electrical_shortfall",
          "total_heat_shortfall"
      ]

      const scenarioElectricity: MetricKey[] = [
          "total_electricity_used",
          "total_electricity_imported",
          "total_electricity_exported",
          "total_electricity_generated",
          "total_electricity_curtailed",
      ]

      const baselineElectricity: MetricKey[] = [
          "baseline_electricity_used",
          "baseline_electricity_imported",
          "baseline_electricity_exported",
          "baseline_electricity_generated",
          "baseline_electricity_curtailed",
      ]

      const elecShortfall: MetricKey[] = [
          "total_electrical_shortfall",
      ]

      const scenarioHeat: MetricKey[] = [
          "total_heat_load",
          "total_dhw_load",
          "total_ch_load",
          "total_gas_used",
      ]

      const baselineHeat: MetricKey[] = [
          "baseline_heat_load",
          "baseline_dhw_load",
          "baseline_ch_load",
          "baseline_gas_used",
      ]

      const heatShortfall: MetricKey[] = [
          "total_heat_shortfall",
          "total_dhw_shortfall",
          "total_ch_shortfall",
      ]

      const scenarioMeter: MetricKey[] = [
          "total_gas_import_cost",
          "total_electricity_import_cost",
          "total_electricity_export_gain",
          "total_meter_cost",
          "total_operating_cost"
      ]

      const baselineMeter: MetricKey[] = [
          "baseline_gas_import_cost",
          "baseline_electricity_import_cost",
          "baseline_electricity_export_gain",
          "baseline_meter_cost",
          "baseline_operating_cost"
      ]

      const financial1: MetricKey[] = [
          "meter_balance",
          "operating_balance",
          "cost_balance",
          "annualised_cost"
      ]

      const financial2: MetricKey[] = [
          "total_net_present_value",
          "baseline_net_present_value",
          "capex",
      ]

        const financial3: MetricKey[] = [
            "payback_horizon",
            "return_on_investment",
        ]

      const scenarioCarbon: MetricKey[] = [
          "total_scope_1_emissions",
          "total_scope_2_emissions",
          "total_combined_carbon_emissions",
          "scenario_environmental_impact_score",
          "scenario_environmental_impact_grade",
      ]

      const baselineCarbon: MetricKey[] = [
          "baseline_scope_1_emissions",
          "baseline_scope_2_emissions",
          "baseline_combined_carbon_emissions",
          "baseline_environmental_impact_score",
          "baseline_environmental_impact_grade",
      ]

      const renderMetricRow = (metricRow: MetricKey[]) => (
        metricRow.map((metric, index) => (
            <Grid item key={index}>
              <Metric name={metric} metrics={result.metrics}/>
            </Grid>
      )))

      const renderTab = (rows: MetricKey[][]) => (
          <Grid container spacing={3}>
            {rows.map(row => (
              <Grid container item xs={12} justifyContent="space-evenly" spacing={2}>
                {renderMetricRow(row)}
              </Grid>
            ))}
          </Grid>
      )

      const renderCapexBreakdown = () => {
          if (!result.metrics.scenario_capex_breakdown) {
              return (
                  <Box sx={{width: "100%", mt: 2}}>
                      <Alert severity="info">
                          Capex Breakdown Unavailable
                      </Alert>
                  </Box>
              )
          }

          return (
              <CostInfoTree
                  items={result.metrics.scenario_capex_breakdown!}
                  totalCapex={result.metrics.capex}
              />
          )
      }

      return (
        <Box>
          {tabValue === 0 && (renderTab([overviewCarbon, overviewFinancial, overviewShortfall]))}
          {tabValue === 1 && (renderTab([scenarioElectricity, baselineElectricity, elecShortfall]))}
          {tabValue === 2 && (renderTab([scenarioHeat, baselineHeat, heatShortfall]))}
          {tabValue === 3 && (renderTab([scenarioMeter, baselineMeter]))}
          {tabValue === 4 && (renderTab([financial1, financial2, financial3]))}
          {tabValue === 5 && (renderTab([scenarioCarbon, baselineCarbon]))}
          {tabValue === 6 && (renderCapexBreakdown())}

          {tabValue === 7 && (<TaskDataViewer data={scenario!}/>)}
          {tabValue === 8 && (<TaskDataViewer data={baseline!}/>)}
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
          <Tab label={"Electricity"}/>
          <Tab label={"Heat"}/>
          <Tab label={"Meter"}/>
          <Tab label={"Financial"}/>
          <Tab label={"Carbon"}/>
          <Tab label={"Capex"}/>
          {scenario !== null && <Tab label={"Scenario"}/>}
          {baseline !== null && <Tab label={"Baseline"}/>}
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
          {/* Top row (4 placeholders, matching overviewCarbon) */}
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

          {/* Bottom row (4 placeholders, matching overviewFinancial count) */}
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
