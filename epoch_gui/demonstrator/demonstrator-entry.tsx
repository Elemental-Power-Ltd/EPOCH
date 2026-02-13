import ReactDOM from "react-dom/client";
import React from "react";

import AppTheme from "../src/AppTheme";
import {Container, useMediaQuery} from "@mui/material";
import SimulationResultViewer from "../src/Components/Results/SimulationResultViewer";
import {SimulationResult} from "../src/Models/Endpoints";
import DemoForm from "./DemoForm";
import {SimulationRequest} from "./demo-endpoint";


export const Demonstrator: React.FC = () => {

    const runSimulation = async (request: SimulationRequest) => {
        setLoading(true);
        setError(null);
        setResult(null);
        setSiteExpanded(false);
        setComponentsExpanded(false);

        try {
            const response = await fetch("/api/simulate", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(request)
            })

            if (!response.ok) {
                const error = `Network Error: ${response.statusText}`;
                setLoading(false);
                setError(error);
            }

            const data: SimulationResult = await response.json()
            setLoading(false);
            setError(null);
            setResult(data);
        } catch (error) {
            const errorText = `Invalid Simulation`
            setError(errorText);
            setLoading(false);
            setResult(null);
        }
    }

    const [result, setResult] = React.useState<any | null>(null);
    const [loading, setLoading] = React.useState<boolean>(false);
    const [error, setError] = React.useState<string | null>(null);

    const [siteExpanded, setSiteExpanded] = React.useState<boolean>(true);
    const [componentsExpanded, setComponentsExpanded] = React.useState<boolean>(true);

    const systemPrefersDark = useMediaQuery('(prefers-color-scheme: dark)');

    return (
        <AppTheme isDarkMode={systemPrefersDark} >

            <Container maxWidth="md">
                <DemoForm
                    onSubmit={runSimulation}
                    siteExpanded={siteExpanded}
                    setSiteExpanded={setSiteExpanded}
                    componentsExpanded={componentsExpanded}
                    setComponentsExpanded={setComponentsExpanded}
                />
            </Container>

            {(result || error || loading) &&
                <SimulationResultViewer isLoading={loading} error={error} result={result}/>
            }
        </AppTheme>
    )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <Demonstrator/>
    </React.StrictMode>
);
