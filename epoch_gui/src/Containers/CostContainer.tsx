import {useState} from "react";

import {
    Alert,
    Box,
    Button,
    CircularProgress,
    Container,
    GridLegacy as Grid,
    Paper,
    Stack,
    TextField,
    Typography,
} from "@mui/material";

import {addCostModel} from "../endpoints";
import {CostModelPicker} from "../Components/CostModel/CostModelPicker.tsx";
import {CostModelRequest, CostModelResponse} from "../Models/Endpoints.ts";

import {CostModelEditor} from "../Components/CostModel/CostModelEditor";
import defaultCostModelJson from "../Components/CostModel/AlchemaiModel.json";
import type {CapexModel, OpexModel} from "../Components/CostModel/Types.ts";
import {CostModelSaveError, CostModelSaveSuccess} from "../Components/CostModel/SaveResponsePages.tsx";


// A container for creating / viewing cost models

type Step = 1 | 2 | 3;
// 1 - pick cost model (new or existing)
// 2 - edit model
// 3 - show success/failure of add-cost-model

const CostContainer = () => {
    const [step, setStep] = useState<Step>(1);

    const [isLoadingAddModels, setIsLoadingAddModels] = useState(false);
    const [errorAddModels, setErrorAddModels] = useState<string | null>(null);

    const [costModel, setCostModel] = useState<CostModelResponse | null>(null);
    const [modelName, setModelName] = useState<string>("");

    const [savedModel, setSavedModel] = useState<CostModelResponse | null>(null);

    const resetState = () => {
        setIsLoadingAddModels(false);
        setErrorAddModels(null);
        setSavedModel(null);
    }

    const handleModelPicked = (model: CostModelResponse | null) => {
        resetState();

        if (!model) {
            setCostModel(null);
            setModelName("");
            return
        }

        setCostModel(model);
        setModelName(model!.model_name!);
        setStep(2);
    }

    const handleNewModel = () => {
        resetState();

        // only the capex_model and opex_model parameters matter here
        // the others are placeholders so we can use the existing type and will be replaced when we call /add-cost-model
        setCostModel({
            cost_model_id: "",
            model_name: "",
            capex_model: defaultCostModelJson.capex_model,
            opex_model: defaultCostModelJson.opex_model,
            created_at: ""
        })

        setModelName("");
        setStep(2);
    }

    const setCapex = (capexModel: CapexModel) => {
        if (!costModel) {
            return;
        }
        setCostModel({...costModel, capex_model: capexModel});
    }

    const setOpex = (opexModel: OpexModel) => {
        if (!costModel) {
            return;
        }
        setCostModel({...costModel, opex_model: opexModel});
    }

    const modelNameValid = () => modelName.trim().length > 0;
    const canSave = () => modelNameValid() && !isLoadingAddModels;

    const handleSaveModel = async () => {
        if (!costModel) {
            return;
        }

        setErrorAddModels(null);
        setIsLoadingAddModels(true);
        setSavedModel(null);

        const payload: CostModelRequest = {
            capex_model: costModel.capex_model,
            opex_model: costModel.opex_model,
            model_name: modelName.trim()
        }

        const res = await addCostModel(payload);

        if (res.error || !res.data) {
            setErrorAddModels(res.error ?? "Failed to save cost model.");
        } else {
            setSavedModel(res.data!);
            setStep(3);
        }
        setIsLoadingAddModels(false);

    }

    const backToStart = () => {
        resetState();
        setCostModel(null);
        setModelName("");
        setStep(1);
    }

    return (
        <Container maxWidth={"xl"}>

            {step === 1 && (
                <Paper variant="outlined" sx={{p: 3}}>
                    <Stack spacing={3}>
                        <Typography variant="h6">
                            Select Cost Model
                        </Typography>

                        <Grid container spacing={2}>
                            <Grid item xs={12} md={6}>
                                <Paper
                                    variant="outlined"
                                    sx={{
                                        p: 2,
                                        height: "90%",
                                        display: "flex",
                                        flexDirection: "column",
                                        gap: 2,
                                    }}
                                >
                                    <Typography variant="subtitle1" fontWeight={600}>
                                        Edit Cost Model
                                    </Typography>

                                    <CostModelPicker
                                        costModel={costModel}
                                        setCostModel={handleModelPicked}
                                    />
                                </Paper>
                            </Grid>

                            <Grid item xs={12} md={6}>
                                <Paper
                                    variant="outlined"
                                    sx={{
                                        p: 2,
                                        height: "90%",
                                        display: "flex",
                                        flexDirection: "column",
                                        gap: 2,
                                        justifyContent: "space-between",
                                    }}
                                >
                                    <Typography variant="subtitle1" fontWeight={600}>
                                        Create New Model
                                    </Typography>

                                    <Typography variant="body2" color="text.secondary">
                                        Start from the default model.
                                    </Typography>

                                    <Button
                                        variant="contained"
                                        size="large"
                                        onClick={handleNewModel}
                                    >
                                        New Cost Model
                                    </Button>
                                </Paper>
                            </Grid>
                        </Grid>
                    </Stack>
                </Paper>


            )}


            {step === 2 && costModel && (
                <Paper variant="outlined" sx={{p: 2}}>
                    <Stack spacing={2}>
                        <Box display="flex" justifyContent="space-between" alignItems="center">
                            <Typography variant="h6">Edit Model</Typography>
                            <Button variant="outlined" onClick={backToStart} disabled={isLoadingAddModels}>
                                Back
                            </Button>
                        </Box>

                        <CostModelEditor
                            capexModel={costModel.capex_model as CapexModel}
                            onChangeCapex={setCapex}
                            opexModel={costModel.opex_model as OpexModel}
                            onChangeOpex={setOpex}
                        />

                        <TextField
                            label="Model name"
                            value={modelName}
                            onChange={(e) => setModelName(e.target.value)}
                            required
                            fullWidth
                            error={!modelNameValid()}
                            helperText={!modelNameValid() ? "Required" : " "}
                        />

                        {errorAddModels && <Alert severity="error">{errorAddModels}</Alert>}

                        <Box display="flex" alignItems="center" gap={2}>
                            <Button variant="contained" onClick={handleSaveModel} disabled={!canSave()}>
                                Save Cost Model
                            </Button>
                            {isLoadingAddModels && <CircularProgress size={22}/>}
                        </Box>
                    </Stack>
                </Paper>
            )}


            {step === 3 && savedModel && (
                <CostModelSaveSuccess model={savedModel} onBack={backToStart}/>
            )}

            {step === 3 && errorAddModels && (
                <CostModelSaveError error={errorAddModels} onBack={backToStart}/>
            )}


        </Container>
    )
}

export default CostContainer
