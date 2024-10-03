import {useEffect, useState} from "react";

import {OptimiserStatusDisplay} from "../Components/OptimiserQueue/OptimiserQueue"
import TaskTable from "../Components/Results/TaskTable"

import {useEpochStore} from "../State/state";

import {getOptimisationResults, getStatus, listOptimisationTasks} from "../endpoints";
import ResultTable from "../Components/Results/ResultTable";


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

    const showResults = state.currentTask !== null;

    return (
        <div>
            <OptimiserStatusDisplay status={state.optimiserServiceStatus}/>
            <TaskTable tasks={state.tasks} setCurrentTask={setCurrentTask}/>
            {
                showResults &&
                <div>
                    RESULTS
                    <ResultTable task={state.currentTask!} results={state.currentTaskResults}/>
                </div>
            }
        </div>
    )
}

export default ResultsContainer;