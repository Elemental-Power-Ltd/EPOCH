import {Button, CircularProgress, Grid, Typography} from "@mui/material";
import {LocalizationProvider} from "@mui/x-date-pickers/LocalizationProvider";
import {AdapterDayjs} from "@mui/x-date-pickers/AdapterDayjs";
import {DateTimePicker} from "@mui/x-date-pickers/DateTimePicker";

import {Dayjs} from 'dayjs';

import {generateAllData} from "../../endpoints.tsx";


interface GenerateAllFormProps {
    selectedSite: string;
    startDate: Dayjs | null;
    setStartDate: (date: Dayjs | null) => void;
    endDate: Dayjs | null;
    setEndDate: (date: Dayjs | null) => void;
    isGenerating: boolean;
    setIsGenerating: (generating: boolean) => void;
    generationResult: any;
    setGenerationResult: (result: any) => void;
}


const GenerateAllForm = ({
    selectedSite,
    startDate,
    setStartDate,
    endDate,
    setEndDate,
    isGenerating,
    setIsGenerating,
    generationResult,
    setGenerationResult
}: GenerateAllFormProps) => {


    const handleGenerateDataset = async () => {
        setIsGenerating(true);
        setGenerationResult(null);
        try {
            const result = await generateAllData(
                selectedSite,
                startDate!.utc().format('YYYY-MM-DDTHH:mm:ss[Z]'),
                endDate!.utc().format('YYYY-MM-DDTHH:mm:ss[Z]')
            );
            setGenerationResult(result);
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            setGenerationResult({error: `Failed to generate dataset due to ${errorMessage}`});
        } finally {
            setIsGenerating(false);
        }
    };


    return (
        <>
            <Typography variant="h5" gutterBottom>
                Generate Dataset
            </Typography>

            <Grid container spacing={2}>
                <Grid item xs={6}>
                    <LocalizationProvider dateAdapter={AdapterDayjs} adapterLocale={"en-gb"}>
                        <DateTimePicker
                            label="Start Date"
                            value={startDate}
                            onChange={(date) => setStartDate(date)}
                        />
                    </LocalizationProvider>
                </Grid>
                <Grid item xs={6}>
                    <LocalizationProvider dateAdapter={AdapterDayjs}>
                        <DateTimePicker
                            label="End Date"
                            value={endDate}
                            onChange={(date) => setEndDate(date)}
                        />
                    </LocalizationProvider>
                </Grid>
                <Grid item xs={12}>
                    <Button
                        fullWidth
                        variant="contained"
                        color="primary"
                        onClick={handleGenerateDataset}
                        disabled={!selectedSite || isGenerating}
                    >
                        {isGenerating ? <CircularProgress size={24}/> : 'Generate Dataset'}
                    </Button>
                </Grid>
                {generationResult && (
                    <Grid item xs={12}>
                        <Typography variant="body1">
                            {generationResult.error
                                ? `Error: ${generationResult.error}`
                                : `Dataset generated successfully: ${JSON.stringify(generationResult)}`}
                        </Typography>
                    </Grid>
                )}
            </Grid>

        </>
    )
}

export default GenerateAllForm;
