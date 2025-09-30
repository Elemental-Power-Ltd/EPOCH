import React, { useState } from 'react';
import {
    Box,
    Button,
    CircularProgress,
    Grid,
    Stack,
    Typography,
} from '@mui/material';

import PortfolioResultsTable from './PortfolioResultsTable';
import {HighlightedResult, HighlightReason, PortfolioOptimisationResult, Site} from '../../State/types';
import {PortfolioSummaryCard} from "./PortfolioSummaryCard.tsx";
import {OptimisationResultsResponse} from "../../Models/Endpoints.ts";
import {useEpochStore} from "../../State/Store.ts";
import {ExtraTaskInfo} from "./ExtraTaskInfo/ExtraTaskInfo.tsx";

interface PortfolioResultsViewerProps {
    isLoading: boolean;
    error: string | null;
    optimisationResult: OptimisationResultsResponse | null;
    selectPortfolio: (portfolio_id: string) => void;
    deselectPortfolio: () => void;
    selectedPortfolioId?: string;
}


const PortfolioResultsViewer: React.FC<PortfolioResultsViewerProps> = ({
    isLoading,
    error,
    optimisationResult,
    selectPortfolio,
    deselectPortfolio,
    selectedPortfolioId,
}) => {

    const results = optimisationResult?.portfolio_results || [];
    const highlighted = optimisationResult?.highlighted_results || [];
    const hints = optimisationResult?.hints || {};
    const searchSpace = optimisationResult?.search_spaces

    const sites: Site[] = useEpochStore((state) => state.global.client_sites);

    const canShowHighlights: boolean = highlighted.length > 0;

    const [showTable, setShowTable] = useState<boolean>(false);
    const actuallyShowTable = !canShowHighlights || showTable;

    if (isLoading) {
        return (
            <Box mt={4} textAlign="center">
                <CircularProgress />
                <Typography mt={2}>Loading results...</Typography>
            </Box>
        );
    }

    if (error) {
        return (
            <Box mt={4} textAlign="center">
                <Typography variant="h6" color="error">
                    Error: {error}
                </Typography>
            </Box>
        );
    }

    if (!results || results.length === 0) {
        return (
            <Box mt={4} textAlign="center">
                <Typography variant="h6">No results available.</Typography>
            </Box>
        );
    }

    // pick out the full highlighted results
    const highlightedPortfolios: Partial<Record<HighlightReason, PortfolioOptimisationResult>> = {};
    highlighted.forEach(highlight => {

        const result = results.find(
            (result) => result.portfolio_id == highlight.portfolio_id);

        if (result) {
            highlightedPortfolios[highlight.reason] = result;
        }
    })

    const handleToggleView = () => {
        setShowTable(prev => !prev);
        deselectPortfolio();
    };

    const renderSummaryCard = (highlight: HighlightedResult) => {

        const result = highlightedPortfolios[highlight.reason]!;

        return (
            <PortfolioSummaryCard
                highlight={highlight}
                result={result}
                onClick={() => selectPortfolio(result.portfolio_id)}
                selected={result.portfolio_id === selectedPortfolioId}
            />
        )
    }

    return (
        <Box mt={4}>
            <Box mt={4} textAlign="center" mb={"1em"}>
                <Stack direction={"row"} justifyContent={"center"} spacing={2}>
                    { /* Only show the toggle if we have some highlighted results*/
                        canShowHighlights &&
                        <Button variant="outlined" onClick={handleToggleView}>
                            {actuallyShowTable ? "View Highlighted Results" : "View All Results"}
                        </Button>
                    }
                    <ExtraTaskInfo
                        searchSpace={searchSpace}
                        hints={hints}
                        sites={sites}
                    />
                </Stack>
            </Box>

            <Typography variant="h5" gutterBottom>
                {actuallyShowTable ? 'Full Portfolio Results' : 'Highlighted Portfolio Results'}
            </Typography>

            <Box mb={4}>
                {actuallyShowTable ? (
                    <PortfolioResultsTable
                        results={results}
                        selectPortfolio={selectPortfolio}
                        selectedPortfolioId={selectedPortfolioId}
                    />
                ) : (
                    <Grid container spacing={3}>
                        {highlighted.map((highlight) => (
                            <Grid item xs={12} md={4} key={highlight.reason}>
                                {renderSummaryCard(highlight)}
                            </Grid>
                        ))}
                    </Grid>
                )}
            </Box>
        </Box>
    );
};

export default PortfolioResultsViewer;
