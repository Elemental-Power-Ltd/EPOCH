import { ReactElement } from "react";

import { Box, Typography } from "@mui/material";

import AssessmentIcon from '@mui/icons-material/Assessment';
import BoltIcon from '@mui/icons-material/Bolt';
import Co2Icon from '@mui/icons-material/Co2';
import FireIcon from '@mui/icons-material/LocalFireDepartment';
import PoundIcon from '@mui/icons-material/CurrencyPound';
import TimelineIcon from '@mui/icons-material/Timeline';

import {MetricDefinition, metricDefs, MetricKey} from "../../util/MetricDefinitions.ts"
import type { SiteMetrics } from "../../State/types.ts"

/**
 * This component is responsible for displaying a single Metric, using the information provided by MetricDefinitions
 */

interface MetricProps {
  name: MetricKey;
  metrics: SiteMetrics;
}

const getIcon = (def: MetricDefinition, rawValue?: any): ReactElement => {

    let iconColor: "action" | "disabled" | "error" = "action"

    if (def.color) {
        iconColor = def.color(rawValue);
    } else if (def.key.startsWith("baseline")) {
        // we used 'disabled' to display the baseline metrics in a faded out colour
        iconColor = "disabled"
    }

    switch (def.icon) {
        case 'Carbon': {
            return <Co2Icon sx={{ fontSize: 40 }} color={iconColor} />
        }
        case 'Pound': {
            return <PoundIcon sx={{ fontSize: 40 }} color={iconColor} />
        }
        case 'Gas': {
            return <FireIcon sx={{ fontSize: 40 }} color={iconColor} />
        }
        case 'Electricity': {
            return <BoltIcon sx={{ fontSize: 40 }} color={iconColor} />
        }
        case 'Year' : {
            return <TimelineIcon sx={{ fontSize: 40 }} color={iconColor} />
        }
        case 'Assessment': {
            return <AssessmentIcon sx={{ fontSize: 40 }} color={iconColor} />
        }
        default: {
            return <FireIcon sx={{ fontSize: 40 }} color={iconColor} />
        }
    }
}

export const Metric: React.FC<MetricProps> = ({ name, metrics }) => {
  const def = metricDefs[name];
  const raw  = metrics[name];
  const value = def.format(raw);

  return (
      <Box display="flex" alignItems="center" justifyContent="center">
        <Box>{getIcon(def, raw)}</Box>
        <Box>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            {def.label}
          </Typography>
          <Typography variant="h6" color="primary" sx={{ fontWeight: 'bold' }}>
            {value}
          </Typography>
        </Box>
      </Box>
  );
};
