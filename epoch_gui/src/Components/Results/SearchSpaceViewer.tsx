import * as React from "react";
import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Box,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  IconButton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
  Paper, Switch,
  FormGroup, FormControlLabel,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import VisibilityIcon from "@mui/icons-material/Visibility";

import {MinMaxParam, ValuesParam, FixedParam, Param, GuiParamDict, SearchSpaces} from "../../Models/Endpoints.ts";
import {Site} from "../../State/types.ts";
import {getComponentInfo} from "../ComponentBuilder/ComponentDisplayInfo.tsx";
import {ComponentType} from "../../Models/Core/ComponentBuilder.ts";

// ---- Type guards ----
function isMinMaxParam(v: unknown): v is MinMaxParam<number> {
  return (
    typeof v === "object" &&
    v !== null &&
    "min" in v &&
    "max" in v &&
    "count" in v &&
    typeof (v as any).min === "number" &&
    typeof (v as any).max === "number" &&
    typeof (v as any).count === "number"
  );
}

function isValuesParam(v: unknown): v is ValuesParam {
  return Array.isArray(v) && v.every((x) => ["number", "string"].includes(typeof x));
}

function isFixedParam(v: unknown): v is FixedParam {
  return ["number", "string"].includes(typeof v);
}

// ---- Small helpers ----
const truncateList = (arr: (string | number)[], limit = 8) => {
  if (arr.length <= limit) return arr.join(", ");
  return `${arr.slice(0, limit).join(", ")} … (+${arr.length - limit} more)`;
};

const mono = { fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace" };

// ---- Renderers ----
function ConsideredCell({ value }: { value: Param["considered"] }) {
  if (isFixedParam(value)) {
    return (
      <Stack direction="row" spacing={1} alignItems="center">
        <Chip size="small" label="fixed" />
        <Typography sx={mono}>{String(value)}</Typography>
      </Stack>
    );
  }

  if (isMinMaxParam(value)) {
    return (
      <Stack direction="row" spacing={1} alignItems="center">
        <Chip size="small" label="range" />
        <Typography sx={mono}>
          {value.min} – {value.max}
        </Typography>
      </Stack>
    );
  }

  if (isValuesParam(value)) {
    const valueNoEmpty = value.map((v) => v === "" ? "None" : v);
    const preview = truncateList(valueNoEmpty as (string | number)[]);
    return (
      <Stack direction="row" spacing={1} alignItems="center">
        <Chip size="small" label="values" />
        <Tooltip title={(value as (string | number)[]).join(", ")}>
          <Typography sx={{ ...mono, whiteSpace: "nowrap", textOverflow: "ellipsis", overflow: "hidden", maxWidth: 420 }}>
            {preview}
          </Typography>
        </Tooltip>
      </Stack>
    );
  }

  // Fallback (unknown structure)
  return (
    <Stack direction="row" spacing={1} alignItems="center">
      <Chip size="small" color="warning" label="unknown" />
      <Typography sx={mono}>{JSON.stringify(value)}</Typography>
    </Stack>
  );
}

function ParamTable({ dict, showFixed }: { dict: GuiParamDict, showFixed: boolean }) {
  const entries = Object.entries(dict);
  return (
    <TableContainer component={Paper} variant="outlined" sx={{ mb: 1 }}>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell sx={{ width: 220 }}>Name</TableCell>
            <TableCell>Considered</TableCell>
            <TableCell sx={{ width: 140 }}>Units</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {entries
              .filter(([_, p]) => showFixed || !isFixedParam(p.considered))
              .map(([key, p]) => (
                  <TableRow key={key}>
                    <TableCell>{p.name ?? <em>(unnamed)</em>}</TableCell>
                    <TableCell><ConsideredCell value={p.considered}/></TableCell>
                    <TableCell>{p.units ?? <em>—</em>}</TableCell>
                  </TableRow>
              ))}
          {entries.length === 0 && (
            <TableRow>
              <TableCell colSpan={4}>
                <Typography color="text.secondary">No params</Typography>
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

function ComponentBlock({
  componentKey,
  value,
  defaultExpanded = false,
  showFixed = true,
}: {
  componentKey: string;
  value: GuiParamDict | GuiParamDict[];
  defaultExpanded?: boolean;
  showFixed?: boolean;
}) {
  const isArray = Array.isArray(value);

  const compInfo = getComponentInfo(componentKey as ComponentType);

  return (
    <Accordion defaultExpanded={defaultExpanded} disableGutters>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Stack direction="row" spacing={1} alignItems="center">
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
            {compInfo.displayName}
          </Typography>
        </Stack>
      </AccordionSummary>
      <AccordionDetails>
        {isArray
          ? (value as GuiParamDict[]).map((dict, idx) => (
              <Box key={idx} sx={{ mb: idx < (value as GuiParamDict[]).length - 1 ? 2 : 0 }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                  Variant #{idx + 1}
                </Typography>
                <ParamTable dict={dict} showFixed={showFixed}/>
              </Box>
            ))
          : <ParamTable dict={value as GuiParamDict} showFixed={showFixed} />
        }
      </AccordionDetails>
    </Accordion>
  );
}

// ---- Main viewer ----
export function SearchSpacesViewer({
  data,
  sites,
  initiallyExpandAll = false,
  showJSONLink = true,
}: {
  data: SearchSpaces;
  sites: Site[];
  initiallyExpandAll?: boolean;
  showJSONLink?: boolean;
}) {
  const [jsonOpen, setJsonOpen] = React.useState(false);

  const handleCopy = React.useCallback(() => {
    try {
      navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    } catch {
      // no-op
    }
  }, [data]);

  const siteEntries = React.useMemo(() => Object.entries(data), [data]);

  const [showFixed, setShowFixed] = React.useState(true);

  const getSiteName = (site_id: string) => {
    const site = sites.find(site => site.site_id === site_id);
    return site ? site.name : site_id;
  }

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
        <Typography variant="h6">SearchSpaces</Typography>
        {showJSONLink && (
          <Stack direction="row" spacing={1} alignItems="center">
            <FormGroup>
              <FormControlLabel
                  control={
                    <Switch
                        checked={showFixed}
                        onChange={(e) => setShowFixed(e.target.checked)}
                    />
                  }
                  label="Show Fixed Values"
              />
            </FormGroup>
            <IconButton size="small" onClick={() => setJsonOpen(true)} aria-label="View raw JSON">
              <VisibilityIcon fontSize="small" />
            </IconButton>
            <Tooltip title="Copy JSON">
              <IconButton size="small" onClick={handleCopy} aria-label="Copy JSON">
                <ContentCopyIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Stack>
        )}
      </Stack>

      {siteEntries.length === 0 && (
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography color="text.secondary">No sites.</Typography>
        </Paper>
      )}

      <Stack spacing={1.25}>
        {siteEntries.map(([siteId, components]) => (
          <Accordion key={siteId} defaultExpanded={initiallyExpandAll} disableGutters>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Stack direction="row" spacing={1} alignItems="center">
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  Site: <Box component="span" sx={mono}>{getSiteName(siteId)}</Box>
                </Typography>
              </Stack>
            </AccordionSummary>
            <AccordionDetails>
              <Stack spacing={1}>
                {Object.entries(components).map(([componentKey, value]) => (
                  <ComponentBlock
                    key={componentKey}
                    componentKey={componentKey}
                    value={value}
                    defaultExpanded={initiallyExpandAll}
                    showFixed={showFixed}
                  />
                ))}
                {Object.keys(components).length === 0 && (
                  <Typography color="text.secondary">No components.</Typography>
                )}
              </Stack>
            </AccordionDetails>
          </Accordion>
        ))}
      </Stack>

      <Dialog open={jsonOpen} onClose={() => setJsonOpen(false)} fullWidth maxWidth="md">
        <DialogTitle>
          Raw JSON
          <Typography variant="caption" component="div" color="text.secondary">
            This reflects the `SearchSpaces` object passed to the viewer.
          </Typography>
        </DialogTitle>
        <DialogContent dividers>
          <Box component="pre" sx={{ ...mono, m: 0, fontSize: 13 }}>
            {JSON.stringify(data, null, 2)}
          </Box>
        </DialogContent>
      </Dialog>
    </Box>
  );
}

