import React, {useState} from 'react';


import SimulationSummary, {ErroredSimulationSummary, LoadingSimulatingSummary} from "./SimulationSummary";
import DataViz from "../DataViz/DataViz";
import {SimulationResult} from "../../Models/Endpoints";
import {Button} from "@mui/material";

interface SimulationResultViewerProps {

    // TODO - make enum state to include error too
    isLoading: boolean;
    error: string | null
    result: SimulationResult | null;
}


const SimulationResultViewer: React.FC<SimulationResultViewerProps> = ({isLoading,error, result}) => {

    const [showAnalysis, setShowAnalysis] = useState<boolean>(false);
    const toggleAnalysis = () => setShowAnalysis(prev => !prev);

    if (isLoading) {
        return <LoadingSimulatingSummary/>;
    } else if (error) {
        return <ErroredSimulationSummary error={error}/>
    } else if (result === null) {
        return <ErroredSimulationSummary error={"Simulation failed - unknown error"}/>
    }

    return (
        <>
            <SimulationSummary result={result}/>
            <Button onClick={toggleAnalysis} variant="outlined">
                {showAnalysis ? "Hide Analysis" : "Show Analysis"}
            </Button>
            {showAnalysis && <DataViz result={result}/>}
        </>
    )
}

export default SimulationResultViewer