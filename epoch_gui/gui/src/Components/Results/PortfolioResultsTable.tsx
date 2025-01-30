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
    IconButton, Typography,
} from '@mui/material';

import ArrowForwardIcon from '@mui/icons-material/ArrowForward';

import {OptimisationTaskListEntry, PortfolioOptimisationResult} from "../../State/types";
import {formatPounds, formatCarbon, formatYears, formatCarbonCost} from "../../util/displayFunctions";
import SiteResultsTable from "./SiteResultsTable";
import {useEpochStore} from "../../State/Store";

interface PortfolioResultsTableProps {
    task: OptimisationTaskListEntry;
    results: PortfolioOptimisationResult[];
}

type Order = 'asc' | 'desc';

const PortfolioResultsTable: React.FC<PortfolioResultsTableProps> = ({ task, results }) => {
    const [order, setOrder] = useState<Order>('asc');
    const [orderBy, setOrderBy] = useState<keyof PortfolioOptimisationResult>('metric_carbon_balance_scope_1');

    const currentPortfolioResult = useEpochStore((state) => state.results.currentPortfolioResult);
    const setCurrentPortfolioResult = useEpochStore((state) => state.setCurrentPortfolioResult);

    const handleRequestSort = (property: keyof PortfolioOptimisationResult) => {
        const isAsc = orderBy === property && order === 'asc';
        setOrder(isAsc ? 'desc' : 'asc');
        setOrderBy(property);
    };

    const sortedResults = results.slice().sort((a, b) => {
        const aValue = a[orderBy];
        const bValue = b[orderBy];

        // undefined cases
        if (aValue === undefined && bValue === undefined) return 0;
        if (aValue === undefined) return order === 'asc' ? 1 : -1;
        if (bValue === undefined) return order === 'asc' ? -1 : 1;

        // normal cases
        if (aValue < bValue) return order === 'asc' ? -1 : 1;
        if (aValue > bValue) return order === 'asc' ? 1 : -1;

        return 0;
    });

    return (
        <>
        <Typography variant="h5" sx={{mt: 4}}>Portfolio Results</Typography>
        <TableContainer component={Paper}>
            <Table>
                <TableHead>
                    <TableRow>
                        <TableCell>
                            <TableSortLabel
                                active={orderBy === 'metric_carbon_balance_scope_1'}
                                direction={orderBy === 'metric_carbon_balance_scope_1' ? order : 'asc'}
                                onClick={() => handleRequestSort('metric_carbon_balance_scope_1')}
                            >
                                Scope 1
                            </TableSortLabel>
                        </TableCell>
                        <TableCell>
                            <TableSortLabel
                                active={orderBy === 'metric_carbon_balance_scope_2'}
                                direction={orderBy === 'metric_carbon_balance_scope_2' ? order : 'asc'}
                                onClick={() => handleRequestSort('metric_carbon_balance_scope_2')}
                            >
                                Scope 2
                            </TableSortLabel>
                        </TableCell>
                        <TableCell>
                            <TableSortLabel
                                active={orderBy === 'metric_carbon_cost'}
                                direction={orderBy === 'metric_carbon_cost' ? order : 'asc'}
                                onClick={() => handleRequestSort('metric_carbon_cost')}
                            >
                                Carbon Cost
                            </TableSortLabel>
                        </TableCell>
                        <TableCell>
                            <TableSortLabel
                                active={orderBy === 'metric_cost_balance'}
                                direction={orderBy === 'metric_cost_balance' ? order : 'asc'}
                                onClick={() => handleRequestSort('metric_cost_balance')}
                            >
                                Cost Balance
                            </TableSortLabel>
                        </TableCell>
                        <TableCell>
                            <TableSortLabel
                                active={orderBy === 'metric_capex'}
                                direction={orderBy === 'metric_capex' ? order : 'asc'}
                                onClick={() => handleRequestSort('metric_capex')}
                            >
                                Capex
                            </TableSortLabel>
                        </TableCell>
                        <TableCell>
                            <TableSortLabel
                                active={orderBy === 'metric_payback_horizon'}
                                direction={orderBy === 'metric_payback_horizon' ? order : 'asc'}
                                onClick={() => handleRequestSort('metric_payback_horizon')}
                            >
                                Payback Horizon
                            </TableSortLabel>
                        </TableCell>
                        <TableCell>
                            <TableSortLabel
                                active={orderBy === 'metric_annualised_cost'}
                                direction={orderBy === 'metric_annualised_cost' ? order : 'asc'}
                                onClick={() => handleRequestSort('metric_annualised_cost')}
                            >
                                Annualised Cost
                            </TableSortLabel>
                        </TableCell>
                        <TableCell>Solution</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {sortedResults.map((portfolio_result) => (
                        <TableRow
                            key={portfolio_result.portfolio_id}
                            selected={currentPortfolioResult?.portfolio_id === portfolio_result.portfolio_id}
                        >
                            <TableCell>{formatCarbon(portfolio_result.metric_carbon_balance_scope_1)}</TableCell>
                            <TableCell>{formatCarbon(portfolio_result.metric_carbon_balance_scope_2)}</TableCell>
                            <TableCell>{formatCarbonCost(portfolio_result.metric_carbon_cost)}</TableCell>
                            <TableCell>{formatPounds(portfolio_result.metric_cost_balance)}</TableCell>
                            <TableCell>{formatPounds(portfolio_result.metric_capex)}</TableCell>
                            <TableCell>{formatYears(portfolio_result.metric_payback_horizon)}</TableCell>
                            <TableCell>{formatPounds(portfolio_result.metric_annualised_cost)}</TableCell>
                            <TableCell>
                                <IconButton
                                    color="primary"
                                    onClick={() => setCurrentPortfolioResult(portfolio_result)}
                                >
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

export default PortfolioResultsTable;
