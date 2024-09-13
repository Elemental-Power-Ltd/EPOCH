import "./Run.css"

import AccordionSection from "../util/Widgets/AccordionSection";
import HyperParamForm from "../Components/HyperParams/OptimiserConfig";
import SearchForm from "../Components/SearchParameters/SearchForm";

import {useEffect, useState} from "react";

import {getStatus, submitOptimisationJob} from "../endpoints";

import {useEpochStore} from "../State/state";
import TaskConfigForm from "../Components/TaskConfig/TaskConfigForm";

function RunContainer() {

    const state = useEpochStore((state) => state.run);

    const onRun = () => {

        const payload = {
            task_name: state.taskConfig.task_name,
            optimiser: {
                // name: state.taskConfig.optimiser,
                name: "NSGA2",
                hyperparameters: {}  // TODO
            },

            search_parameters: state.searchParameters,
            objectives: Object.keys(state.taskConfig.objectives),
            site_data: {
                loc: "remote",
                site_id: state.taskConfig.site_id,
                start_ts: state.taskConfig.start_date,
                duration: state.taskConfig.duration
            }
        }

        // ignore the response for now
        submitOptimisationJob(payload);
    }


    return (
        <div className="run-tab">
            <AccordionSection title="Config Form">
                <TaskConfigForm/>
                <HyperParamForm/>
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