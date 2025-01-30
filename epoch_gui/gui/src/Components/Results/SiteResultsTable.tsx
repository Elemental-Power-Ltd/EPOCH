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
import {useEpochStore} from "../../State/Store"; // Import the modal component

interface SiteResultsTableProps {
    results: SiteOptimisationResult[];
}

const SiteResultsTable: React.FC<SiteResultsTableProps> = ({ results }) => {
    const [selectedSolution, setSelectedSolution] = useState<{ [key: string]: number } | null>(null);
    const [modalOpen, setModalOpen] = useState<boolean>(false);

    const sites: Site[] = useEpochStore((state) => state.global.client_sites);

    const getSiteName = (site_id: string) => {
        const site = sites.find(site => site.site_id === site_id);
        return site ? site.name : site_id;
    }

    const handleShowSolution = (solution: any) => {
        setSelectedSolution(solution);
        setModalOpen(true);
    };

    const handleCloseModal = () => {
        setModalOpen(false);
        setSelectedSolution(null);
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
                            <TableCell>{formatCarbon(site_result.metric_carbon_balance_scope_1)}</TableCell>
                            <TableCell>{formatCarbon(site_result.metric_carbon_balance_scope_2)}</TableCell>
                            <TableCell>{formatCarbonCost(site_result.metric_carbon_cost)}</TableCell>
                            <TableCell>{formatPounds(site_result.metric_cost_balance)}</TableCell>
                            <TableCell>{formatPounds(site_result.metric_capex)}</TableCell>
                            <TableCell>{formatYears(site_result.metric_payback_horizon)}</TableCell>
                            <TableCell>{formatPounds(site_result.metric_annualised_cost)}</TableCell>
                            <TableCell>
                                <IconButton
                                    color="primary"
                                    onClick={() => handleShowSolution(site_result.scenario)}
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

export default SiteResultsTable;
