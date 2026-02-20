import {useEffect, useMemo, useState} from "react";
import {
    GridLegacy as Grid,
    Typography,
    RadioGroup,
    FormControlLabel,
    Radio,
    TextField,
    MenuItem,
    Divider,
} from "@mui/material";
import {useEpochStore} from "../../State/Store";
import {addSiteRequest} from "../../Models/Endpoints.ts";
import AddSiteForm from "./AddSiteForm.tsx";
import {Site} from "../../State/types.ts";

type Mode = "existing" | "add";

interface AddOrEditSiteProps {
    selectedSite: string;
    setSelectedSite: (siteId: string) => void;
    onSuccess: (message: string) => void;
}

const AddOrEditSite = ({selectedSite, setSelectedSite, onSuccess}: AddOrEditSiteProps) => {
    const selectedClient = useEpochStore((s) => s.global.selectedClient);
    const sites = useEpochStore((s) => s.global.client_sites);
    const addClientSite = useEpochStore((s) => s.addClientSite);

    const hasSites = sites.length > 0;

    const defaultMode: Mode = useMemo(() => {
        if (selectedSite) return "existing";
        return hasSites ? "existing" : "add";
    }, [selectedSite, hasSites]);

    const [mode, setMode] = useState<Mode>(defaultMode);
    useEffect(() => setMode(defaultMode), [defaultMode]);

    // --- AddSiteForm state (owned here) ---
    const [clientId, setClientId] = useState<string>(selectedClient?.client_id ?? "");
    const [siteId, setSiteId] = useState<string>("");
    const [siteName, setSiteName] = useState<string>("");
    const [siteLocation, setSiteLocation] = useState<string>("");
    const [coordinates, setCoordinates] = useState<[number, number] | null>(null);
    const [address, setAddress] = useState<string>("");
    const [postcode, setPostcode] = useState<string>("");
    const [epcLmk, setEpcLmk] = useState<string | null>(null);
    const [decLmk, setDecLmk] = useState<string | null>(null);

    const [siteLoading, setSiteLoading] = useState<boolean>(false);
    const [siteError, setSiteError] = useState<string | null>(null);

    const handleModeChange = (nextMode: Mode) => {
        setMode(nextMode);

        if (nextMode === "add") {
            // Clear selection so step 0 becomes blocking again
            setSelectedSite("");
        }
    };

    // keep clientId synced to selected client
    useEffect(() => {
        setClientId(selectedClient?.client_id ?? "");
    }, [selectedClient?.client_id]);

    const handleAdded = (site: addSiteRequest) => {

        const s: Site = {site_id: site.site_id, name: site.name};
        addClientSite(s);
        setSelectedSite(site.site_id);
        onSuccess(`${site.name} added successfully!`)

        // reset the state after adding a site
        setSiteId("");
        setSiteName("");
        setSiteLocation("");
        setCoordinates(null);
        setAddress("");
        setPostcode("");
        setEpcLmk(null);
        setDecLmk(null);
        setSiteError(null);

        // switch back to existing mode
        setMode("existing");
    };

    return (
        <>
            <Typography variant="h5" gutterBottom>
                Site
            </Typography>

            <RadioGroup
                row
                value={mode}
                onChange={(e) => handleModeChange(e.target.value as Mode)}
            >
                <FormControlLabel
                    value="existing"
                    control={<Radio/>}
                    label="Select existing"
                    disabled={!hasSites}
                />
                <FormControlLabel value="add" control={<Radio/>} label="Add new"/>
            </RadioGroup>

            <Divider sx={{my: 2}}/>

            {mode === "existing" && (
                <Grid container spacing={2}>
                    <Grid item xs={12}>
                        <TextField
                            fullWidth
                            select
                            label="Site"
                            value={selectedSite}
                            onChange={(e) => setSelectedSite(e.target.value)}
                            disabled={!selectedClient || !hasSites}
                            helperText={
                                !selectedClient
                                    ? "Select a client first"
                                    : !hasSites
                                        ? "No sites available yet"
                                        : undefined
                            }
                        >
                            {sites.map((s) => (
                                <MenuItem key={s.site_id} value={s.site_id}>
                                    {s.name}
                                </MenuItem>
                            ))}
                        </TextField>
                    </Grid>
                </Grid>
            )}

            {mode === "add" && (
                <AddSiteForm
                    clientId={clientId}
                    siteId={siteId}
                    setSiteId={setSiteId}
                    siteName={siteName}
                    setSiteName={setSiteName}
                    siteLocation={siteLocation}
                    setSiteLocation={setSiteLocation}
                    coordinates={coordinates}
                    setCoordinates={setCoordinates}
                    address={address}
                    setAddress={setAddress}
                    postcode={postcode}
                    setPostcode={setPostcode}
                    epcLmk={epcLmk}
                    setEpcLmk={setEpcLmk}
                    decLmk={decLmk}
                    setDecLmk={setDecLmk}
                    siteLoading={siteLoading}
                    setSiteLoading={setSiteLoading}
                    siteError={siteError}
                    setSiteError={setSiteError}
                    onAdded={handleAdded}
                />
            )}
        </>
    );
};

export default AddOrEditSite;
