import StatusDisplay from "../Components/Results/StatusDisplay";
import AccordionSection from "../util/Widgets/AccordionSection";
import ConfigForm from "../Components/Config/OptimiserConfig";
import SearchForm from "../Components/SearchParameters/SearchForm";
import {useEffect, useState} from "react";

import {getStatus, submitOptimisationJob} from "../endpoints";

import {useEpochStore} from "../State/state";

function RunContainer() {

    const state = useEpochStore((state) => state.run);

    const [serverStatus, setServerStatus] = useState<{ state: string }>({ state: "UNKNOWN" });

    const onRun = () => {

        const payload = {
            site: state.selectedSite,
            optimiser: state.selectedOptimiser,
            optimiserConfig: state.optimisers[state.selectedOptimiser],
            searchParameters: state.searchSpace,
        }

        // ignore the response for now
        submitOptimisationJob(payload);
    }




    // useEffect(() => {
    //     const interval = setInterval(async () => {
    //         const response = await getStatus();
    //         setServerStatus(response);
    //     }, 3000);
    //
    //     return () => {
    //         clearInterval(interval);
    //     };
    // }, []);


    return (
        <div className="run-tab">
            <StatusDisplay serverStatus={serverStatus} />

            <AccordionSection title="Config Form">
                <ConfigForm/>
            </AccordionSection>

            <AccordionSection title="Search Form">
                <SearchForm />
            </AccordionSection>

            <button onClick={onRun}>RUN</button>
            <button onClick={()=>{alert("TODO")}}>SAVE CONFIGURATION</button>

        </div>
    )


}

export default RunContainer