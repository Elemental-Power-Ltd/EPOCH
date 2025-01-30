import React from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, IconButton } from '@mui/material';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';

import {OptimisationTaskListEntry} from "../../State/types";
import {parseISODuration} from "../../util/displayFunctions";

interface TaskTableProps {
    tasks: OptimisationTaskListEntry[];
    setCurrentTask: (task: OptimisationTaskListEntry) => void;
    // for highlighting the row
    currentTaskId?: string;
}

const TaskTable: React.FC<TaskTableProps> = ({tasks, setCurrentTask, currentTaskId}) => {
    return (
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
                    {tasks.map((task) => (
                        <TableRow key={task.task_id} selected={task.task_id === currentTaskId}>
                            <TableCell>{task.task_name || 'Unnamed Task'}</TableCell>
                            <TableCell>{task.n_evals || "-"}</TableCell>
                            <TableCell>{parseISODuration(task.exec_time)}</TableCell>
                            <TableCell>{task.result_ids ? task.result_ids.length : 0}</TableCell>
                            <TableCell>
                                <IconButton color="primary" onClick={()=>setCurrentTask(task)}>
                                    <ArrowForwardIcon/>
                                </IconButton>
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </TableContainer>
    );
};

export default TaskTable;
