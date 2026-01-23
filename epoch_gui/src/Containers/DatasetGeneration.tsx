import {useEffect, useState} from 'react';
import {
    Button,
    Grid,
    Container,
    Stepper, Step, StepButton
} from '@mui/material';
import dayjs, {Dayjs} from 'dayjs';
import 'dayjs/locale/en-gb';
import utc from 'dayjs/plugin/utc';
import {useEpochStore} from '../State/Store';

import {FuelType, PhppMetadata} from "../Models/Endpoints.ts";
import UploadMeterFileForm from '../Components/ConfigureSite/UploadMeterForm.tsx';
import AddSolarLocationForm from "../Components/ConfigureSite/AddSolarForm.tsx";
import UploadPhppForm from "../Components/ConfigureSite/UploadPhppForm.tsx";
import BaselineForm from "../Components/ConfigureSite/AddBaselineForm.tsx";
import AddOrEditSite from "../Components/ConfigureSite/AddOrEditSite.tsx";
import GenerateAllForm from "../Components/ConfigureSite/GenerateAllForm.tsx";
import {getPrepochStatus} from "../endpoints.tsx";
import {PrepochStatusDisplay} from "../Components/PrepochQueue/PrepochQueue.tsx";

dayjs.extend(utc);

const DatasetGenerationContainer = () => {

    const selectedClient = useEpochStore((state) => state.global.selectedClient);
    const sites = useEpochStore((state) => state.global.client_sites);

    const [step, setStep] = useState(0);
    const stepLabels = [
        "Select Site",
        "Upload Meter Files",
        "Add Solar Locations",
        "Configure Baseline",
        "Upload PHPP",
        "Generate Dataset",
    ];

    // state for generate-all
    const [selectedSite, setSelectedSite] = useState(sites.length === 1 ? sites[0].site_id : '');
    const [startDate, setStartDate] = useState<Dayjs | null>(dayjs("2022-01-01T00:00:00Z"));
    const [endDate, setEndDate] = useState<Dayjs | null>(dayjs("2023-01-01T00:00:00Z"));
    const [isGenerating, setIsGenerating] = useState(false);
    const [generationResult, setGenerationResult] = useState<any>(null);

    // state for upload-meter-file
    const [fuelType, setFuelType] = useState<FuelType>("gas");
    const [file, setFile] = useState<File | null>(null);
    const [meterFileLoading, setMeterFileLoading] = useState<boolean>(false);
    const [meterFileError, setMeterFileError] = useState<string | null>(null);

    // state for add-solar-location
    const [solarName, setSolarName] = useState<string>("");
    const [solarAzimuth, setSolarAzimuth] = useState<number | null>(null);
    const [solarTilt, setSolarTilt] = useState<number | null>(null);
    const [solarMaxPower, setSolarMaxPower] = useState<number | null>(null);
    const [solarMountingType, setSolarMountingType] = useState<"building-integrated" | "free">("building-integrated");
    const [solarLoading, setSolarLoading] = useState<boolean>(false);
    const [solarError, setSolarError] = useState<string | null>(null);

    // state for upload-phpp
    const [phppFile, setPhppFile] = useState<File | null>(null);
    const [phppLoading, setPhppLoading] = useState<boolean>(false);
    const [phppError, setPhppError] = useState<string | null>(null);
    const [phppMetadata, setPhppMetadata] = useState<PhppMetadata | null>(null);

    // state for baseline
    const [baselineLoading, setBaselineLoading] = useState<boolean>(false);
    const [baselineError, setBaselineError] = useState<string | null>(null);

    const [prepochQueueStatus, setPrepochQueueStatus] = useState<any>('OFFLINE');

    useEffect(() => {
        let cancelled = false;

        const pollPrepochStatus = async () => {
            if (cancelled) return;

            const response = await getPrepochStatus();
            if (!cancelled) {
                setPrepochQueueStatus(response);
            }

            setTimeout(pollPrepochStatus, 2000);
        };

        pollPrepochStatus();

        return () => {
            cancelled = true;
        };
    }, []);


    return (
        <Container maxWidth="md">
            <Stepper activeStep={step} alternativeLabel>
                {stepLabels.map((label, index) => (
                    <Step key={label}>
                        <StepButton
                            onClick={() => {
                                if (!selectedSite) {
                                    return;
                                }
                                setStep(index);
                            }}
                            disabled={!selectedSite}
                        >{label}</StepButton>
                    </Step>
                ))}
            </Stepper>

            {step === 0 && (
                <AddOrEditSite selectedSite={selectedSite} setSelectedSite={setSelectedSite}/>
            )}


            {step === 1 && (
                <UploadMeterFileForm
                    selectedClient={selectedClient}
                    selectedSite={selectedSite}
                    fuelType={fuelType}
                    setFuelType={setFuelType}
                    file={file}
                    setFile={setFile}
                    meterFileLoading={meterFileLoading}
                    setMeterFileLoading={setMeterFileLoading}
                    meterFileError={meterFileError}
                    setMeterFileError={setMeterFileError}
                />
            )}

            {step === 2 && (
                <AddSolarLocationForm
                    selectedSite={selectedSite}
                    solarName={solarName}
                    setSolarName={setSolarName}
                    solarAzimuth={solarAzimuth}
                    setSolarAzimuth={setSolarAzimuth}
                    solarTilt={solarTilt}
                    setSolarTilt={setSolarTilt}
                    solarMaxPower={solarMaxPower}
                    setSolarMaxPower={setSolarMaxPower}
                    solarMountingType={solarMountingType}
                    setSolarMountingType={setSolarMountingType}
                    solarLoading={solarLoading}
                    setSolarLoading={setSolarLoading}
                    solarError={solarError}
                    setSolarError={setSolarError}
                />
            )}

            {step === 3 && (
                <BaselineForm
                    selectedSite={selectedSite}
                    baselineLoading={baselineLoading}
                    setBaselineLoading={setBaselineLoading}
                    baselineError={baselineError}
                    setBaselineError={setBaselineError}
                />
            )}

            {step === 4 && (
                <UploadPhppForm
                    selectedClient={selectedClient}
                    selectedSite={selectedSite}
                    phppFile={phppFile}
                    setPhppFile={setPhppFile}
                    phppLoading={phppLoading}
                    setPhppLoading={setPhppLoading}
                    phppError={phppError}
                    setPhppError={setPhppError}
                    phppMetadata={phppMetadata}
                    setPhppMetadata={setPhppMetadata}
                />
            )}

            {step === 5 && (
                <>
                    <GenerateAllForm
                        selectedSite={selectedSite}
                        startDate={startDate}
                        setStartDate={setStartDate}
                        endDate={endDate}
                        setEndDate={setEndDate}
                        isGenerating={isGenerating}
                        setIsGenerating={setIsGenerating}
                        generationResult={generationResult}
                        setGenerationResult={setGenerationResult}
                    />
                    <PrepochStatusDisplay status={prepochQueueStatus}/>
                </>

            )}

            <Grid container spacing={2} sx={{mt: 3}}>
                <Grid item xs={6}>
                    <Button
                        fullWidth
                        variant="outlined"
                        disabled={step === 0}
                        onClick={() => setStep((s) => s - 1)}
                    >
                        Back
                    </Button>
                </Grid>

                <Grid item xs={6}>
                    <Button
                        fullWidth
                        variant="contained"
                        disabled={
                            step === stepLabels.length - 1 ||
                            (step === 0 && !selectedSite) // required step
                        }
                        onClick={() => setStep((s) => s + 1)}
                    >
                        Next
                    </Button>
                </Grid>
            </Grid>
        </Container>
    );
};

export default DatasetGenerationContainer;
