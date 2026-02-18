import {
    TextField,
    Button,
    GridLegacy as Grid,
    Typography,
    CircularProgress, MenuItem,
} from "@mui/material";
import {ChangeEvent, useEffect, useMemo} from "react";
import {addSiteRequest} from "../../Models/Endpoints.ts";
import {addSite} from "../../endpoints";

interface AddSiteFormProps {
    clientId: string;

    siteId: string;
    setSiteId: (value: string) => void;

    siteName: string;
    setSiteName: (value: string) => void;

    siteLocation: string;
    setSiteLocation: (value: string) => void;

    coordinates: [number, number] | null;
    setCoordinates: (value: [number, number] | null) => void;

    address: string;
    setAddress: (value: string) => void;

    postcode: string;
    setPostcode: (value: string) => void;

    epcLmk: string | null;
    setEpcLmk: (value: string | null) => void;

    decLmk: string | null;
    setDecLmk: (value: string | null) => void;

    siteLoading: boolean;
    setSiteLoading: (value: boolean) => void;

    siteError: string | null;
    setSiteError: (value: string | null) => void;

    onAdded?: (site: addSiteRequest) => void;
}

const toPostgresId = (raw: string): string => {
    // unquoted Postgres identifier-ish rules (safe subset):
    // letters, digits, underscore; cannot start with digit; max 63 chars
    let s = (raw ?? "")
        .trim()
        .toLowerCase()
        .replace(/\s+/g, "_")
        .replace(/[^a-z0-9_]/g, "_")
        .replace(/_+/g, "_")
        .replace(/^_+|_+$/g, "");

    if (!s) return "";
    if (/^\d/.test(s)) s = `id_${s}`;
    return s.slice(0, 63);
};

const epcBandFromScore = (score: number): "A" | "B" | "C" | "D" | "E" | "F" | "G" => {
    // EPC banding (SAP score) commonly used for 1–100:
    // A 92–100, B 81–91, C 69–80, D 55–68, E 39–54, F 21–38, G 1–20
    if (score >= 92) return "A";
    if (score >= 81) return "B";
    if (score >= 69) return "C";
    if (score >= 55) return "D";
    if (score >= 39) return "E";
    if (score >= 21) return "F";
    return "G";
};

const AddSiteForm = ({
                         clientId,
                         siteId,
                         setSiteId,
                         siteName,
                         setSiteName,
                         siteLocation,
                         setSiteLocation,
                         coordinates,
                         setCoordinates,
                         address,
                         setAddress,
                         postcode,
                         setPostcode,
                         epcLmk,
                         setEpcLmk,
                         decLmk,
                         setDecLmk,
                         siteLoading,
                         setSiteLoading,
                         siteError,
                         setSiteError,
                         onAdded,
                     }: AddSiteFormProps) => {
    // Derived site_id: clientId + siteName (replaces user-entered Site ID field)
    const derivedSiteId = useMemo(() => {
        const combined = `${clientId} ${siteName}`; // join + then normalize spaces to underscores in toPostgresId
        return toPostgresId(combined);
    }, [clientId, siteName]);

    // keep parent state in sync (optional but handy if parent uses siteId elsewhere)
    useEffect(() => {
        if (derivedSiteId && siteId !== derivedSiteId) {
            setSiteId(derivedSiteId);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [derivedSiteId]);

    const handleCoordinateChange =
        (index: 0 | 1) => (e: ChangeEvent<HTMLInputElement>) => {
            const raw = e.target.value;

            if (raw === "") {
                setCoordinates(null);
                return;
            }

            const num = Number(raw);
            if (Number.isNaN(num)) return;

            const next: [number, number] = coordinates ?? [0, 0];
            next[index] = num;
            setCoordinates([next[0], next[1]]);
        };

    // EPC: only A-G (optional)
    const handleEpcChange = (e: ChangeEvent<HTMLInputElement>) => {
        const raw = e.target.value.trim().toUpperCase();
        if (raw === "") {
            setEpcLmk(null);
            return;
        }
        const ch = raw[raw.length - 1]; // keep last typed char
        if (/^[A-G]$/.test(ch)) setEpcLmk(ch);
    };

    // DEC: integer 1-100 (optional)
    const handleDecChange = (e: ChangeEvent<HTMLInputElement>) => {
        const raw = e.target.value;
        if (raw === "") {
            setDecLmk(null);
            return;
        }
        const num = Number(raw);
        if (!Number.isFinite(num) || !Number.isInteger(num)) return;
        if (num < 1 || num > 100) return;
        setDecLmk(String(num));
    };

    const epcValid = epcLmk === null || /^[A-G]$/.test(epcLmk);
    const decNum = decLmk === null ? null : Number(decLmk);
    const decValid =
        decLmk === null ||
        (Number.isInteger(decNum) && decNum! >= 1 && decNum! <= 100);

    // If both provided, DEC score must land in the EPC band
    const bandMatch =
        epcLmk === null ||
        decNum === null ||
        !decValid ||
        epcLmk === epcBandFromScore(decNum);

    const canSubmitSite = (): boolean => {
        return (
            !!clientId &&
            !!siteName &&
            !!siteLocation &&
            !!address &&
            !!postcode &&
            coordinates !== null &&
            derivedSiteId.length > 0 &&
            !siteLoading &&
            epcValid &&
            decValid &&
            bandMatch
        );
    };

    const handleAddSite = async () => {
        if (!canSubmitSite()) return;

        setSiteLoading(true);
        setSiteError(null);

        const payload: addSiteRequest = {
            client_id: clientId,
            site_id: derivedSiteId,
            name: siteName,
            location: siteLocation,
            coordinates: coordinates!,
            address: `${address}, ${postcode}`,
            epc_lmk: epcLmk,
            dec_lmk: decLmk,
        };

        try {
            const res = await addSite(payload);

            setSiteLoading(false);
            if (res.success && res.data) {
                setSiteError(null);
                onAdded?.(res.data);
            } else {
                setSiteError(res.error ?? "Unknown Error");
            }
        } catch {
            setSiteError("Unknown Error");
            setSiteLoading(false);
        }
    };

    const decHelper =
        decLmk !== null && decNum !== null && decValid && epcLmk
            ? `DEC score maps to EPC band ${epcBandFromScore(decNum)}`
            : " ";

    return (
        <>
            <Typography variant="h5" gutterBottom mt={2}>
                Add Site
            </Typography>

            <Grid container spacing={2}>

                <Grid item xs={12}>
                    <TextField
                        fullWidth
                        label="Name"
                        value={siteName}
                        onChange={(e) => setSiteName(e.target.value)}
                    />
                </Grid>

                <Grid item xs={12}>
                    <TextField
                        fullWidth
                        label="Weather Station Location (Nearest Town)"
                        value={siteLocation}
                        onChange={(e) => setSiteLocation(e.target.value)}
                    />
                </Grid>

                <Grid item xs={12}>
                    <Grid container spacing={2}>
                        <Grid item xs={6}>
                            <TextField
                                fullWidth
                                label="Latitude"
                                type="number"
                                value={coordinates ? coordinates[0] : ""}
                                onChange={handleCoordinateChange(0)}
                            />
                        </Grid>

                        <Grid item xs={6}>
                            <TextField
                                fullWidth
                                label="Longitude"
                                type="number"
                                value={coordinates ? coordinates[1] : ""}
                                onChange={handleCoordinateChange(1)}
                            />
                        </Grid>
                    </Grid>
                </Grid>

                <Grid item xs={12}>
                    <TextField
                        fullWidth
                        label="Address"
                        value={address}
                        onChange={(e) => setAddress(e.target.value)}
                    />
                </Grid>

                <Grid item xs={12}>
                    <TextField
                        fullWidth
                        label="Postcode"
                        value={postcode}
                        onChange={(e) => setPostcode(e.target.value)}
                    />
                </Grid>

                <Grid item xs={12}>
                    <TextField
                        fullWidth
                        select
                        label="EPC Rating [optional]"
                        value={epcLmk ?? ""}
                        onChange={handleEpcChange}
                        error={!epcValid || !bandMatch}
                    >
                        <MenuItem value="">-</MenuItem>
                        <MenuItem value="A">A</MenuItem>
                        <MenuItem value="B">B</MenuItem>
                        <MenuItem value="C">C</MenuItem>
                        <MenuItem value="D">D</MenuItem>
                        <MenuItem value="E">E</MenuItem>
                        <MenuItem value="F">F</MenuItem>
                        <MenuItem value="G">G</MenuItem>
                    </TextField>
                </Grid>

                <Grid item xs={12}>
                    <TextField
                        fullWidth
                        label="DEC Score (1–100) [optional]"
                        type="number"
                        value={decLmk ?? ""}
                        onChange={handleDecChange}
                        inputProps={{min: 1, max: 100, step: 1}}
                        error={!decValid || !bandMatch}
                        helperText={
                            !decValid
                                ? "DEC must be an integer between 1 and 100."
                                : !bandMatch && decNum !== null && epcLmk
                                    ? `DEC score ${decNum} maps to EPC band ${epcBandFromScore(decNum)} (doesn't match EPC ${epcLmk}).`
                                    : decHelper
                        }
                    />
                </Grid>

                {siteError && (
                    <Grid item xs={12}>
                        <Typography variant="body2" color="error">
                            {siteError}
                        </Typography>
                    </Grid>
                )}

                <Grid item xs={12}>
                    <Button
                        fullWidth
                        variant="contained"
                        color="primary"
                        disabled={!canSubmitSite()}
                        onClick={handleAddSite}
                    >
                        {siteLoading ? <CircularProgress size={24}/> : "Add Site"}
                    </Button>
                </Grid>
            </Grid>
        </>
    );
};

export default AddSiteForm;
