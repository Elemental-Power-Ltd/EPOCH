import React, {useState} from 'react';


import SimulationSummary from "./SimulationSummary";
import DataViz from "../DataViz/DataViz";
import {SimulationResult} from "../../Models/Endpoints";
import {Button, Container} from "@mui/material";

interface SimulationResultViewerProps {

    // TODO - make enum state to include error too
    isLoading: boolean;
    error: string | null
    result: SimulationResult | null;
}


const SimulationResultViewer: React.FC<SimulationResultViewerProps> = ({isLoading,error, result}) => {

    const [showAnalysis, setShowAnalysis] = useState<boolean>(false);
    const toggleAnalysis = () => setShowAnalysis(prev => !prev);

    return (
        <>
            <Container maxWidth={"lg"}>
                <SimulationSummary
                    result={result}
                    scenario={result?.task_data}
                    baseline={result?.site_data?.baseline}
                    isLoading={isLoading}
                    error={error}/>
            </Container>
            {(!isLoading && !error && result) &&
                <>
                    <Button onClick={toggleAnalysis} variant="outlined" disabled={result.report_data === null}>
                        {showAnalysis ? "Hide Analysis" : "Show Analysis"}
                    </Button>
                    {showAnalysis && <DataViz result={result}/>}
                </>
            }
        </>
    )
}

export default SimulationResultViewer