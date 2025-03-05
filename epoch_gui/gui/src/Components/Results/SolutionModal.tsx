import React from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    Table,
    TableBody,
    TableCell,
    TableRow,
    Typography,
} from '@mui/material';
import {useNavigate} from "react-router-dom";
import ArrowForward from "@mui/icons-material/ArrowForward";
import DownloadIcon from "@mui/icons-material/Download";

import SimulationSummary from "./SimulationSummary";
import {SiteOptimisationResult} from "../../State/types";
import {SimulationResult} from "../../Models/Endpoints";


interface SolutionModalProps {
    open: boolean;
    onClose: () => void;
    siteResult: SiteOptimisationResult;
}

const SolutionModal: React.FC<SolutionModalProps> = ({ open, onClose, siteResult }) => {
    const scenario = siteResult.scenario;

    const navigate = useNavigate();

    // FIXME - unify types returned from the services
    const SimResult = {
        objectives: {
            carbon_balance_scope_1: siteResult.metric_carbon_balance_scope_1,
            carbon_balance_scope_2: siteResult.metric_carbon_balance_scope_2,
            cost_balance: siteResult.metric_cost_balance,
            capex: siteResult.metric_capex,
            payback_horizon: siteResult.metric_payback_horizon,
            annualised_cost: siteResult.metric_annualised_cost,
            carbon_cost: siteResult.metric_carbon_cost
        },
        task_data: scenario,
        report_data: null,
        site_data: null
    };

    const handleAnalyse = async () => {
        navigate(`/analyse/${siteResult.portfolio_id}/${siteResult.site_id}`);
    }

    const handleDownload = () => {
        const jsonData = JSON.stringify(scenario, null, 4);
        const blob = new Blob([jsonData], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "TaskData.json";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    return (
        <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
            <DialogTitle>Solution Details</DialogTitle>
            <DialogContent dividers>
                <SimulationSummary result={SimResult}/>
                <Typography variant="h6" gutterBottom>
                    Components
                </Typography>
                <Table>
                    <TableBody>
                        {Object.entries(scenario).map(([key, value]) => (
                            <TableRow key={key}>
                                <TableCell>{key}</TableCell>
                                <TableCell>{JSON.stringify(value)}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </DialogContent>
            <DialogActions>
                <Button
                    variant="outlined"
                    startIcon={<DownloadIcon/>}
                    onClick={handleDownload}
                >
                    Download TaskData
                </Button>
                <Button
                    variant="outlined"
                    endIcon={<ArrowForward/>}
                    onClick={handleAnalyse}
                >
                    Analyse Results
                </Button>
            </DialogActions>
        </Dialog>
    );
};

export default SolutionModal;
