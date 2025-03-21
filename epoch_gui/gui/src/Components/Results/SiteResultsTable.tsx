import React, {useState} from 'react';
import {
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    IconButton, Typography,
} from '@mui/material';

import InfoIcon from '@mui/icons-material/Info';

import {Site, SiteOptimisationResult} from "../../State/types";
import {formatPounds, formatCarbon, formatYears, formatCarbonCost} from "../../util/displayFunctions";
import SolutionModal from './SolutionModal';
import {useEpochStore} from "../../State/Store";
import {reproduceSimulation} from "../../endpoints";
import {SimulationResult} from "../../Models/Endpoints";
import SimulationResultViewer from "./SimulationResultViewer";

interface SiteResultsTableProps {
    results: SiteOptimisationResult[];
}

const SiteResultsTable: React.FC<SiteResultsTableProps> = ({ results }) => {
    const [selectedResult, setSelectedResult] = useState<SiteOptimisationResult | null>(null);
    const [modalOpen, setModalOpen] = useState<boolean>(false);

    const sites: Site[] = useEpochStore((state) => state.global.client_sites);

    const getSiteName = (site_id: string) => {
        const site = sites.find(site => site.site_id === site_id);
        return site ? site.name : site_id;
    }

    const handleShowSolution = async (siteResult: SiteOptimisationResult) => {
        // Immediately show the solution and open the modal
        setSelectedResult(siteResult);
        setModalOpen(true);
    };

    const handleCloseModal = () => {
        setModalOpen(false);
        setSelectedResult(null);
    };

    return (
        <>
        <Typography variant="h5" sx={{mt: 4}}>Site Results</Typography>
        <TableContainer component={Paper}>
            <Table>
                <TableHead>
                    <TableRow>
                        <TableCell>
                            Site
                        </TableCell>
                        <TableCell>
                            Scope 1
                        </TableCell>
                        <TableCell>
                            Scope 2
                        </TableCell>
                        <TableCell>
                            Carbon Cost
                        </TableCell>
                        <TableCell>
                            Cost Balance
                        </TableCell>
                        <TableCell>
                            Capex
                        </TableCell>
                        <TableCell>
                            Payback Horizon
                        </TableCell>
                        <TableCell>
                            Annualised Cost
                        </TableCell>
                        <TableCell>Solution</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {results.map((site_result) => (
                        <TableRow key={site_result.site_id}>
                            <TableCell>{getSiteName(site_result.site_id)}</TableCell>
                            <TableCell>{formatCarbon(site_result.metrics.carbon_balance_scope_1)}</TableCell>
                            <TableCell>{formatCarbon(site_result.metrics.carbon_balance_scope_2)}</TableCell>
                            <TableCell>{formatCarbonCost(site_result.metrics.carbon_cost)}</TableCell>
                            <TableCell>{formatPounds(site_result.metrics.cost_balance)}</TableCell>
                            <TableCell>{formatPounds(site_result.metrics.capex)}</TableCell>
                            <TableCell>{formatYears(site_result.metrics.payback_horizon)}</TableCell>
                            <TableCell>{formatPounds(site_result.metrics.annualised_cost)}</TableCell>
                            <TableCell>
                                <IconButton
                                    color="primary"
                                    onClick={async () => handleShowSolution(site_result)}
                                >
                                    <InfoIcon/>
                                </IconButton>
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </TableContainer>

        {selectedResult && (
                <SolutionModal
                    open={modalOpen}
                    onClose={handleCloseModal}
                    siteResult={selectedResult}
                />
        )}
        </>

    );
};

export default SiteResultsTable;
