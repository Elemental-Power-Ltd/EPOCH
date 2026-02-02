import {FC, useState} from "react";
import {Container, Stepper, Step, StepLabel} from "@mui/material";
import {Dayjs} from "dayjs";

import {useEpochStore} from "../State/Store";

import {TaskData} from "../Components/TaskDataViewer/TaskData.ts";

import SiteSelector from "../Components/Simulate/SiteSelector";
import Simulator from "../Components/Simulate/Simulator";


const steps = ["Configure Site", "Configure Components", "View Results"];

const SimulationContainer: FC = () => {
  const client_sites = useEpochStore(state => state.global.client_sites);

  const [activeStep, setActiveStep] = useState<0 | 1 | 2>(0);
  const [baseline, setBaseline] = useState<TaskData | null>(null);
  const [siteID, setSiteID] = useState<string>("");
  const [startDate, setStartDate] = useState<Dayjs | null>(null);
  const [_timestep, setTimestep] = useState<number>(30);

  const handleBaselineReady = (
    baseline: TaskData,
    siteID: string,
    startDate: Dayjs,
    timestep: number
  ) => {
    setBaseline(baseline);
    setSiteID(siteID);
    setStartDate(startDate);
    setTimestep(timestep);
    setActiveStep(1);
  };

  return (
    <Container maxWidth="xl">
      <Container maxWidth="md">
        <Stepper activeStep={activeStep} sx={{mb: 4}}>
          {steps.map(label => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
      </Container>

      {activeStep === 0 && (
        <SiteSelector
          clientSites={client_sites}
          onBaselineReady={handleBaselineReady}
        />
      )}

      {activeStep > 0 && baseline && startDate && (
        <Simulator
          baseline={baseline}
          siteID={siteID}
          startDate={startDate}
          onBackToSiteSelector={() => setActiveStep(0)}
        />
      )}
    </Container>
  );
};

export default SimulationContainer;
