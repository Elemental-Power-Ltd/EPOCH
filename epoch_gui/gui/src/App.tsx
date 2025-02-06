import React, {useEffect} from 'react';
import './App.css';
import {Tab, Tabs, Box, Select, SelectChangeEvent, MenuItem} from '@mui/material';

import OptimisationContainer from "./Containers/Optimise";
import ResultsContainer from "./Containers/Results";
import DatasetGenerationContainer from "./Containers/DatasetGeneration";
import SimulationContainer from "./Containers/Simulate";
import AnalysisContainer from "./Containers/AnalysisContainer";
import NotALogin from "./Components/Login/NotALogin";
import {useEpochStore} from "./State/Store";
import {listClients, listSites} from "./endpoints";
import {BrowserRouter, Navigate, Route, Routes, useLocation, useNavigate} from "react-router-dom";

function App() {

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


    // Handle client selection change
    const handleSelectChange = (event: SelectChangeEvent<string>) => {
        const client = availableClients.find((client) => client.client_id === event.target.value);

        if (client) {
            setSelectedClient(client);
        }
    };

    return (
        <BrowserRouter>
            <div className="fixed-tabs">
                <Box display="flex" alignItems="center">
                    <NavTabs/>
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
                    <Routes>
                        <Route path="/" element={<Navigate to="/optimise" replace/>}/>
                        <Route path="/optimise" element={<OptimisationContainer/>}/>
                        <Route path="/simulate" element={<SimulationContainer/>}/>
                        <Route path="/results" element={<ResultsContainer/>}/>
                        <Route path="/analyse/:portfolio_id?/:site_id?" element={<AnalysisContainer/>}/>
                        <Route path="/generate-data" element={<DatasetGenerationContainer/>}/>

                        {/*404*/}
                        <Route path="*" element={<div>404</div>}/>
                  </Routes>
                </Box>
            }
        </BrowserRouter>
    );
}


const NavTabs = () => {
    const navigate = useNavigate();
    const location = useLocation();

    const tabsConfig = [
        {label: 'Optimise', path: '/optimise'},
        {label: 'Simulate', path: '/simulate'},
        {label: 'Results', path: '/results'},
        {label: 'Analyse', path: '/analyse'},
        {label: 'Generate Dataset', path: '/generate-data'},
    ];

    // Determine which tab is selected based on the URL
    const currentTabIndex = tabsConfig.findIndex((tab) =>
        location.pathname.startsWith(tab.path)
    );

    const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
        navigate(tabsConfig[newValue].path);
    };

    return (
        <Tabs value={currentTabIndex} onChange={handleTabChange} sx={{flexGrow: 1}}>
            {tabsConfig.map((tab) => (
                <Tab key={tab.path} label={tab.label}/>
            ))}
        </Tabs>
    );
}

export default App;
