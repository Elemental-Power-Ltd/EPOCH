import React, {FC, useState} from "react";

import {
    Button,
    Container,
    Stepper,
    Step,
    StepLabel,
} from "@mui/material";

import {submitSimulation} from "../endpoints";
import {SubmitSimulationRequest, SimulationResult} from "../Models/Endpoints";

import {useComponentBuilderState} from "../Components/ComponentBuilder/useComponentBuilderState";
import {validateTaskData} from "../Components/ComponentBuilder/ValidateBuilders";
import SiteDataForm from "../Components/TaskConfig/SiteDataForm";
import {useEpochStore} from "../State/Store";
import SimulationResultViewer from "../Components/Results/SimulationResultViewer";
import dayjs, {Dayjs} from "dayjs";
import ComponentBuilderForm from "../Components/ComponentBuilder/ComponentBuilderForm";

const simulationSteps = [
    "Configure Site",
    "Configure Components",
    "View Results",
];

const SimulationContainer: FC = () => {

    // --------------------------
    // Simulation / Error state
    // --------------------------
    const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    // --------------------------
    // SiteData form
    // --------------------------

    const client_sites = useEpochStore((state) => state.global.client_sites);
    const [siteID, setSiteID] = useState<string>("");
    const [startDate, setStartDate] = useState<Dayjs|null>(dayjs("2022-01-01T00:00:00Z"));
    const [timestep, setTimestep] = useState<number>(30);


    // --------------------------
    // Stepper State
    // --------------------------
    const [activeStep, setActiveStep] = useState<number>(0);

    // --------------------------
    // TaskData selection state
    // --------------------------
    const componentBuilderState = useComponentBuilderState("TaskDataMode");
    // we alias getComponents as getTaskData to make it slightly clearer
    const getTaskData = componentBuilderState.getComponents;

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
                loc: "remote",
                site_id: siteID,
                start_ts: startDate!.toISOString(),
                // an EPOCH year is exactly 8760 hours (irrespective of leap years)
                end_ts: startDate!.add(8760, "hour").toISOString()
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
            const isSiteIdValid = client_sites.some(site => site.site_id === siteID);
            const isStartDateValid = Boolean(startDate);
            const isDurationValid = Boolean(timestep);

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
                        siteId={siteID}
                        onSiteChange={setSiteID}
                        startDate={startDate}
                        onStartDateChange={setStartDate}
                        timestepMinutes={timestep}
                        onTimestepChange={setTimestep}
                        clientSites={client_sites}
                    />
                );
            case 1:
                // Step 1: Configure Components
                return (<ComponentBuilderForm
                    mode={"TaskDataMode"}
                    componentsMap={componentBuilderState.componentsState}
                    addComponent={componentBuilderState.addComponent}
                    removeComponent={componentBuilderState.removeComponent}
                    updateComponent={componentBuilderState.updateComponent}
                    setComponents={componentBuilderState.setComponents}
                    getComponents={getTaskData}
                    />)

            case 2:
                return (
                    <SimulationResultViewer
                        isLoading={isLoading}
                        error={error}
                        result={simulationResult}
                    />);
        }
    };

    return (
        <Container maxWidth={"xl"}>
            <Container maxWidth={"md"}>
                <Stepper activeStep={activeStep} style={{marginBottom: "2rem"}}>
                    {simulationSteps.map((label) => (
                        <Step key={label}>
                            <StepLabel>{label}</StepLabel>
                        </Step>
                    ))}
                </Stepper>
            </Container>

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
        </Container>
    );
};

export default SimulationContainer;
