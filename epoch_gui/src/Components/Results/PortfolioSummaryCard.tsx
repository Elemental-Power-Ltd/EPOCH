import React from "react";
import {HighlightedResult, HighlightReason, PortfolioOptimisationResult} from "../../State/types.ts";
import {Box, Card, CardContent, Table, TableBody, TableCell, TableRow, Typography} from "@mui/material";
import {formatCarbon, formatPounds, formatYears} from "../../util/displayFunctions.ts";
import AccessTimeIcon from "@mui/icons-material/AccessTime";
import ForestIcon from "@mui/icons-material/Forest";
import SavingsIcon from "@mui/icons-material/Savings";
import StarsIcon from '@mui/icons-material/Stars';
import JsonViewer from "../../util/Widgets/JsonViewer.tsx";



const getIcon = (reason: HighlightReason): React.ReactNode => {
    switch (reason) {
        case HighlightReason.BestCarbonBalance:
            return <ForestIcon fontSize="inherit" />
        case HighlightReason.BestCostBalance:
            return <SavingsIcon fontSize="inherit" />
        case HighlightReason.BestPaybackHorizon:
            return <AccessTimeIcon fontSize="inherit" />
        case HighlightReason.BestReturnOnInvestment:
            return <AccessTimeIcon fontSize="inherit" />
        default:
            return <StarsIcon fontSize="inherit" />
    }
}


export const PortfolioSummaryCard: React.FC<{
    highlight: HighlightedResult;
    result: PortfolioOptimisationResult;
    onClick?: () => void;
    selected?: boolean;
}> = ({ highlight, result, onClick, selected }) => {

    const icon = getIcon(highlight.reason);
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
            <CardContent sx={{position: 'relative'}}>
                <Box sx={{position: 'absolute', top: '0.5em', right: '0.5em'}}>
                    <JsonViewer data={result.metrics} name={"Portfolio Result"}/>
                </Box>

                <Box display="flex" flexDirection="column" alignItems="center" mb={2}>
                    <Box fontSize={48}>{icon}</Box>
                    <Typography variant="body2">Best</Typography>
                    <Typography variant="h6">{highlight.display_name}</Typography>
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
                            <TableCell><strong>Operating Balance</strong></TableCell>
                            <TableCell align="right">{formatPounds(metrics.operating_balance)}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell><strong>NPV Balance</strong></TableCell>
                            <TableCell align="right">{formatPounds(metrics.npv_balance)}</TableCell>
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
