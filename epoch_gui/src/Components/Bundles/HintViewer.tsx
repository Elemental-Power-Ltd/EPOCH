import * as React from "react";
import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Box,
  Chip,
  Divider,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Paper,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";

import {BundleHint, HeatingLoadMetadata, SolarLocation, TariffMetadata} from "../../Models/Endpoints.ts";
import JsonViewer from "../../util/Widgets/JsonViewer.tsx";

const fmtDate = (iso?: string | null) =>
  iso ? new Date(iso).toLocaleString() : "—";

const fmtNum = (n: number | null | undefined, opts?: Intl.NumberFormatOptions) =>
  typeof n === "number" ? new Intl.NumberFormat(undefined, opts).format(n) : "—";

const fmtCost = (n: number | null | undefined) =>
  typeof n === "number" ? `${fmtNum(n, { maximumFractionDigits: 4 })} /kWh` : "—";

const CellMono: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <Box component="span" sx={{ fontFamily: "monospace" }}>{children}</Box>
);

const Section: React.FC<{ title: string; count?: number; children: React.ReactNode }> = ({ title, count, children }) => (
  <Accordion>
    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
      <Stack direction="row" spacing={1} alignItems="center">
        <Typography variant="h6">{title}</Typography>
        {count !== undefined && <Chip size="small" label={count} />}
      </Stack>
    </AccordionSummary>
    <AccordionDetails>{children}</AccordionDetails>
  </Accordion>
);

const RenewablesTable: React.FC<{ rows: SolarLocation[] }> = ({ rows }) => {
  if (!rows.length) return <Typography color="text.secondary">No solar locations.</Typography>;
  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Renewables ID</TableCell>
            <TableCell>Name</TableCell>
            <TableCell align="right">Azimuth (°)</TableCell>
            <TableCell align="right">Tilt (°)</TableCell>
            <TableCell align="right">Max Power (kW)</TableCell>
            <TableCell>Mounting</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.map((r) => (
            <TableRow key={r.renewables_location_id ?? `${r.site_id}-${r.name ?? "unnamed"}`}>
              <TableCell><CellMono>{r.renewables_location_id ?? "—"}</CellMono></TableCell>
              <TableCell>{r.name ?? "—"}</TableCell>
              <TableCell align="right">{fmtNum(r.azimuth)}</TableCell>
              <TableCell align="right">{fmtNum(r.tilt)}</TableCell>
              <TableCell align="right">{fmtNum(r.maxpower)}</TableCell>
              <TableCell>
                <Chip size="small" label={r.mounting_type} variant="outlined" />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

const TariffsTable: React.FC<{ rows: TariffMetadata[] }> = ({ rows }) => {
  if (!rows.length) return <Typography color="text.secondary">No tariffs.</Typography>;
  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Dataset ID</TableCell>
            <TableCell>Provider</TableCell>
            <TableCell>Product</TableCell>
            <TableCell>Tariff</TableCell>
            <TableCell>Valid From</TableCell>
            <TableCell>Valid To</TableCell>
            <TableCell align="right">Day</TableCell>
            <TableCell align="right">Night</TableCell>
            <TableCell align="right">Peak</TableCell>
            <TableCell>Created</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.map((t) => (
            <TableRow key={`${t.dataset_id}-${t.tariff_name}`}>
              <TableCell><CellMono>{t.dataset_id}</CellMono></TableCell>
              <TableCell><Chip size="small" label={t.provider} /></TableCell>
              <TableCell>{t.product_name}</TableCell>
              <TableCell>{t.tariff_name}</TableCell>
              <TableCell>{fmtDate(t.valid_from)}</TableCell>
              <TableCell>{fmtDate(t.valid_to)}</TableCell>
              <TableCell align="right">{fmtCost(t.day_cost)}</TableCell>
              <TableCell align="right">{fmtCost(t.night_cost)}</TableCell>
              <TableCell align="right">{fmtCost(t.peak_cost)}</TableCell>
              <TableCell>{fmtDate(t.created_at)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

const HeatingTable: React.FC<{ rows: HeatingLoadMetadata[] }> = ({ rows }) => {
  if (!rows.length) return <Typography color="text.secondary">No heating load metadata.</Typography>;

  // calculate percentage savings agains the base peak load (row[0])
  const basePeakLoad = rows[0].peak_hload;
  const calcSavings = (peak: number | null) => {
    if (basePeakLoad === null || peak === null || peak === basePeakLoad) {
      return "-"
    }
    const savings = (basePeakLoad - peak) / basePeakLoad * 100
    return `${savings.toFixed(2)}%`
  }


  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Dataset ID</TableCell>
            <TableCell>Generation Method</TableCell>
            <TableCell>Interventions</TableCell>
            <TableCell align="right">Peak HLoad (kW)</TableCell>
            <TableCell align="right">Savings</TableCell>
            <TableCell>Created</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.map((h) => (
            <TableRow key={`${h.dataset_id}-${h.created_at}`}>
              <TableCell><CellMono>{h.dataset_id}</CellMono></TableCell>
              <TableCell>
                <Chip size="small" label={h.generation_method} variant="outlined" />
              </TableCell>
              <TableCell>
                <Stack direction="row" spacing={0.5} useFlexGap flexWrap="wrap">
                  {h.interventions?.length
                    ? h.interventions.map((i) => (
                        <Chip key={i} size="small" label={i} />
                      ))
                    : <Typography component="span">—</Typography>}
                </Stack>
              </TableCell>
              <TableCell align="right">{fmtNum(h.peak_hload)}</TableCell>
              <TableCell align="right">{calcSavings(h.peak_hload)}</TableCell>
              <TableCell>{fmtDate(h.created_at)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export const HintViewer: React.FC<{ hints: BundleHint, siteName?: string }> = ({ hints, siteName }) => {
  return (
    <Stack spacing={2} sx={{mb: "1em"}}>
      <Paper variant="outlined">
        <Box p={2} sx={{display: 'flex', alignItems: 'center', gap: 1}}>
          <Typography variant="h5" sx={{'flex': 1}} gutterBottom>
            {siteName ?? "Bundle Hints"}
          </Typography>
          <JsonViewer data={hints} name={"Site Hints"}/>

        </Box>
        <Divider />

        <Section title="Renewables" count={hints.renewables?.length ?? 0}>
          <RenewablesTable rows={hints.renewables ?? []} />
        </Section>

        <Section title="Tariffs" count={hints.tariffs?.length ?? 0}>
          <TariffsTable rows={hints.tariffs ?? []} />
        </Section>

        <Section title="Heating" count={hints.heating?.length ?? 0}>
          <HeatingTable rows={hints.heating ?? []} />
        </Section>

      </Paper>




    </Stack>
  );
};
