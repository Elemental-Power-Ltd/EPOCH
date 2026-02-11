import * as React from "react";
import {
    Accordion,
    AccordionSummary,
    AccordionDetails,
    Box,
    Button,
    Container,
    FormControl,
    IconButton,
    InputAdornment,
    InputLabel,
    MenuItem,
    Select,
    Stack,
    Switch,
    TextField,
    ToggleButton,
    ToggleButtonGroup,
    Typography,
} from "@mui/material";

import LocationOnIcon from "@mui/icons-material/LocationOn";
import HomeWorkIcon from "@mui/icons-material/HomeWork";
import SolarPowerIcon from "@mui/icons-material/SolarPower";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import DeleteIcon from "@mui/icons-material/Delete";
import AddIcon from "@mui/icons-material/Add";
import LocalFireDepartmentIcon from "@mui/icons-material/LocalFireDepartment";
import BatteryChargingFullIcon from "@mui/icons-material/BatteryChargingFull";
import WindowIcon from "@mui/icons-material/Window";
import LayersIcon from "@mui/icons-material/Layers";
import RoofingIcon from "@mui/icons-material/Roofing";

import {
    Direction,
    HeatSource,
    Location,
    BuildingType,
    PanelInfo,
    InsulationInfo,
    SimulationRequest,
} from "./demo-endpoint";

const LOCATIONS: Location[] = ["Cardiff", "London", "Edinburgh"];
const BUILDINGS: BuildingType[] = ["Domestic", "TownHall", "LeisureCentre"];
const DIRECTIONS: Direction[] = ["North", "East", "South", "West"];

const BUILDING_LABEL: Record<BuildingType, string> = {
    Domestic: "Domestic",
    TownHall: "Town hall",
    LeisureCentre: "Leisure centre",
};

function clampNonNeg(n: number) {
    if (!Number.isFinite(n)) return 0;
    return Math.max(0, n);
}

type DemoFormProps = {
    onSubmit: (request: SimulationRequest) => void;
    siteExpanded: boolean;
    setSiteExpanded: (expanded: boolean) => void;
    componentsExpanded: boolean;
    setComponentsExpanded: (expanded: boolean) => void;
};

const Section: React.FC<{
    title: React.ReactNode;
    icon?: React.ReactNode;
    action?: React.ReactNode;
    children: React.ReactNode;
}> = ({title, icon, action, children}) => (
    <Box
        sx={{
            p: 2,
            borderRadius: 2,
            border: "1px solid",
            borderColor: "divider",
            bgcolor: "background.paper",
        }}
    >
        <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{mb: 1}}>
            <Stack direction="row" spacing={1} alignItems="center">
                {icon}
                <Typography variant="subtitle2" color="text.secondary">
                    {title}
                </Typography>
            </Stack>
            {action}
        </Stack>
        {children}
    </Box>
);

const DemoForm: React.FC<DemoFormProps> = ({
                                               onSubmit,
                                               siteExpanded,
                                               setSiteExpanded,
                                               componentsExpanded,
                                               setComponentsExpanded,
                                           }) => {
    const [request, setRequest] = React.useState<SimulationRequest>({
        location: "Cardiff",
        building: "Domestic",
        panels: [],
        heat: {heat_power: 8, heat_source: "Boiler"},
        insulation: {double_glazing: false, cladding: false, loft: false},
        battery: null,
        full_reporting: true,
    });

    const [batteryPowerTouched, setBatteryPowerTouched] = React.useState<boolean>(false);

    React.useEffect(() => {
        if (!request.battery) return;
        if (batteryPowerTouched) return;

        const cap = clampNonNeg(request.battery.capacity);
        const desiredPower = cap / 2;

        if (request.battery.power !== desiredPower) {
            setRequest((prev) => ({
                ...prev,
                battery: prev.battery ? {...prev.battery, power: desiredPower} : prev.battery,
            }));
        }
    }, [request.battery?.capacity, request.battery?.power, request.battery, batteryPowerTouched]);

    const setLocation = (_: unknown, value: Location | null) => {
        if (!value) return;
        setRequest((r) => ({...r, location: value}));
    };

    const setBuilding = (_: unknown, value: BuildingType | null) => {
        if (!value) return;
        setRequest((r) => ({...r, building: value}));
    };

    const toggleInsulation = (key: keyof InsulationInfo) => {
        setRequest((r) => ({
            ...r,
            insulation: {...r.insulation, [key]: !r.insulation[key]},
        }));
    };

    const updatePanel = (idx: number, patch: Partial<PanelInfo>) => {
        setRequest((r) => ({
            ...r,
            panels: r.panels.map((p, i) => (i === idx ? {...p, ...patch} : p)),
        }));
    };

    const addPanel = () => {
        setRequest((r) => ({
            ...r,
            panels: [...r.panels, {solar_peak: 2.5, direction: "South"}],
        }));
    };

    const removePanel = (idx: number) => {
        setRequest((r) => ({
            ...r,
            panels: r.panels.filter((_, i) => i !== idx),
        }));
    };

    const setBatteryEnabled = (enabled: boolean) => {
        setBatteryPowerTouched(false);
        setRequest((r) => ({
            ...r,
            battery: enabled ? {capacity: 10, power: 5} : null,
        }));
    };

    const centreSummaryStyle = {
        position: "relative",
        justifyContent: "center",
        "& .MuiAccordionSummary-content": {
            justifyContent: "center",
            margin: 0,
        },
        "& .MuiAccordionSummary-expandIconWrapper": {
            position: "absolute",
            right: 12,
        },
        minHeight: 44,
        px: 2,
        "&.MuiAccordionSummary-root": {py: 0.5}
    };

    const siteFormContent = () => (
        <Stack spacing={2}>
            <Typography variant="caption" color="text.secondary">
                Choose a type of building and its location.
            </Typography>

            <Stack direction={{xs: "column", md: "row"}} spacing={2}>
                <Box sx={{flex: 1}}>
                    <Typography variant="subtitle2" color="text.secondary" sx={{mb: 1}}>
                        <LocationOnIcon fontSize="small" style={{verticalAlign: "middle"}}/> Location
                    </Typography>
                    <ToggleButtonGroup value={request.location} exclusive onChange={setLocation} fullWidth size="small">
                        {LOCATIONS.map((loc) => (
                            <ToggleButton key={loc} value={loc} sx={{textTransform: "none"}}>
                                {loc}
                            </ToggleButton>
                        ))}
                    </ToggleButtonGroup>
                </Box>

                <Box sx={{flex: 1}}>
                    <Typography variant="subtitle2" color="text.secondary" sx={{mb: 1}}>
                        <HomeWorkIcon fontSize="small" style={{verticalAlign: "middle"}}/> Building
                    </Typography>
                    <ToggleButtonGroup value={request.building} exclusive onChange={setBuilding} fullWidth size="small">
                        {BUILDINGS.map((b) => (
                            <ToggleButton key={b} value={b} sx={{textTransform: "none"}}>
                                {BUILDING_LABEL[b]}
                            </ToggleButton>
                        ))}
                    </ToggleButtonGroup>
                </Box>
            </Stack>
        </Stack>
    );

    const panelsFormInner = () => {
        const action = (
            <Button startIcon={<AddIcon/>} onClick={addPanel} size="small" variant="outlined">
                {request.panels.length > 0 ? "Add" : "Add panels"}
            </Button>
        );

        return (
            <Section
                title="Solar"
                icon={<SolarPowerIcon fontSize="small" style={{verticalAlign: "middle"}}/>}
                action={action}
            >
                {request.panels.length === 0 ? (
                    <Typography variant="body2" color="text.secondary">
                        No panels installed.
                    </Typography>
                ) : (
                    <Stack spacing={1}>
                        {request.panels.map((p, idx) => (
                            <Stack
                                key={idx}
                                direction={{xs: "column", md: "row"}}
                                spacing={1.5}
                                alignItems="center"
                                sx={{
                                    py: 1,
                                    borderTop: idx === 0 ? "none" : "1px solid",
                                    borderColor: "divider",
                                }}
                            >
                                <TextField
                                    sx={{flex: 1, width: "100%"}}
                                    label="Peak"
                                    type="number"
                                    value={p.solar_peak}
                                    onChange={(e) => updatePanel(idx, {solar_peak: clampNonNeg(Number(e.target.value))})}
                                    InputProps={{
                                        endAdornment: <InputAdornment position="end">kWp</InputAdornment>,
                                    }}
                                    size="small"
                                />

                                <FormControl sx={{flex: 1, width: "100%"}} size="small">
                                    <InputLabel id={`panel-direction-label-${idx}`}>Direction</InputLabel>
                                    <Select
                                        labelId={`panel-direction-label-${idx}`}
                                        value={p.direction}
                                        label="Direction"
                                        onChange={(e) => updatePanel(idx, {direction: e.target.value as Direction})}
                                    >
                                        {DIRECTIONS.map((direction) => (
                                            <MenuItem key={direction} value={direction}>
                                                {direction}
                                            </MenuItem>
                                        ))}
                                    </Select>
                                </FormControl>

                                <IconButton aria-label="Remove panel" onClick={() => removePanel(idx)} size="small">
                                    <DeleteIcon fontSize="small"/>
                                </IconButton>
                            </Stack>
                        ))}
                    </Stack>
                )}
            </Section>
        );
    };

    const heatFormInner = () => (
        <Section
            title="Heat"
            icon={<LocalFireDepartmentIcon fontSize="small" style={{verticalAlign: "middle"}}/>}
        >
            <Stack spacing={1.5}>
                <ToggleButtonGroup
                    value={request.heat.heat_source === "HeatPump" ? "ashp" : "boiler"}
                    exclusive
                    onChange={(_, v: "boiler" | "ashp" | null) => {
                        if (!v) return;
                        setRequest((r) => ({
                            ...r,
                            heat: {...r.heat, heat_source: v === "boiler" ? "Boiler" : "HeatPump"},
                        }));
                    }}
                    fullWidth
                    size="small"
                >
                    <ToggleButton value="boiler" sx={{textTransform: "none"}}>
                        Keep boiler
                    </ToggleButton>
                    <ToggleButton value="ashp" sx={{textTransform: "none"}}>
                        Install heat pump
                    </ToggleButton>
                </ToggleButtonGroup>

                {request.heat.heat_source === "HeatPump" && (
                    <Box sx={{p: 1.5, borderRadius: 2}}>
                        <TextField
                            fullWidth
                            label="Heat pump power"
                            type="number"
                            value={request.heat.heat_power}
                            onChange={(e) =>
                                setRequest((r) => ({
                                    ...r,
                                    heat: {...r.heat, heat_power: clampNonNeg(Number(e.target.value))},
                                }))
                            }
                            InputProps={{
                                endAdornment: <InputAdornment position="end">kW</InputAdornment>,
                            }}
                            size="small"
                        />
                    </Box>
                )}
            </Stack>
        </Section>
    );

    const batteryFormInner = () => {
        const action = (
            <Stack direction="row" spacing={1} alignItems="center">
                <Typography variant="caption" color="text.secondary">
                    {request.battery ? "On" : "Off"}
                </Typography>
                <Switch checked={!!request.battery} onChange={(e) => setBatteryEnabled(e.target.checked)} size="small"/>
            </Stack>
        );

        return (
            <Section
                title="Battery"
                icon={<BatteryChargingFullIcon fontSize="small" style={{verticalAlign: "middle"}}/>}
                action={action}
            >
                {request.battery ? (
                    <Stack spacing={1.25}>
                        <Stack direction={{xs: "column", md: "row"}} spacing={2}>
                            <TextField
                                sx={{flex: 1}}
                                label="Capacity"
                                type="number"
                                value={request.battery.capacity}
                                onChange={(e) => {
                                    const capacity = clampNonNeg(Number(e.target.value));
                                    setRequest((r) => ({
                                        ...r,
                                        battery: r.battery ? {...r.battery, capacity} : r.battery,
                                    }));
                                }}
                                InputProps={{
                                    endAdornment: <InputAdornment position="end">kWh</InputAdornment>,
                                }}
                                size="small"
                            />

                            <TextField
                                sx={{
                                    flex: 1,
                                    opacity: batteryPowerTouched ? 1 : 0.7,
                                    transition: "opacity 150ms ease",
                                }}
                                label="Power"
                                type="number"
                                value={request.battery.power}
                                onChange={(e) => {
                                    const power = clampNonNeg(Number(e.target.value));
                                    setBatteryPowerTouched(true);
                                    setRequest((r) => ({
                                        ...r,
                                        battery: r.battery ? {...r.battery, power} : r.battery,
                                    }));
                                }}
                                InputProps={{
                                    endAdornment: <InputAdornment position="end">kW</InputAdornment>,
                                }}
                                size="small"
                            />
                        </Stack>
                    </Stack>
                ) : (
                    <Typography variant="body2" color="text.secondary">
                        No Battery Installed.
                    </Typography>
                )}
            </Section>
        );
    };

    const insulationFormInner = () => (
        <Section title="Insulation">
            <Stack direction="row" spacing={1} flexWrap="wrap" justifyContent="flex-start">
                <ToggleButton
                    value="double_glazing"
                    selected={request.insulation.double_glazing}
                    onChange={() => toggleInsulation("double_glazing")}
                    size="small"
                    sx={{textTransform: "none"}}
                >
                    <WindowIcon fontSize="small"/>
                    <Box sx={{ml: 1}}>Double glazing</Box>
                </ToggleButton>

                <ToggleButton
                    value="cladding"
                    selected={request.insulation.cladding}
                    onChange={() => toggleInsulation("cladding")}
                    size="small"
                    sx={{textTransform: "none"}}
                >
                    <LayersIcon fontSize="small"/>
                    <Box sx={{ml: 1}}>Cladding</Box>
                </ToggleButton>

                <ToggleButton
                    value="loft"
                    selected={request.insulation.loft}
                    onChange={() => toggleInsulation("loft")}
                    size="small"
                    sx={{textTransform: "none"}}
                >
                    <RoofingIcon fontSize="small"/>
                    <Box sx={{ml: 1}}>Loft</Box>
                </ToggleButton>
            </Stack>
        </Section>
    );

    const siteForm = () => (
        <Accordion
            expanded={siteExpanded}
            onChange={(_, v) => setSiteExpanded(v)}
            disableGutters
            sx={{
                mb: 1,
                border: "1px solid",
                borderColor: "divider",
                borderRadius: 2,
                "&:before": {display: "none"},
            }}
        >
            <AccordionSummary
                expandIcon={<ExpandMoreIcon/>}
                sx={centreSummaryStyle}
            >
                <Typography variant="subtitle1" sx={{textAlign: "center", width: "100%"}}>
                    Site
                </Typography>
            </AccordionSummary>
            <AccordionDetails sx={{pt: 0, px: 2, pb: 2}}>{siteFormContent()}</AccordionDetails>
        </Accordion>
    );

    const componentsForm = () => (
        <Accordion
            expanded={componentsExpanded}
            onChange={(_, v) => setComponentsExpanded(v)}
            disableGutters
            sx={{
                border: "1px solid",
                borderColor: "divider",
                borderRadius: 2,
                "&:before": {display: "none"},
            }}
        >
            <AccordionSummary
                expandIcon={<ExpandMoreIcon/>}
                sx={centreSummaryStyle}
            >
                <Typography variant="subtitle1" sx={{textAlign: "center", width: "100%"}}>
                    Components
                </Typography>
            </AccordionSummary>
            <AccordionDetails sx={{pt: 0, px: 2, pb: 2}}>

                <Stack spacing={2}>
                <Typography variant="caption" color="text.secondary">
                    Choose the upgrades to make to your site
                </Typography>
                    {panelsFormInner()}
                    {heatFormInner()}
                    {batteryFormInner()}
                    {insulationFormInner()}
                </Stack>
            </AccordionDetails>
        </Accordion>
    );

    return (
        <Container maxWidth="md">
            {siteForm()}
            {componentsForm()}
            <Box my={1}>
                <Button variant="contained" fullWidth onClick={() => onSubmit(request)}>
                    Simulate
                </Button>
            </Box>
        </Container>
    );
};

export default DemoForm;
