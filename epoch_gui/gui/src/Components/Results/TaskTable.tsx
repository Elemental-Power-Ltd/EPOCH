import React from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, IconButton } from '@mui/material';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';

import {Task} from "../../State/types";

interface TaskTableProps {
    tasks: Task[];
    setCurrentTask: (task: Task) => void;
}

const TaskTable: React.FC<TaskTableProps> = ({tasks, setCurrentTask}) => {
    return (
        <TableContainer component={Paper}>
            <Table>
                <TableHead>
                    <TableRow>
                        <TableCell>Task Name</TableCell>
                        <TableCell>Site</TableCell>
                        <TableCell>Number of Evaluations</TableCell>
                        <TableCell>Exec Time</TableCell>
                        <TableCell>Number of Results</TableCell>
                        <TableCell></TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {tasks.map((task) => (
                        <TableRow key={task.task_id}>
                            <TableCell>{task.task_name || 'Unnamed Task'}</TableCell>
                            <TableCell>{task.site_id}</TableCell>
                            <TableCell>{task.n_evals}</TableCell>
                            <TableCell>{task.exec_time}</TableCell>
                            <TableCell>{task.result_ids.length}</TableCell>
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
