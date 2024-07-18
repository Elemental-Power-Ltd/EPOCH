import StatusDisplay from "../Components/Results/StatusDisplay";
import AccordionSection from "../util/Widgets/AccordionSection";
import ConfigForm from "../Components/Config/EpochConfig";
import SearchForm from "../Components/SearchSpace/SearchForm";
import {useEffect, useState} from "react";

import { getStatus } from "../endpoints";

function RunContainer() {

    const [serverStatus, setServerStatus] = useState<{ state: string }>({ state: "UNKNOWN" });

    useEffect(() => {
        const interval = setInterval(async () => {
            const response = await getStatus();
            setServerStatus(response);
        }, 3000);

        return () => {
            clearInterval(interval);
        };
    }, []);


    return (
        <div className="run-tab">
            <StatusDisplay serverStatus={serverStatus} />

            <AccordionSection title="Config Form">
                <ConfigForm />
            </AccordionSection>

            <AccordionSection title="Search Form">
                <SearchForm />
            </AccordionSection>

            <button onClick={()=>{alert("TODO")}}>RUN</button>
            <button onClick={()=>{alert("TODO")}}>SAVE CONFIGURATION</button>

        </div>
    )


}

export default RunContainer