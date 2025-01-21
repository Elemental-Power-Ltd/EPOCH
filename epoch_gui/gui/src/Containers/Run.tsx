import AccordionSection from "../util/Widgets/AccordionSection";
import HyperParamForm from "../Components/HyperParams/OptimiserConfig";
import SearchForm from "../Components/SearchParameters/SearchForm";

import {Button, Container} from '@mui/material';

import {getStatus, submitOptimisationJob} from "../endpoints";

import {useEpochStore} from "../State/state";
import TaskConfigForm from "../Components/TaskConfig/TaskConfigForm";

function RunContainer() {

    const state = useEpochStore((state) => state.run);
    const client_id = useEpochStore((state) => state.global.selectedClient?.client_id);

    const onRun = () => {

        const payload = {
            client_id: client_id,
            // TODO - name must be unique to portfolio so we're just reusing the site_id (but we already set that in site_data)
            name: state.taskConfig.site_id,

            task_name: state.taskConfig.task_name,
            optimiser: {
                name: state.taskConfig.optimiser,
                hyperparameters: {}
            },

            search_parameters: state.searchParameters,
            objectives: Object.keys(state.taskConfig.objectives).filter(
                (objective) => state.taskConfig.objectives[objective]
            ),
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
                {/*<HyperParamForm/>*/}
            </AccordionSection>

            <AccordionSection title="Search Form">
                <SearchForm />
            </AccordionSection>
            <Button
                onClick={onRun}
                variant="contained"
                size="large"
            >Run Optimisation</Button>

        </div>
    )
}

export default RunContainer