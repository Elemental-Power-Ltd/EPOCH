import {useEffect, useState} from "react";
import {useNavigate, useParams} from "react-router-dom";

import {useEpochStore} from "../State/Store";
import SimulationResultViewer from "../Components/Results/SimulationResultViewer";
import {reproduceSimulation} from "../endpoints";
import {Box, Button, Typography} from "@mui/material";


const AnalysisContainer = () => {
    const state = useEpochStore((state) => state.analysis);
    const setAnalysisResult = useEpochStore((state) => state.setAnalysisResult);

    const {portfolio_id, site_id} = useParams();

    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!portfolio_id || !site_id) {
            return;
        }

        const fetchData = async () => {
            setIsLoading(true);
            try {
                const res = await reproduceSimulation({portfolio_id: portfolio_id, site_id: site_id});
                if (res.success) {
                    setAnalysisResult(res.data!);
                } else {
                    setError(res.error!);
                }
            } catch (error) {
                setError("Network error. Failed to reproduce simulation");
            } finally {
                setIsLoading(false)
            }
        }

        fetchData();

    }, [portfolio_id, site_id]);



    const noResultRequested: boolean = !isLoading && state.siteResult === null;

    return (
        <>
            {noResultRequested
                ? <NoResultToAnalyse/>
                :<SimulationResultViewer isLoading={isLoading} error={error} result={state.siteResult}/>
            }
        </>
    )
}

const NoResultToAnalyse = () => {
    const navigate = useNavigate();

    return (
      <Box
        display="flex"
        flexDirection="column"
        justifyContent="center"
        alignItems="center"
        height="100%"
        textAlign="center"
      >
        <Typography variant="h5" gutterBottom>
          No Analysis Requested
        </Typography>
        <Typography variant="body1" paragraph>
          No site or portfolio has been selected for analysis.
          Navigate to the Results page to select a result.
        </Typography>
        <Button
          variant="contained"
          color="primary"
          onClick={() => navigate("/results")}
        >
          Go to Results
        </Button>
      </Box>
    );
}


export default AnalysisContainer;