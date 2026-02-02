import React from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
} from '@mui/material';
import {useNavigate} from "react-router-dom";
import ArrowForward from "@mui/icons-material/ArrowForward";
import DownloadIcon from "@mui/icons-material/Download";

import SimulationSummary from "./SimulationSummary";
import {SiteOptimisationResult} from "../../State/types";
import {SimulationResult} from "../../Models/Endpoints";
import {TaskDataViewer} from "../TaskDataViewer/TaskDataViewer.tsx";
import {TaskData} from "../TaskDataViewer/TaskData.ts";


interface SolutionModalProps {
    open: boolean;
    onClose: () => void;
    siteResult: SiteOptimisationResult;
}

const SolutionModal: React.FC<SolutionModalProps> = ({ open, onClose, siteResult }) => {
    const scenario = siteResult.scenario;

    const navigate = useNavigate();

    const SimResult: SimulationResult = {
        metrics: siteResult.metrics,
        task_data: scenario,
        // set these to null; we don't care about them in here
        report_data: null,
        site_data: null,
        days_of_interest: null,
    };

    const handleAnalyse = async () => {
        navigate(`/analyse/${siteResult.portfolio_id}/${siteResult.site_id}`);
    }

    const handleDownload = (nameHint?: string) => {
        const jsonData = JSON.stringify(scenario, null, 4);
        const blob = new Blob([jsonData], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = nameHint ? `${nameHint}_TaskData.json` : "TaskData.json";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    return (
        <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
            <DialogTitle>Solution Details</DialogTitle>
            <DialogContent dividers>
                <SimulationSummary
                    result={SimResult}
                    scenario={null}
                    baseline={null}
                    isLoading={false}
                    error={null}
                />
                <TaskDataViewer data={scenario as TaskData}/>
            </DialogContent>
            <DialogActions>
                <Button
                    variant="outlined"
                    startIcon={<DownloadIcon/>}
                    onClick={() => handleDownload(siteResult.site_id)}
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
