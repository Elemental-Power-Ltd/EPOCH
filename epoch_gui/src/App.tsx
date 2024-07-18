import React, { useState } from 'react';
import './App.css';
import { Tab, Tabs, Box } from '@mui/material';

import RunContainer from "./Containers/Run";
import ResultsContainer from "./Containers/Results";

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
            </Tabs>

            <h1>Epoch</h1>

            <Box className="content">
                {selectedTab === 0 && <RunContainer />}
                {selectedTab === 1 && <ResultsContainer />}
            </Box>
        </>
    );
}

export default App;
