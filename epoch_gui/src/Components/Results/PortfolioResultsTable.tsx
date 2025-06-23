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

import {PortfolioMetrics, PortfolioOptimisationResult} from "../../State/types";
import {formatPounds, formatCarbon, formatYears, formatCarbonCost} from "../../util/displayFunctions";

interface PortfolioResultsTableProps {
    results: PortfolioOptimisationResult[];
    selectPortfolio: (portfolio_id: string) => void;
    selectedPortfolioId?: string;
}

type Order = 'asc' | 'desc';

const PortfolioResultsTable: React.FC<PortfolioResultsTableProps> = ({ results, selectPortfolio, selectedPortfolioId }) => {
    const [order, setOrder] = useState<Order>('asc');
    const [orderBy, setOrderBy] = useState<keyof PortfolioMetrics>('carbon_balance_scope_1');

    const handleRequestSort = (property: keyof PortfolioMetrics) => {
        const isAsc = orderBy === property && order === 'asc';
        setOrder(isAsc ? 'desc' : 'asc');
        setOrderBy(property);
    };

    const sortedResults = results.slice().sort((a, b) => {
        const aValue = a.metrics[orderBy];
        const bValue = b.metrics[orderBy];

        // undefined cases
        if (aValue === undefined && bValue === undefined) return 0;
        if (aValue === undefined) return order === 'asc' ? 1 : -1;
        if (bValue === undefined) return order === 'asc' ? -1 : 1;

        // special case:
        // if we are sorting by payback_horizon, negative values are worse
        if (orderBy == 'payback_horizon') {
            if (aValue < 0 && bValue >= 0) return order == 'asc' ? 1 : -1;
            if (aValue >= 0 && bValue < 0) return order == 'asc' ? -1 : 1;
            // otherwise, allow the usual sorting cases to apply
        }

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
                                active={orderBy === 'npv_balance'}
                                direction={orderBy === 'npv_balance' ? order : 'asc'}
                                onClick={() => handleRequestSort('npv_balance')}
                            >
                                NPV Balance
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
                    {sortedResults.map((portfolio_result) => (
                        <TableRow
                            key={portfolio_result.portfolio_id}
                            selected={selectedPortfolioId === portfolio_result.portfolio_id}
                        >
                            <TableCell>{formatCarbon(portfolio_result.metrics.carbon_balance_scope_1)}</TableCell>
                            <TableCell>{formatCarbon(portfolio_result.metrics.carbon_balance_scope_2)}</TableCell>
                            <TableCell>{formatCarbonCost(portfolio_result.metrics.carbon_cost)}</TableCell>
                            <TableCell>{formatPounds(portfolio_result.metrics.cost_balance)}</TableCell>
                            <TableCell>{formatPounds(portfolio_result.metrics.npv_balance)}</TableCell>
                            <TableCell>{formatPounds(portfolio_result.metrics.capex)}</TableCell>
                            <TableCell>{formatYears(portfolio_result.metrics.payback_horizon)}</TableCell>
                            <TableCell>{formatPounds(portfolio_result.metrics.annualised_cost)}</TableCell>
                            <TableCell>
                                <IconButton
                                    color="primary"
                                    onClick={() => selectPortfolio(portfolio_result.portfolio_id)}
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
