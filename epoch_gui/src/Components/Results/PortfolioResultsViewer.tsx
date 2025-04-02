import React, { useState } from 'react';
import {
    Box,
    Button,
    Card,
    CardContent,
    Grid,
    Table,
    TableBody,
    TableCell,
    TableRow,
    Typography,
} from '@mui/material';

import AccessTimeIcon from '@mui/icons-material/AccessTime';
import ForestIcon from '@mui/icons-material/Forest';
import SavingsIcon from '@mui/icons-material/Savings';

import PortfolioResultsTable from './PortfolioResultsTable';
import { PortfolioOptimisationResult } from '../../State/types';
import { formatCarbon, formatPounds, formatYears } from '../../util/displayFunctions';

interface PortfolioResultsViewerProps {
    results: PortfolioOptimisationResult[];
    selectPortfolio: (portfolio_id: string) => void;
    deselectPortfolio: () => void;
    selectedPortfolioId?: string;
}

const PortfolioSummaryCard: React.FC<{
    icon: React.ReactNode;
    title: string;
    result: PortfolioOptimisationResult | null;
    onClick?: () => void;
    selected?: boolean;
}> = ({ icon, title, result, onClick, selected }) => {
    if (!result) {
        return (
            <Card sx={{ height: '100%' }}>
                <CardContent>
                    <Box display="flex" flexDirection="column" alignItems="center" mb={2}>
                        <Box fontSize={48}>{icon}</Box>
                        <Typography variant="h6">{title}</Typography>
                    </Box>
                    <Typography variant="body2" align="center">
                        No valid result available
                    </Typography>
                </CardContent>
            </Card>
        );
    }

    const metrics = result.metrics;

    return (
        <Card
            onClick={onClick}
            sx={{
                height: '100%',
                cursor: 'pointer',
                border: selected ? '2px solid #1976d2' : '1px solid rgba(0,0,0,0.12)',
                boxShadow: selected ? 4 : 1,
            }}
        >
            <CardContent>
                <Box display="flex" flexDirection="column" alignItems="center" mb={2}>
                    <Box fontSize={48}>{icon}</Box>
                    <Typography variant="h6">{title}</Typography>
                </Box>

                <Table size="small">
                    <TableBody>
                        <TableRow>
                            <TableCell><strong>Scope 1 Savings</strong></TableCell>
                            <TableCell align="right">{formatCarbon(metrics.carbon_balance_scope_1)}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell><strong>Scope 2 Savings</strong></TableCell>
                            <TableCell align="right">{formatCarbon(metrics.carbon_balance_scope_2)}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell><strong>Cost Balance</strong></TableCell>
                            <TableCell align="right">{formatPounds(metrics.cost_balance)}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell><strong>Capex</strong></TableCell>
                            <TableCell align="right">{formatPounds(metrics.capex)}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell><strong>Payback Horizon</strong></TableCell>
                            <TableCell align="right">{formatYears(metrics.payback_horizon)}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell><strong>Annualised Cost</strong></TableCell>
                            <TableCell align="right">{formatPounds(metrics.annualised_cost)}</TableCell>
                        </TableRow>
                    </TableBody>
                </Table>
            </CardContent>
        </Card>
    );
};

const PortfolioResultsViewer: React.FC<PortfolioResultsViewerProps> = ({
    results,
    selectPortfolio,
    deselectPortfolio,
    selectedPortfolioId,
}) => {
    const [showTable, setShowTable] = useState(false);

    if (!results || results.length === 0) {
        return (
            <Box mt={4} textAlign="center">
                <Typography variant="h6">No results available.</Typography>
            </Box>
        );
    }

    const validPaybacks = results.filter(
        r => typeof r.metrics.payback_horizon === 'number' && r.metrics.payback_horizon >= 0
    );
    const bestPayback = validPaybacks.reduce((best, current) =>
        (current.metrics.payback_horizon ?? Infinity) < (best.metrics.payback_horizon ?? Infinity)
            ? current
            : best,
        validPaybacks[0]
    ) ?? null;

    const validCarbon = results.filter(r =>
        typeof r.metrics.carbon_balance_scope_1 === 'number' ||
        typeof r.metrics.carbon_balance_scope_2 === 'number'
    );
    const bestCarbon = validCarbon.reduce((best, current) => {
        const currentTotal = (current.metrics.carbon_balance_scope_1 ?? 0) + (current.metrics.carbon_balance_scope_2 ?? 0);
        const bestTotal = (best.metrics.carbon_balance_scope_1 ?? 0) + (best.metrics.carbon_balance_scope_2 ?? 0);
        return currentTotal > bestTotal ? current : best;
    }, validCarbon[0]) ?? null;

    const validCostBalance = results.filter(
        r => typeof r.metrics.cost_balance === 'number'
    );
    const bestCostBalance = validCostBalance.reduce((best, current) =>
        (current.metrics.cost_balance ?? -Infinity) > (best.metrics.cost_balance ?? -Infinity)
            ? current
            : best,
        validCostBalance[0]
    ) ?? null;

    const handleToggleView = () => {
        setShowTable(prev => !prev);
        deselectPortfolio();
    };

    return (
        <Box mt={4}>
            <Typography variant="h5" gutterBottom>
                {showTable ? 'Full Portfolio Results' : 'Highlighted Portfolio Results'}
            </Typography>

            {showTable ? (
                <>
                    <PortfolioResultsTable
                        results={results}
                        selectPortfolio={selectPortfolio}
                        selectedPortfolioId={selectedPortfolioId}
                    />
                    <Box mt={4} textAlign="center">
                        <Button variant="outlined" onClick={handleToggleView}>
                            View Highlighted Results
                        </Button>
                    </Box>
                </>
            ) : (
                <>
                    <Grid container spacing={3}>
                        <Grid item xs={12} md={4}>
                            <PortfolioSummaryCard
                                icon={<AccessTimeIcon fontSize="inherit" />}
                                title="Best Payback Horizon"
                                result={bestPayback}
                                onClick={() => bestPayback && selectPortfolio(bestPayback.portfolio_id)}
                                selected={bestPayback?.portfolio_id === selectedPortfolioId}
                            />
                        </Grid>
                        <Grid item xs={12} md={4}>
                            <PortfolioSummaryCard
                                icon={<ForestIcon fontSize="inherit" />}
                                title="Best Carbon Savings"
                                result={bestCarbon}
                                onClick={() => bestCarbon && selectPortfolio(bestCarbon.portfolio_id)}
                                selected={bestCarbon?.portfolio_id === selectedPortfolioId}
                            />
                        </Grid>
                        <Grid item xs={12} md={4}>
                            <PortfolioSummaryCard
                                icon={<SavingsIcon fontSize="inherit" />}
                                title="Best Cost Balance"
                                result={bestCostBalance}
                                onClick={() => bestCostBalance && selectPortfolio(bestCostBalance.portfolio_id)}
                                selected={bestCostBalance?.portfolio_id === selectedPortfolioId}
                            />
                        </Grid>
                    </Grid>

                    <Box mt={4} textAlign="center">
                        <Button variant="outlined" onClick={handleToggleView}>
                            View All Results
                        </Button>
                    </Box>
                </>
            )}
        </Box>
    );
};

export default PortfolioResultsViewer;
