import {FC, useState} from "react";
import {Box, Button, Paper} from "@mui/material";
import {SubmitSimulationRequest, SimulationResult, CostModelResponse} from "../../Models/Endpoints";
import {submitSimulation} from "../../endpoints";
import {Dayjs} from "dayjs";
import {useComponentBuilderState} from "../ComponentBuilder/useComponentBuilderState";
import {validateTaskData} from "../ComponentBuilder/ValidateBuilders";
import ComponentBuilderForm from "../ComponentBuilder/ComponentBuilderForm";
import SimulationResultViewer from "../Results/SimulationResultViewer";
import {TaskData} from "../TaskDataViewer/TaskData.ts";

import {CostModelPicker} from "../CostModel/CostModelPicker.tsx";

interface Props {
  baseline: TaskData;
  siteID: string;
  startDate: Dayjs;
  onBackToSiteSelector: () => void;
}

const Simulator: FC<Props> = ({baseline, siteID, startDate, onBackToSiteSelector}) => {
  // step 1: Component Builder
  // step 2: Results Viewer
  const [step, setStep] = useState<1 | 2>(1);

  const componentBuilderState = useComponentBuilderState("TaskDataMode", baseline);
  const getTaskData = componentBuilderState.getComponents;

  const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

    const [costModel, setCostModel] = useState<CostModelResponse | null>(null);

  const runSimulation = async () => {
    setIsLoading(true);
    setError(null);
    setSimulationResult(null);

    const taskData = getTaskData();
    const validation = validateTaskData(taskData);
    if (!validation.valid) {
      setError("Invalid TaskData – check console.");
      console.error("Invalid TaskData", validation.result);
      setIsLoading(false);
      return;
    }

    const request: SubmitSimulationRequest = {
      task_data: taskData,
      site_data: {
        site_id: siteID,
        start_ts: startDate.toISOString(),
        end_ts: startDate.add(8760, "hour").toISOString(),
      },
      config: {
        ...componentBuilderState.siteInfo.config,
        capex_model: costModel!.capex_model,
        opex_model: costModel!.opex_model
      }
    };

    try {
      const res = await submitSimulation(request);
      if (res.success) {
        setSimulationResult(res.data);
      } else {
        setError("Simulation failed – see server logs.");
      }
    } catch (e) {
      setError("Network / unexpected simulation error.");
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const canSimulate = () => {
    if (!costModel) {
      return false;
    }
    return true;
  }

  const handleNext = async () => {
    if (step === 1) {
      // Immediately switch to the results viewer and set as loading
      setStep(2);
      setIsLoading(true);
      await runSimulation();
    }
  };

  const handleBack = () => {
      if (step === 2) {
          // from result to component builder
          setStep(1);
      } else if (step === 1) {
          // from component builder back to site selection
          onBackToSiteSelector();
      }
  }

  return (
    <>
      {step === 1 && (
          <>
          <ComponentBuilderForm
            mode="TaskDataMode"
            siteInfo={componentBuilderState.siteInfo}
            addComponent={componentBuilderState.addComponent}
            removeComponent={componentBuilderState.removeComponent}
            updateComponent={componentBuilderState.updateComponent}
            setComponents={componentBuilderState.setComponents}
            getComponents={getTaskData}
            setConfig={componentBuilderState.setConfig}
            site_id={siteID}
          />

          <Box my={2}>
              <Paper variant="outlined" sx={{ p: 1 }}>
                  <CostModelPicker costModel={costModel} setCostModel={setCostModel}/>
              </Paper>
          </Box>

        </>
      )}

      {step === 2 && (
        <SimulationResultViewer
          isLoading={isLoading}
          error={error}
          result={simulationResult}
        />
      )}

      <div style={{marginTop: "2rem", display: "flex", justifyContent: "space-between"}}>
        <Button onClick={handleBack}>Back</Button>
        {step === 1 && (
          <Button variant="contained" color="primary" onClick={handleNext} disabled={!canSimulate()}>
            Simulate
          </Button>
        )}
      </div>
    </>
  );
};

export default Simulator;
