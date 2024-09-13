import React, { useState } from 'react';
import './App.css';
import { Tab, Tabs, Box } from '@mui/material';

import RunContainer from "./Containers/Run";
import ResultsContainer from "./Containers/Results";
import DatasetGenerationContainer from "./Containers/DatasetGeneration";

function App() {
    const [selectedTab, setSelectedTab] = useState(0);

    const handleTabChange = (event: React.ChangeEvent<{}>, newValue: number) => {
        setSelectedTab(newValue);
    };

    return (
        <>
            <Tabs value={selectedTab} onChange={handleTabChange} className="fixed-tabs">
                <Tab label="Run" />
                <Tab label="Results" />
                <Tab label="Generate Dataset" />
            </Tabs>

            <h1>Epoch</h1>

            <Box className="content">
                {selectedTab === 0 && <RunContainer />}
                {selectedTab === 1 && <ResultsContainer />}
                {selectedTab === 2 && <DatasetGenerationContainer />}
            </Box>
        </>
    );
}

export default App;