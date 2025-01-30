import React, {useEffect, useState} from 'react';
import './App.css';
import {Tab, Tabs, Box, Select, SelectChangeEvent, MenuItem} from '@mui/material';

import OptimisationContainer from "./Containers/Optimise";
import ResultsContainer from "./Containers/Results";
import DatasetGenerationContainer from "./Containers/DatasetGeneration";
import SimulationContainer from "./Containers/Simulate";
import NotALogin from "./Components/Login/NotALogin";
import {useEpochStore} from "./State/Store";
import {listClients, listSites} from "./endpoints";

function App() {
    const [selectedTab, setSelectedTab] = useState(0);

    const selectedClient = useEpochStore((state) => state.global.selectedClient);
    const availableClients = useEpochStore((state) => state.global.availableClients);

    const setSelectedClient = useEpochStore((state) => state.setSelectedClient);
    const setClientSites = useEpochStore((state) => state.setClientSites);
    const setClients = useEpochStore((state) => state.setAvailableClients);

    const noClient = selectedClient === null;

    useEffect(() => {
        const fetchClients = async () => {
            const result = await listClients();
            if (result.success && result.data) {
                setClients(result.data);
            } else {
                console.error(`Failed to fetch clients: ${result.error}`);
            }
        };

        fetchClients();
    }, [setClients]);

    useEffect(() => {
        if (selectedClient) {
            const fetchSites = async () => {
                const result = await listSites(selectedClient.client_id);
                if (result.success && result.data) {
                    setClientSites(result.data);
                } else {
                    console.error(`Failed to fetch sites: ${result.error}`);
                }
            };

            fetchSites();
        }
    }, [selectedClient, setClientSites]);


    // Handle tab change
    const handleTabChange = (event: React.ChangeEvent<{}>, newValue: number) => {
        setSelectedTab(newValue);
    };

    // Handle client selection change
    const handleSelectChange = (event: SelectChangeEvent<string>) => {
        const client = availableClients.find((client) => client.client_id === event.target.value);

        if (client) {
            setSelectedClient(client);
        }
    };

    return (
        <>
            <div className="fixed-tabs">
                <Box display="flex" alignItems="center">
                    <Tabs
                        value={selectedTab}
                        onChange={handleTabChange}
                        sx={{flexGrow: 1}}
                    >
                        <Tab label="Optimise"/>
                        <Tab label="Simulate"/>
                        <Tab label="Results"/>
                        <Tab label="Generate Dataset"/>
                    </Tabs>
                    <Select
                        value={selectedClient ? selectedClient.client_id : ""}
                        onChange={handleSelectChange}
                        variant="standard"
                    >
                        {availableClients.map((client) =>
                            <MenuItem key={client.client_id} value={client.client_id}>
                                {client.name}
                            </MenuItem>
                        )}
                    </Select>
                </Box>
            </div>

            <h1>Epoch</h1>


            {noClient ? <NotALogin/> :
                <Box className="content">
                    {selectedTab === 0 && <OptimisationContainer/>}
                    {selectedTab === 1 && <SimulationContainer/>}
                    {selectedTab === 2 && <ResultsContainer/>}
                    {selectedTab === 3 && <DatasetGenerationContainer/>}
                </Box>
            }
        </>
    );
}

export default App;
