import {useEffect, useRef, useState} from "react";

import {Alert, CircularProgress, Container} from "@mui/material";
import {useNavigate, useParams} from "react-router-dom";


import {OptimiserStatusDisplay} from "../Components/OptimiserQueue/OptimiserQueue"
import TaskTable, {ColumnKey, OPTIONAL_COLUMN_KEYS, HIDE_BY_DEFAULT} from "../Components/Results/TaskTable"

import {useEpochStore} from "../State/Store";

import {getOptimisationResults, getStatus, listOptimisationTasks} from "../endpoints";
import PortfolioResultsViewer from "../Components/Results/PortfolioResultsViewer.tsx";
import SiteResultsTable from "../Components/Results/SiteResultsTable";
import {OptimisationResultsResponse} from "../Models/Endpoints.ts";




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

    // pagination state for the tasks list
    const [page, setPage] = useState(0);
    const [rowsPerPage, setRowsPerPage] = useState(20);
    const [total, setTotal] = useState(0);

    // loading and error states for tasks
    const [isLoadingTasks, setIsLoadingTasks] = useState(false);
    const [tasksError, setTasksError] = useState<string | null>(null);

    // counter to avoid race conditions
    const tasksReqId = useRef(0);

    const {task_id, portfolio_id} = useParams();
    const navigate = useNavigate();

    // state / loading / error for the PortfolioResults within a task
    const [resultsForTask, setResultsForTask] = useState<OptimisationResultsResponse | null>(null);
    const [isLoadingPortfolio, setIsLoadingPortfolio] = useState(false);
    const [portfolioError, setPortfolioError] = useState<string | null>(null);


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

        const reqId = ++tasksReqId.current;
        setIsLoadingTasks(true);
        setTasksError(null);

        const fetchTasks = async () => {
            const taskResponse = await listOptimisationTasks({
                client_id: client_id,
                limit: rowsPerPage,
                offset: page * rowsPerPage
            });

            if (reqId !== tasksReqId.current) {
                // this result is stale
                return;
            }

            if(taskResponse.success) {
                setTasks(taskResponse.data!.tasks);
                setTotal(taskResponse.data!.total_results);
            } else {
                setTasksError(taskResponse.error!);
            }
            setIsLoadingTasks(false);
        }

        fetchTasks();

    }, [client_id, page, rowsPerPage, setTasks]);


    // Fetch the PortfolioResults for a given task_id
    useEffect(() => {
        if (!client_id || !task_id) {
            return;
        }

        const fetchPortfolioResults = async () => {
            setIsLoadingPortfolio(true);
            setPortfolioError(null);
            const result = await getOptimisationResults(task_id);

            if (result.success && result.data) {
                setResultsForTask(result.data);
                setPortfolioError(null);
            } else {
                setPortfolioError(result.error!)
            }
            setIsLoadingPortfolio(false);
        }

        fetchPortfolioResults();

    }, [client_id, task_id])

    const resultsForPortfolio = resultsForTask?.portfolio_results.find((result) =>
        result.portfolio_id === portfolio_id
    )

    const handleRowsPerPage = (r: number) => {
        setRowsPerPage(r);
        setPage(0);
    };


    const [visibleCols, setvisibleCols] = useState<Set<ColumnKey>>(
        () => new Set<ColumnKey>(OPTIONAL_COLUMN_KEYS.filter(k => !HIDE_BY_DEFAULT.includes(k)))
    );

    return (
        <Container maxWidth={"lg"}>
            <OptimiserStatusDisplay status={state.optimiserServiceStatus}/>

            {isLoadingTasks && <CircularProgress sx={{ mb: 2 }} />}
            {tasksError && <Alert severity="error" sx={{ mb: 2 }}>{tasksError}</Alert>}
            {!isLoadingTasks && !tasksError &&
                <TaskTable
                tasks={state.tasks}
                total={total}
                page={page}
                rowsPerPage={rowsPerPage}
                onPageChange={setPage}
                onRowsPerPageChange={handleRowsPerPage}
                selectTask={(task_id: string) => navigate(`/results/${task_id}`)}
                deselectTask={()=> navigate(`/results/`)}
                selectedTaskId={task_id}
                visibleCols={visibleCols}
                setVisibleCols={setvisibleCols}
            />}

            {task_id &&
                <PortfolioResultsViewer
                    isLoading={isLoadingPortfolio}
                    error={portfolioError}
                    optimisationResult={resultsForTask}
                    selectPortfolio={(portfolio_id: string) => navigate(`/results/${task_id}/${portfolio_id}`)}
                    deselectPortfolio={()=> navigate(`/results/${task_id}`)}
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