import React, {useEffect, useState} from "react";

import {Container} from "@mui/material";
import {useNavigate, useParams} from "react-router-dom";


import {OptimiserStatusDisplay} from "../Components/OptimiserQueue/OptimiserQueue"
import TaskTable from "../Components/Results/TaskTable"

import {useEpochStore} from "../State/Store";

import {getOptimisationResults, getStatus, listOptimisationTasks} from "../endpoints";
import PortfolioResultsTable from "../Components/Results/PortfolioResultsTable";
import SiteResultsTable from "../Components/Results/SiteResultsTable";
import {PortfolioOptimisationResult} from "../State/types.ts";


function ResultsContainer() {

    const client_id = useEpochStore((state) => state.global.selectedClient?.client_id);

    const {
        results: state,
        setOptimiserServiceStatus,
        setTasks,
    } = useEpochStore((state) => ({
        results: state.results,
        setOptimiserServiceStatus: state.setOptimiserServiceStatus,
        setTasks: state.setTasks,
    }));


    const {task_id, portfolio_id} = useParams();
    const navigate = useNavigate();

    const [resultsForTask, setResultsForTask] = useState<PortfolioOptimisationResult[] | null>(null);
    const [isLoadingResults, setIsLoadingResults] = useState(false);
    const [error, setError] = useState<string | null>(null);


    // Fetch the Optimiser Service Status periodically
    useEffect(() => {
        const interval = setInterval(async () => {
            const response = await getStatus();
            setOptimiserServiceStatus(response);
        }, 2000);

        return () => {
            clearInterval(interval);
        };
    }, []);


    // Fetch all optimisation tasks
    useEffect(() => {
        if (!client_id) {
            return;
        }

        const fetchTasks = async () => {
            const tasks = await listOptimisationTasks(client_id);
            setTasks(tasks);
        }

        fetchTasks();

    }, [client_id])


    // Fetch the PortfolioResults for a given task_id
    useEffect(() => {
        if (!client_id || !task_id) {
            return;
        }

        const fetchPortfolioResults = async () => {
            try {
                setIsLoadingResults(true);
                const results = await getOptimisationResults(task_id);
                setResultsForTask(results);
            }  catch (error) {
                setError("Failed to fetch results.");
            } finally {
                setIsLoadingResults(false);
            }
        }

        fetchPortfolioResults();

    }, [client_id, task_id])

    const resultsForPortfolio = resultsForTask?.find((result) =>
        result.portfolio_id === portfolio_id
    )

    return (
        <Container maxWidth={"lg"}>
            <OptimiserStatusDisplay status={state.optimiserServiceStatus}/>

            <TaskTable
                tasks={state.tasks}
                selectTask={(task_id: string) => navigate(`/results/${task_id}`)}
                deselectTask={()=> navigate(`/results/`)}
                selectedTaskId={task_id}
            />

            {(task_id && resultsForTask) &&
                <PortfolioResultsTable
                    results={resultsForTask}
                    selectPortfolio={(portfolio_id: string) => navigate(`/results/${task_id}/${portfolio_id}`)}
                    selectedPortfolioId={portfolio_id}
                />
            }

            {(task_id && resultsForPortfolio) &&
                <SiteResultsTable
                    results={resultsForPortfolio.site_results}

                />
            }

        </Container>
    )
}

export default ResultsContainer;