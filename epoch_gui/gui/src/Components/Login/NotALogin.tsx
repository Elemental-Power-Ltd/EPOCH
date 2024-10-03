import React from 'react';
import {Select, MenuItem, FormControl, InputLabel} from '@mui/material';

import {useEpochStore} from "../../State/state";

const NotALogin = () => {
    const availableClients = useEpochStore((state) => state.global.availableClients);
    const setSelectedClient = useEpochStore((state) => state.setSelectedClient);
    const selectedClient = useEpochStore((state) => state.global.selectedClient);

    // Handle dropdown change event
    const handleChange = (event) => {
        const client = availableClients.find((client) => client.client_id === event.target.value);
        if (client) {
            setSelectedClient(client);
        }
    };

    return (
        <FormControl fullWidth>
            <InputLabel id="client-selector-label">Select Client</InputLabel>
            <Select
                labelId="client-selector-label"
                id="client-selector"
                value={selectedClient ? selectedClient.client_id : ''}
                onChange={handleChange}
                label="Select Client"
            >
                {availableClients.map((client) => (
                    <MenuItem key={client.client_id} value={client.client_id}>
                        {client.name}
                    </MenuItem>
                ))}
            </Select>
        </FormControl>
    );
};

export default NotALogin;
