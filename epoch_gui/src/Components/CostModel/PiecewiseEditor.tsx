import * as React from "react";
import {
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Divider,
  GridLegacy as Grid,
  IconButton,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import {Add, Delete, Sort} from "@mui/icons-material";
import {PiecewiseCostModel, Segment} from "./Types.ts";
import {cloneModel, normalizeNumberInput, sortSegments, validateModel} from "./Util.ts";


type PiecewiseEditorProps = {
  model: PiecewiseCostModel;
  onChange: (next: PiecewiseCostModel) => void;
  readOnly?: boolean;
};

export const PiecewiseEditor: React.FC<PiecewiseEditorProps> = ({
  model,
  onChange,
  readOnly,
}) => {
  const errors = React.useMemo(() => validateModel(model), [model]);

  const setField = (key: keyof PiecewiseCostModel, val: number) => {
    const next = cloneModel(model);
    (next[key] as number) = val;
    onChange(next);
  };

  const updateSegment = (index: number, patch: Partial<Segment>) => {
    const next = cloneModel(model);
    next.segments[index] = { ...next.segments[index], ...patch };
    onChange(next);
  };

  const addSegment = () => {
    const next = cloneModel(model);
    const lastUpper = next.segments.length > 0 ? next.segments[next.segments.length - 1].upper : 0;
    next.segments.push({ upper: lastUpper + 1, rate: 0 });
    onChange(next);
  };

  const removeSegment = (index: number) => {
    const next = cloneModel(model);
    next.segments.splice(index, 1);
    onChange(next);
  };

  const handleSort = () => {
    const next = cloneModel(model);
    next.segments = sortSegments(next.segments);
    onChange(next);
  };

  const hasOrderIssue = (() => {
    for (let i = 1; i < model.segments.length; i++) {
      if (model.segments[i].upper <= model.segments[i - 1].upper) return true;
    }
    return false;
  })();

  return (
    <Card variant="outlined" sx={{ borderRadius: 2, boxShadow: "sm" }}>
      <CardHeader
        title={<Typography variant="subtitle1">Edit Prices</Typography>}
      />
      <Divider />
      <CardContent>
        <Grid container spacing={2}>
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              type="number"
              label="Fixed Cost"
              value={model.fixed_cost}
              onChange={(e) => setField("fixed_cost", normalizeNumberInput(e.target.value))}
              inputProps={{ step: "any" }}
              disabled={readOnly}
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <Tooltip title="Add a new segment">
              <span>
                <Button onClick={addSegment} startIcon={<Add />} disabled={readOnly}>
                  Add Segment
                </Button>
              </span>
            </Tooltip>
          </Grid>
        </Grid>

        <Box mt={3} component={Paper} variant="outlined" sx={{ borderRadius: 3, overflow: "hidden" }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell width={140}>Upper Threshold</TableCell>
                <TableCell width={140}>Rate</TableCell>
                <TableCell width={80} align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {model.segments.length === 0 && (
                <TableRow>
                  <TableCell colSpan={3}>
                    <Typography variant="body2" color="text.secondary">
                      No segments. All units will be charged at the Final Rate after the Fixed Cost.
                    </Typography>
                  </TableCell>
                </TableRow>
              )}

              {model.segments.map((seg, idx) => (
                <TableRow key={idx} hover>
                  <TableCell>
                    <TextField
                      fullWidth
                      type="number"
                      value={seg.upper}
                      onChange={(e) => updateSegment(idx, { upper: normalizeNumberInput(e.target.value) })}
                      inputProps={{ step: "any", min: 0 }}
                      disabled={readOnly}
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      fullWidth
                      type="number"
                      value={seg.rate}
                      onChange={(e) => updateSegment(idx, { rate: normalizeNumberInput(e.target.value) })}
                      inputProps={{ step: "any" }}
                      disabled={readOnly}
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="Remove segment">
                      <span>
                        <IconButton onClick={() => removeSegment(idx)} disabled={readOnly}>
                          <Delete />
                        </IconButton>
                      </span>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Box>

        <Grid container spacing={2} mt={2}>
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              type="number"
              label="Final Rate"
              value={model.final_rate}
              onChange={(e) => setField("final_rate", normalizeNumberInput(e.target.value))}
              inputProps={{ step: "any" }}
              disabled={readOnly}
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <Tooltip title="Sort segments by upper threshold">
              <span>
                <Button onClick={handleSort} startIcon={<Sort />} disabled={readOnly || model.segments.length < 2}>
                  Sort Segments
                </Button>
              </span>
            </Tooltip>
          </Grid>
        </Grid>


        <Stack direction="row" spacing={1} mt={2} flexWrap="wrap">
          {hasOrderIssue && <Chip color="warning" label="Segments are not strictly increasing by upper" />}
          {errors.length > 0 && (
            <Tooltip
              title={
                <Box>
                  {errors.map((e, i) => (
                    <Typography key={i} variant="caption" display="block">• {e}</Typography>
                  ))}
                </Box>
              }
            >
              <Chip color="error" label={`${errors.length} validation issue${errors.length > 1 ? "s" : ""}`} />
            </Tooltip>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
};

export function calculatePiecewiseCosts(model: PiecewiseCostModel, numUnits: number): number {
  let total = model.fixed_cost;
  let prevUpper = 0;
  for (const seg of model.segments) {
    if (numUnits > seg.upper) {
      total += (seg.upper - prevUpper) * seg.rate;
    } else {
      total += (numUnits - prevUpper) * seg.rate;
      return total;
    }
    prevUpper = seg.upper;
  }
  if (numUnits > prevUpper) {
    total += (numUnits - prevUpper) * model.final_rate;
  }
  return total;
}
