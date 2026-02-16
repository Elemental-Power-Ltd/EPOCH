import { Dialog, DialogTitle, DialogContent, DialogActions, Button, TextField, MenuItem, Box, CircularProgress, Alert } from "@mui/material";
import { useState, useEffect } from "react";
import { getBundleContents } from "../../endpoints"; // adjust import path
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import { DatasetListResponse } from "../../Models/Endpoints";

interface UploadDatasetDialogProps {
    open: boolean;
    onClose: () => void;
    bundleId: string | null;
    onUploadSuccess: () => void;
}

const UploadDatasetDialog = ({ open, onClose, bundleId, onUploadSuccess }: UploadDatasetDialogProps) => {
    const [bundleContents, setBundleContents] = useState<DatasetListResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [selectedDatasetType, setSelectedDatasetType] = useState<string>("");
    const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");
    const [uploadedFile, setUploadedFile] = useState<File | null>(null);
    const [fabricCostBreakdown, setFabricCostBreakdown] = useState<string>("");
    const [error, setError] = useState<string | null>(null);
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        if (open && bundleId) {
            loadBundleContents();
        }
    }, [open, bundleId]);

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

    const getDatasetTypes = (): string[] => {
        if (!bundleContents) return [];
        const types = Object.keys(bundleContents).filter(
            (key) => bundleContents[key as keyof DatasetListResponse] && !["site_id", "start_ts", "end_ts", "is_complete", "is_error", "bundle_id", "ASHPData", "GasMeterData", "ElectricityMeterData", "CarbonIntensity"].includes(key)
        );
        return types;
    };

    const getDatasetIds = (): Array<{ id: string; label: string }> => {
        if (!bundleContents || !selectedDatasetType) return [];
        const datasets = bundleContents[selectedDatasetType as keyof DatasetListResponse];
        if (!datasets) return [];
        
        if (Array.isArray(datasets)) {
            return datasets.map((d) => ({
                id: d.dataset_id,
                label: d.dataset_subtype || d.dataset_id
            }));
        } else {
            return [{
                id: datasets.dataset_id,
                label: datasets.dataset_subtype || datasets.dataset_id
            }];
        }
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
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
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
                                setSelectedDatasetType(e.target.value);
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