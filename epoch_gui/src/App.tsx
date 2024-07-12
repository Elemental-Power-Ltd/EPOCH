import {useEffect, useState} from 'react'
import './App.css'

import ConfigForm from "./Config/EpochConfig"
import SearchForm from "./Search/SearchForm"
import StatusDisplay from "./Results/StatusDisplay"
import {getStatus} from "./endpoints"

function App() {

    const [serverStatus, setServerStatus] = useState<Object>({state: "UNKNOWN"});

    useEffect(() => {
        const interval = setInterval(async () => {
            try {
                const response = await getStatus();
                setServerStatus(response);
            } catch (error) {
                console.error("Error updating status:", error);
                setServerStatus({state: "UNKNOWN"});
            }
        }, 3000);

        return () => {
            clearInterval(interval);
        };
    }, []);

    return (
        <>
            <h1>Epoch</h1>
            <StatusDisplay serverStatus={serverStatus}/>
            <ConfigForm/>
            <SearchForm/>
        </>
    )
}

export default App
