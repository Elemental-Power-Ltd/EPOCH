import React, {useEffect} from 'react';
import {Tab, Tabs, Box, Select, SelectChangeEvent, MenuItem, useMediaQuery} from '@mui/material';

import OptimisationContainer from "./Containers/Optimise";
import ResultsContainer from "./Containers/Results";
import DatasetGenerationContainer from "./Containers/DatasetGeneration";
import SimulationContainer from "./Containers/Simulate";
import AnalysisContainer from "./Containers/AnalysisContainer";
import SitesContainer from "./Containers/Sites";
import NotALogin from "./Components/Login/NotALogin";
import {useEpochStore} from "./State/Store";
import {listClients, listSites} from "./endpoints";
import {BrowserRouter, Navigate, Route, Routes, useLocation, useNavigate} from "react-router-dom";

import AppTheme from "./AppTheme";
import DeveloperSettings from "./Components/Settings/DeveloperSettings.tsx";

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

    const systemPrefersDark = useMediaQuery('(prefers-color-scheme: dark)');

    const [isDarkMode, setIsDarkMode] = React.useState(systemPrefersDark);
    const [isInformedEmbed, setIsInformedEmbed] = React.useState(false);
    const [devOpen, setDevOpen] = React.useState(false);

    const handleEpochClick: React.MouseEventHandler<HTMLHeadingElement> = (e) => {
        if (e.detail === 3) setDevOpen(true); // triple-click
    };

    return (
        <BrowserRouter>
            <AppTheme isDarkMode={isDarkMode} isInformedEmbed={isInformedEmbed}>
                <div className="fixed-tabs">
                    <Box
                        display="flex"
                        alignItems="center"
                        sx={{ bgcolor: 'background.paper', borderBottom: 1, borderColor: 'divider' }}
                    >
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

                <h1 onClick={handleEpochClick}>Epoch</h1>

                {noClient ? <NotALogin/> :
                    <Box className="content">
                        <Routes>
                            <Route path="/" element={<Navigate to="/optimise" replace/>}/>
                            <Route path="/optimise" element={<OptimisationContainer/>}/>
                            <Route path="/simulate" element={<SimulationContainer/>}/>
                            <Route path="/results/:task_id?/:portfolio_id?" element={<ResultsContainer/>}/>
                            <Route path="/analyse/:portfolio_id?/:site_id?" element={<AnalysisContainer/>}/>
                            <Route path="/sites" element={<SitesContainer/>}/>
                            <Route path="/generate-data" element={<DatasetGenerationContainer/>}/>

                            {/*404*/}
                            <Route path="*" element={<div>404</div>}/>
                        </Routes>
                    </Box>
                }


                <DeveloperSettings
                  open={devOpen}
                  onClose={() => setDevOpen(false)}
                  isDarkMode={isDarkMode}
                  setIsDarkMode={setIsDarkMode}
                  isInformedEmbed={isInformedEmbed}
                  setIsInformedEmbed={setIsInformedEmbed}
                />
            </AppTheme>
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
        {label: 'Sites', path: '/sites'},
        {label: 'Generate Dataset', path: '/generate-data'},
    ];

    // Determine which tab is selected based on the URL
    const currentTabIndex = tabsConfig.findIndex((tab) =>
        location.pathname.startsWith(tab.path)
    );

    const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
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
