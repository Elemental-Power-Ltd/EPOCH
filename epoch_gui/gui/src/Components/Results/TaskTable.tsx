import React from 'react';
import { Box, Button, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, IconButton } from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';

import {OptimisationTaskListEntry} from "../../State/types";
import {parseISODuration} from "../../util/displayFunctions";

interface TaskTableProps {
    tasks: OptimisationTaskListEntry[];
    selectTask: (task_id: string) => void;
    deselectTask: () => void;
    selectedTaskId?: string;
}

const TaskTable: React.FC<TaskTableProps> = ({tasks, selectTask, deselectTask, selectedTaskId}) => {

    // if a task has been selected, we only show the user that task
    // (as they will be more interested in viewing the portfolio results table)
    // if they have not selected a task, show all task results
    const tasksToShow = tasks.filter(
        (task) => (!selectedTaskId || task.task_id === selectedTaskId)
    );


    return (
        <>

            {/* Conditionally render the Back button above the table */}
            {selectedTaskId && (
                <Box marginBottom={2} display="flex" justifyContent="flex-start">
                    <Button
                        startIcon={<ArrowBackIcon/>}
                        onClick={() => deselectTask()}
                    >
                        Show all Tasks
                    </Button>
                </Box>
            )}

            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>Task Name</TableCell>
                            <TableCell>Number of Evaluations</TableCell>
                            <TableCell>Exec Time</TableCell>
                            <TableCell>Number of Results</TableCell>
                            <TableCell></TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {tasksToShow.map((task) => (
                            <TableRow key={task.task_id}>
                                <TableCell>{task.task_name || 'Unnamed Task'}</TableCell>
                                <TableCell>{task.n_evals || "-"}</TableCell>
                                <TableCell>{parseISODuration(task.exec_time)}</TableCell>
                                <TableCell>{task.n_saved ? task.n_saved : 0}</TableCell>
                                <TableCell>
                                    <IconButton color="primary" onClick={()=>selectTask(task.task_id)}>
                                        <ArrowForwardIcon/>
                                    </IconButton>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        </>
    );
};

export default TaskTable;
