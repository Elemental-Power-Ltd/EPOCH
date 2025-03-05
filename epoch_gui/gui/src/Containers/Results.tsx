import React, {useEffect, useState} from "react";

import {Container} from "@mui/material";

import {OptimiserStatusDisplay} from "../Components/OptimiserQueue/OptimiserQueue"
import TaskTable from "../Components/Results/TaskTable"

import {useEpochStore} from "../State/Store";

import {getOptimisationResults, getStatus, listOptimisationTasks} from "../endpoints";
import PortfolioResultsTable from "../Components/Results/PortfolioResultsTable";
import SiteResultsTable from "../Components/Results/SiteResultsTable";


function ResultsContainer() {

    const {
        results: state,
        global: globalState,

        setOptimiserServiceStatus,
        setTasks,
        setCurrentTask,
        setCurrentTaskResults,
    } = useEpochStore((state) => ({
        results: state.results,
        global: state.global,

        setOptimiserServiceStatus: state.setOptimiserServiceStatus,
        setTasks: state.setTasks,
        setCurrentTask: state.setCurrentTask,
        setCurrentTaskResults: state.setCurrentTaskResults,
    }));


    useEffect(() => {
        const interval = setInterval(async () => {
            const response = await getStatus();
            setOptimiserServiceStatus(response);
        }, 2000);

        return () => {
            clearInterval(interval);
        };
    }, []);

    useEffect(() => {
        const clientId = globalState.selectedClient?.client_id;

        if (clientId) {

            const fetchTasks = async () => {
                const tasks = await listOptimisationTasks(clientId);
                setTasks(tasks);
            }

            fetchTasks();
        }

    }, [globalState.selectedClient?.client_id])

    useEffect(() => {
        if (state.currentTask !== null) {
            const fetchResults = async () => {
                const results = await getOptimisationResults(state.currentTask!.task_id);
                setCurrentTaskResults(results);
            }

            fetchResults();
        }
    }, [state.currentTask])

    return (
        <Container maxWidth={"lg"}>
            <OptimiserStatusDisplay status={state.optimiserServiceStatus}/>
            <TaskTable tasks={state.tasks} setCurrentTask={setCurrentTask} currentTaskId={state.currentTask?.task_id}/>

            {state.currentTask !== null &&
                <PortfolioResultsTable task={state.currentTask} results={state.currentTaskResults}/>
            }

            {state.currentPortfolioResult !== null &&
                <SiteResultsTable results={state.currentPortfolioResult.site_results}/>
            }

        </Container>
    )
}

export default ResultsContainer;