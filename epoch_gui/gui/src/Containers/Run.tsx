import "./Run.css"

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
            optimiser: {
                name: state.selectedOptimiser,
                hyperparameters: {}  // TODO
            },
            search_parameters: state.searchParameters,
        }

        // ignore the response for now
        submitOptimisationJob(payload);
    }


    return (
        <div className="run-tab">
            <AccordionSection title="Config Form">
                <ConfigForm/>
            </AccordionSection>

            <AccordionSection title="Search Form">
                <SearchForm />
            </AccordionSection>

            <div className="run-footer">
                <button onClick={onRun}>RUN</button>
                <button onClick={()=>{alert("TODO")}}>SAVE CONFIGURATION</button>
            </div>

        </div>
    )
}

export default RunContainer