import { Dialog, DialogTitle, DialogContent, DialogActions, Button, TextField, MenuItem, Box, CircularProgress, Alert } from "@mui/material";
import { useState, useEffect } from "react";
import { getBundleContents } from "../../endpoints";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import {DatasetEntryResponse, DatasetListResponse} from "../../Models/Endpoints";

interface UploadDatasetDialogProps {
    open: boolean;
    onClose: () => void;
    bundleId: string | null;
    onUploadSuccess: () => void;
}

const UploadDatasetDialog = ({ open, onClose, bundleId, onUploadSuccess }: UploadDatasetDialogProps) => {

    const META_KEYS = [
        "site_id",
        "start_ts",
        "end_ts",
        "is_complete",
        "is_error",
        "bundle_id",
    ] as const;
    type MetaKey = typeof META_KEYS[number];
    type DatasetKey = Exclude<keyof DatasetListResponse, MetaKey>;

    const isDatasetEntry = (v: unknown): v is DatasetEntryResponse => {
        return typeof v === "object" && v !== null && "dataset_id" in v;
    };

    const isDatasetEntryArray = (v: unknown): v is DatasetEntryResponse[] => {
        return Array.isArray(v) && v.every(isDatasetEntry);
    };

    const HIDDEN_DATASET_KEYS = [
        "ASHPData",
        "GasMeterData",
        "ElectricityMeterData",
        "CarbonIntensity",
        "Weather",
        "ThermalModel",
        "PHPP"
    ] as const;

    type HiddenDatasetKey = typeof HIDDEN_DATASET_KEYS[number];
    type VisibleDatasetKey = Exclude<DatasetKey, HiddenDatasetKey>;


    const [bundleContents, setBundleContents] = useState<DatasetListResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [selectedDatasetType, setSelectedDatasetType] = useState<VisibleDatasetKey | "">("");
    const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");
    const [uploadedFile, setUploadedFile] = useState<File | null>(null);
    const [fabricCostBreakdown, setFabricCostBreakdown] = useState<string>("");
    const [error, setError] = useState<string | null>(null);
    const [submitting, setSubmitting] = useState(false);

    // track whether we've changed anything so that we know whether to refresh the SiteData upon close or not
    const [bundleChanged, setBundleChanged] = useState<boolean>(false);

    const loadBundleContents = async () => {
        setLoading(true);
        setError(null);
        const response = await getBundleContents(bundleId!);
        if (response.success && response.data) {
            setBundleContents(response.data);
        } else {
            setError(response.error || "Failed to load bundle contents");
        }
        setLoading(false);
    };

    useEffect(() => {
        if (open && bundleId) {
            loadBundleContents();
        }
    }, [open, bundleId]);

    const getDatasetTypes = (): VisibleDatasetKey[] => {
        if (!bundleContents) return [];

        return (Object.keys(bundleContents) as Array<keyof DatasetListResponse>)
            .filter((k): k is VisibleDatasetKey => {
                if ((META_KEYS as readonly string[]).includes(k as string)) return false;
                if ((HIDDEN_DATASET_KEYS as readonly string[]).includes(k as string)) return false;
                return true;
            });
    };

    const getDatasetIds = (): Array<{ id: string; label: string }> => {
        if (!bundleContents || !selectedDatasetType) return [];

        const value = bundleContents[selectedDatasetType];

        if (isDatasetEntryArray(value)) {
            return value.map((d) => ({
                id: d.dataset_id,
                label: d.dataset_subtype || d.dataset_id,
            }));
        }

        if (isDatasetEntry(value)) {
            return [{
                id: value.dataset_id,
                label: value.dataset_subtype || value.dataset_id,
            }];
        }

        return [];
    };

    const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files && event.target.files.length > 0) {
            setUploadedFile(event.target.files[0]);
        }
    };

    const handleSubmit = async () => {
        if (!selectedDatasetType || !selectedDatasetId || !uploadedFile) {
            setError("Please select a dataset type, dataset ID, and upload a file");
            return;
        }

        setSubmitting(true);
        setBundleChanged(true);
        setError(null);

        const formData = new FormData();
        formData.append("data", uploadedFile);

        const queryParams = new URLSearchParams({
            dataset_id: selectedDatasetId,
        });

        if (fabricCostBreakdown && selectedDatasetType === "HeatingLoad") {
            queryParams.append("fabric_cost_breakdown", fabricCostBreakdown);
        }

        try {
            const response = await fetch(`/api/data/replace-dataset?${queryParams.toString()}`, {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                let errorMessage = "Failed to upload dataset";
                try {
                    const errorData = await response.json();
                    if (errorData.detail) {
                        errorMessage = errorData.detail;
                    }
                } catch {
                    errorMessage = `HTTP error! Status: ${response.status}`;
                }
                throw new Error(errorMessage);
            }

            // Success - reset form but keep dialog open
            setSelectedDatasetType("");
            setSelectedDatasetId("");
            setUploadedFile(null);
            setFabricCostBreakdown("");
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to upload dataset");
        } finally {
            setSubmitting(false);
        }
    };

    const handleClose = async () => {
        if (!bundleChanged) {
            // no changes, we don't need to refresh
            onClose();
            return;
        }

        try {
            await fetch("/api/optimisation/clear-bundle-cache", {
                method: "POST",
            });
        } catch (err) {
            console.error("Failed to clear bundle cache:", err);
        }
        onUploadSuccess();
        onClose();
    };


    const datasetTypes = getDatasetTypes();
    const datasetIds = getDatasetIds();

    return (
        <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
            <DialogTitle>Upload Replacement Dataset</DialogTitle>
            <DialogContent sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 2 }}>
                {error && <Alert severity="error">{error}</Alert>}

                {loading ? (
                    <Box sx={{ display: "flex", justifyContent: "center", py: 3 }}>
                        <CircularProgress />
                    </Box>
                ) : (
                    <>
                        <TextField
                            select
                            label="Dataset Type"
                            value={selectedDatasetType}
                            onChange={(e) => {
                                setSelectedDatasetType(e.target.value as VisibleDatasetKey);
                                setSelectedDatasetId(""); // Reset dataset ID when type changes
                            }}
                            fullWidth
                            disabled={datasetTypes.length === 0}
                        >
                            {datasetTypes.map((type) => (
                                <MenuItem key={type} value={type}>
                                    {type}
                                </MenuItem>
                            ))}
                        </TextField>

                        <TextField
                            select
                            label="Dataset ID"
                            value={selectedDatasetId}
                            onChange={(e) => setSelectedDatasetId(e.target.value)}
                            fullWidth
                            disabled={datasetIds.length === 0 || !selectedDatasetType}
                        >
                            {datasetIds.map((item) => (
                                <MenuItem key={item.id} value={item.id}>
                                    {item.label}
                                </MenuItem>
                            ))}
                        </TextField>

                        <Button
                            variant="contained"
                            component="label"
                            startIcon={<CloudUploadIcon />}
                            fullWidth
                        >
                            {uploadedFile ? `File: ${uploadedFile.name}` : "Upload File"}
                            <input
                                type="file"
                                hidden
                                onChange={handleFileUpload}
                            />
                        </Button>

                        {fabricCostBreakdown !== null && selectedDatasetType === "HeatingLoad" && (
                            <TextField
                                label="Fabric Cost Breakdown (JSON)"
                                multiline
                                rows={4}
                                value={fabricCostBreakdown}
                                onChange={(e) => setFabricCostBreakdown(e.target.value)}
                                fullWidth
                                placeholder='{"key": "value"}'
                            />
                        )}
                    </>
                )}
            </DialogContent>
            <DialogActions>
                <Button onClick={handleClose}>Close</Button>
                <Button
                    onClick={handleSubmit}
                    variant="contained"
                    disabled={submitting || loading || !selectedDatasetType || !selectedDatasetId || !uploadedFile}
                >
                    {submitting ? <CircularProgress size={24} /> : "Submit"}
                </Button>
            </DialogActions>
        </Dialog>
    );
};

export default UploadDatasetDialog;