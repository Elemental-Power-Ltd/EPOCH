import React, {useState} from 'react';
import {
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    TableSortLabel,
    IconButton,
} from '@mui/material';

import InfoIcon from '@mui/icons-material/Info';

import {Task, OptimisationResult} from "../../State/types";
import {formatPounds, formatCarbon, formatYears, formatCarbonCost} from "../../util/displayFunctions";
import SolutionModal from './SolutionModal'; // Import the modal component

interface OptimisationResultsTableProps {
    task: Task;
    results: OptimisationResult[];
}

type Order = 'asc' | 'desc';

const OptimisationResultsTable: React.FC<OptimisationResultsTableProps> = ({ task, results }) => {
    const [order, setOrder] = useState<Order>('asc');
    const [orderBy, setOrderBy] = useState<keyof OptimisationResult['objective_values']>('carbon_balance_scope_1');
    const [selectedSolution, setSelectedSolution] = useState<{ [key: string]: number } | null>(null);
    const [modalOpen, setModalOpen] = useState<boolean>(false);

    const handleRequestSort = (property: keyof OptimisationResult['objective_values']) => {
        const isAsc = orderBy === property && order === 'asc';
        setOrder(isAsc ? 'desc' : 'asc');
        setOrderBy(property);
    };

    const handleShowSolution = (solution: { [key: string]: number }) => {
        setSelectedSolution(solution);
        setModalOpen(true);
    };

    const handleCloseModal = () => {
        setModalOpen(false);
        setSelectedSolution(null);
    };

    const sortedResults = results.slice().sort((a, b) => {
        const aValue = a.objective_values[orderBy];
        const bValue = b.objective_values[orderBy];
        if (aValue < bValue) return order === 'asc' ? -1 : 1;
        if (aValue > bValue) return order === 'asc' ? 1 : -1;
        return 0;
    });

    return (
        <>
        <TableContainer component={Paper}>
            <Table>
                <TableHead>
                    <TableRow>
                        <TableCell>
                            <TableSortLabel
                                active={orderBy === 'carbon_balance_scope_1'}
                                direction={orderBy === 'carbon_balance_scope_1' ? order : 'asc'}
                                onClick={() => handleRequestSort('carbon_balance_scope_1')}
                            >
                                Scope 1
                            </TableSortLabel>
                        </TableCell>
                        <TableCell>
                            <TableSortLabel
                                active={orderBy === 'carbon_balance_scope_2'}
                                direction={orderBy === 'carbon_balance_scope_2' ? order : 'asc'}
                                onClick={() => handleRequestSort('carbon_balance_scope_2')}
                            >
                                Scope 2
                            </TableSortLabel>
                        </TableCell>
                        <TableCell>
                            <TableSortLabel
                                active={orderBy === 'carbon_cost'}
                                direction={orderBy === 'carbon_cost' ? order : 'asc'}
                                onClick={() => handleRequestSort('carbon_cost')}
                            >
                                Carbon Cost
                            </TableSortLabel>
                        </TableCell>
                        <TableCell>
                            <TableSortLabel
                                active={orderBy === 'cost_balance'}
                                direction={orderBy === 'cost_balance' ? order : 'asc'}
                                onClick={() => handleRequestSort('cost_balance')}
                            >
                                Cost Balance
                            </TableSortLabel>
                        </TableCell>
                        <TableCell>
                            <TableSortLabel
                                active={orderBy === 'capex'}
                                direction={orderBy === 'capex' ? order : 'asc'}
                                onClick={() => handleRequestSort('capex')}
                            >
                                Capex
                            </TableSortLabel>
                        </TableCell>
                        <TableCell>
                            <TableSortLabel
                                active={orderBy === 'payback_horizon'}
                                direction={orderBy === 'payback_horizon' ? order : 'asc'}
                                onClick={() => handleRequestSort('payback_horizon')}
                            >
                                Payback Horizon
                            </TableSortLabel>
                        </TableCell>
                        <TableCell>
                            <TableSortLabel
                                active={orderBy === 'annualised_cost'}
                                direction={orderBy === 'annualised_cost' ? order : 'asc'}
                                onClick={() => handleRequestSort('annualised_cost')}
                            >
                                Annualised Cost
                            </TableSortLabel>
                        </TableCell>
                        <TableCell>Solution</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {sortedResults.map((result) => (
                        <TableRow key={result.result_id}>
                            <TableCell>{formatCarbon(result.objective_values.carbon_balance_scope_1)}</TableCell>
                            <TableCell>{formatCarbon(result.objective_values.carbon_balance_scope_2)}</TableCell>
                            <TableCell>{formatCarbonCost(result.objective_values.carbon_cost)}</TableCell>
                            <TableCell>{formatPounds(result.objective_values.cost_balance)}</TableCell>
                            <TableCell>{formatPounds(result.objective_values.capex)}</TableCell>
                            <TableCell>{formatYears(result.objective_values.payback_horizon)}</TableCell>
                            <TableCell>{formatPounds(result.objective_values.annualised_cost)}</TableCell>
                            <TableCell>
                                <IconButton
                                        onClick={() => handleShowSolution(result.solution)}                                    color="primary"
                                >
                                    <InfoIcon/>
                                </IconButton>
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </TableContainer>

        {selectedSolution && (
                <SolutionModal
                    open={modalOpen}
                    onClose={handleCloseModal}
                    solution={selectedSolution}
                />
        )}
        </>

    );
};

export default OptimisationResultsTable;
