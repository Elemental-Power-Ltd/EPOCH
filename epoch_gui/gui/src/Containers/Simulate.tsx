import React, {FC, useState} from "react";

import {
    Button,
    Stepper,
    Step,
    StepLabel,
    Skeleton,
    Alert,
    Typography,
} from "@mui/material";

import FileUploadIcon from "@mui/icons-material/FileUpload";
import FileDownloadIcon from "@mui/icons-material/FileDownload";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";

import {ComponentType} from "../Models/Core/TaskData";
import TaskComponentSelector from "../Components/TaskData/TaskComponentSelector";
import {ComponentWidget} from "../Components/TaskData/TaskComponents/ComponentWidget";
import SimulationSummary, {
    ErroredSimulationSummary,
    LoadingSimulatingSummary
} from "../Components/Results/SimulationSummary";

import {submitSimulation} from "../endpoints";
import {SubmitSimulationRequest, SimulationResult} from "../Models/Endpoints";

import {useTaskComponentsState} from "../State/useComponentsState";
import {useTaskDataFileHandlers} from "../Components/TaskData/useTaskDataFileHandlers";
import {validateTaskData} from "../Components/TaskData/validateTaskData";
import SiteDataForm from "../Components/TaskConfig/SiteDataForm";
import {useEpochStore} from "../State/state";
import {TaskConfig} from "../State/types";

const simulationSteps = [
    "Configure Site",
    "Configure Components",
    "View Results",
];

const SimulationContainer: FC = () => {
    const {
        componentsState,
        addComponent,
        removeComponent,
        updateComponent,
        setTaskData,
        getTaskData
    } = useTaskComponentsState();

    const {onUpload, onDownload, onCopy} = useTaskDataFileHandlers({
        setTaskData: setTaskData
    });

    // --------------------------
    // Simulation / Error state
    // --------------------------
    const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    // --------------------------
    // TaskConfig / SiteData form
    // --------------------------

    // This uses the same state as the Optimisation Container
    const taskConfig = useEpochStore((state) => state.run.taskConfig);
    const setTaskConfig = useEpochStore((state) => state.setTaskConfig);
    const client_sites = useEpochStore((state) => state.global.client_sites);

    const handleChange = (field: keyof TaskConfig, value: any) => {
        setTaskConfig({[field]: value});
    };

    // --------------------------
    // Stepper State
    // --------------------------
    const [activeStep, setActiveStep] = useState<number>(0);

    // -------------------------
    // TaskData selection state
    // -------------------------

    const selectedComponents = Object.entries(componentsState)
        .filter(([_, {selected}]) => selected)
        .map(([key]) => key as ComponentType);


    const handleTaskComponentChange = (component: ComponentType, evt: any) => {
        updateComponent(component, evt.formData);
    };

    // --------------------------
    // Simulation Submission
    // --------------------------
    const handleSubmitSimulation = async () => {
        setIsLoading(true);
        setError(null);
        setSimulationResult(null);

        const taskData = getTaskData();
        const validation = validateTaskData(taskData);

        if (!validation.valid) {
            // Immediately fail if taskData is invalid
            setError("Invalid TaskData: " + JSON.stringify(validation.result));
            console.error("Invalid TaskData", validation.result);
            setIsLoading(false);
            return;
        }

        const request: SubmitSimulationRequest = {
            task_data: taskData,
            site_data: {
                duration: taskConfig.duration,
                loc: "remote",
                site_id: taskConfig.site_id,
                start_ts: taskConfig.start_date
            }
        };

        try {
            const response = await submitSimulation(request);
            if (response.success) {
                setSimulationResult(response.data);
            } else {
                // Handle a server-side error or unsuccessful result
                setError("Simulation failed, please check the logs.");
            }
        } catch (err) {
            // Handle a network or unexpected error
            setError("An error occurred while submitting the simulation.");
            console.error("Simulation error:", err);
        } finally {
            setIsLoading(false);
        }
    };

    // --------------------------
    // Navigation Logic
    // --------------------------

    /**
     * Determines if user can move from the current step to the next.
     *
     * For now, this function users an alert if the state is not valid to keep control flow simpler
     * Disabling the next button would be better but validating TaskData on every state change is expensive
     * @returns boolean
     */
    const canProgress = (): boolean => {
        // to progress to 'Configure Components' the site data must be valid
        if (activeStep === 0) {
            const {site_id, start_date, duration} = taskConfig;
            const isSiteIdValid = client_sites.some(site => site.site_id === site_id);
            const isStartDateValid = Boolean(start_date);
            const isDurationValid = Boolean(duration);

            const siteDataIsValid: boolean = isSiteIdValid && isStartDateValid && isDurationValid;
            if (!siteDataIsValid) {
                alert("Invalid Site Data");
            }
            return siteDataIsValid;
        }

        // to progress to 'View Results' the taskData must be valid
        if (activeStep === 1) {
            const taskData = getTaskData();
            const validation = validateTaskData(taskData);

            if (!validation.valid) {
                alert("Invalid TaskData – see console for details.");
                console.error("Invalid TaskData", validation.result);
            }

            return validation.valid;
        }

        // this should be unreachable
        return true;
    };


    const handleNext = async () => {
        // First check if progression is allowed
        if (!canProgress()) {
            return;
        }

        // If we’re about to move from step 1 (Configure Components) to step 2 (View Results),
        // run the simulation.
        if (activeStep === 1) {
            setActiveStep((prevStep) => prevStep + 1);
            await handleSubmitSimulation();
        } else {
            setActiveStep((prevStep) => prevStep + 1);
        }
    };

    const handleBack = () => {
        setActiveStep((prevStep) => prevStep - 1);
    };

    // --------------------------
    // Step Content
    // --------------------------
    const getStepContent = (step: number) => {
        switch (step) {
            case 0:
                // Step 0: Configure Site
                return (
                    <SiteDataForm
                        siteId={taskConfig.site_id}
                        onSiteChange={(val) => handleChange("site_id", val)}
                        startDate={taskConfig.start_date}
                        onStartDateChange={(val) => handleChange("start_date", val)}
                        timestepMinutes={taskConfig.timestep_minutes}
                        onTimestepChange={(val) => handleChange("timestep_minutes", val)}
                        clientSites={client_sites}
                    />
                );
            case 1:
                // Step 1: Configure Components
                return (
                    <>
                        <TaskComponentSelector
                            componentsState={componentsState}
                            onAddComponent={addComponent}
                        />

                        <div style={{
                            display: "flex",
                            flexWrap: "wrap",
                            gap: "16px",
                            margin: "1rem 0"
                        }}>
                            {selectedComponents.map((component) => (
                                <ComponentWidget
                                    key={component}
                                    componentKey={component}
                                    displayName={componentsState[component].displayName}
                                    onRemove={removeComponent}
                                    data={componentsState[component].data}
                                    onFormChange={handleTaskComponentChange}
                                />
                            ))}
                        </div>

                        <div style={{marginTop: "1rem", display: "flex", gap: "8px"}}>
                            <label htmlFor="upload-taskData">
                                <input
                                    id="upload-taskData"
                                    type="file"
                                    accept=".json"
                                    onChange={onUpload}
                                    style={{display: "none"}}
                                />
                                <Button
                                    variant="outlined"
                                    component="span"
                                    size="large"
                                    startIcon={<FileUploadIcon/>}
                                >
                                    Upload
                                </Button>
                            </label>
                            <Button
                                variant="outlined"
                                startIcon={<FileDownloadIcon/>}
                                onClick={() => onDownload(getTaskData())}
                            >
                                Download
                            </Button>

                            <Button
                                variant="outlined"
                                startIcon={<ContentCopyIcon/>}
                                onClick={async () => await onCopy(getTaskData())}
                            >
                                Copy
                            </Button>
                        </div>
                    </>
                );
            case 2:
                // Step 2: View Results
                if (isLoading) {
                    return <LoadingSimulatingSummary/>;
                }

                if (error) {
                    return <ErroredSimulationSummary error={error}/>;
                }

                return simulationResult
                    ? <SimulationSummary result={simulationResult}/>
                    : <Typography>No simulation results yet.</Typography>

            default:
                return <div>Unknown step</div>;
        }
    };

    return (
        <div style={{maxWidth: 900, margin: "0 auto"}}>
            <Stepper activeStep={activeStep} style={{marginBottom: "2rem"}}>
                {simulationSteps.map((label) => (
                    <Step key={label}>
                        <StepLabel>{label}</StepLabel>
                    </Step>
                ))}
            </Stepper>

            {getStepContent(activeStep)}

            <div style={{marginTop: "2rem", display: "flex", justifyContent: "space-between"}}>
                <Button
                    disabled={activeStep === 0}
                    onClick={handleBack}
                >
                    Back
                </Button>
                {/* only show the next/simulate button if there is another step */}
                {activeStep < simulationSteps.length - 1 && (
                    <Button
                        variant="contained"
                        color="primary"
                        onClick={handleNext}
                    >
                        {activeStep === simulationSteps.length - 2 ? "Simulate" : "Next"}
                    </Button>
                )}
            </div>
        </div>
    );
};

export default SimulationContainer;
