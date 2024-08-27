import React, { useState, useEffect } from 'react';
import './App.css';
import { Tab, Tabs, Box } from '@mui/material';

import RunContainer from "./Containers/Run";
import ResultsContainer from "./Containers/Results";

import {useEpochStore} from "./State/state";
import {listSites} from "./endpoints";

function App() {
    const [selectedTab, setSelectedTab] = useState(0);

    const globalState = useEpochStore((state) => state.global);
    const setSites = useEpochStore((state) => state.setSites);


    useEffect(() => {
        if (globalState.client) {

            const fetchSites = async () => {
                const sites = await listSites(globalState.client.client_id);
                setSites(sites);
            }

            fetchSites();
        }
    }, [globalState.client.client_id])

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
