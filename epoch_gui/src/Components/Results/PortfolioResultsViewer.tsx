import React, { useState } from 'react';
import {
    Box,
    Button,
    CircularProgress,
    Grid,
    Typography,
} from '@mui/material';

import PortfolioResultsTable from './PortfolioResultsTable';
import {HighlightedResult, HighlightReason, PortfolioOptimisationResult} from '../../State/types';
import {PortfolioSummaryCard} from "./PortfolioSummaryCard.tsx";

interface PortfolioResultsViewerProps {
    isLoading: boolean;
    error: string | null;
    results: PortfolioOptimisationResult[];
    highlighted: HighlightedResult[];
    selectPortfolio: (portfolio_id: string) => void;
    deselectPortfolio: () => void;
    selectedPortfolioId?: string;
}


const PortfolioResultsViewer: React.FC<PortfolioResultsViewerProps> = ({
    isLoading,
    error,
    results,
    highlighted,
    selectPortfolio,
    deselectPortfolio,
    selectedPortfolioId,
}) => {

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
            <Typography variant="h5" gutterBottom>
                {actuallyShowTable ? 'Full Portfolio Results' : 'Highlighted Portfolio Results'}
            </Typography>

            <>
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
                { /* Only show the toggle if we have some highlighted results*/
                    canShowHighlights &&
                    <Box mt={4} textAlign="center">
                        <Button variant="outlined" onClick={handleToggleView}>
                            {actuallyShowTable ? "View Highlighted Results" : "View All Results"}
                        </Button>
                    </Box>
                }
            </>
        </Box>
    );
};

export default PortfolioResultsViewer;
