import {useState} from "react";

import AccordionSection from "../util/Widgets/AccordionSection";
import HyperParamForm from "../Components/HyperParams/OptimiserConfig";
import SearchForm from "../Components/SearchParameters/SearchForm";
import AddSiteModal from "../Components/SearchParameters/AddSite";
import DefaultSiteRange from "../util/json/default/DefaultHumanFriendlySiteRange.json";

import {Button, Box, IconButton} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';

import {getStatus, submitOptimisationJob} from "../endpoints";

import {useEpochStore} from "../State/Store";
import TaskConfigForm from "../Components/TaskConfig/TaskConfigForm";
import {SubmitOptimisationRequest, Objective} from "../Models/Endpoints";
import {SiteRange} from "../State/types";
import expandSiteRange from "../Components/ComponentBuilder/ConvertSiteRange";
import ComponentBuilderForm from "../Components/ComponentBuilder/ComponentBuilderForm";
import {ComponentBuilderState, useComponentBuilderState} from "../Components/ComponentBuilder/useComponentBuilderState";

function OptimisationContainer() {

    const state = useEpochStore((state) => state.optimise);
    const client_id = useEpochStore((state) => state.global.selectedClient?.client_id);
    const client_sites = useEpochStore((state) => state.global.client_sites);


    const addSite = useEpochStore((state) => state.addSiteRange);
    const removeSite = useEpochStore((state) => state.removeSiteRange);

    const addComponent = useEpochStore((state) => state.addComponent);
    const removeComponent = useEpochStore((state) => state.removeComponent);
    const updateComponent = useEpochStore((state) => state.updateComponent);

    // in this context, setComponents and getComponents are for a SiteRange
    const setSiteRange = useEpochStore((state) => state.setComponents);
    const getSiteRange = useEpochStore((state) => state.getComponents);

    const [siteModalOpen, setSiteModalOpen] = useState<boolean>(false);

    const onRun = () => {

        if (!client_id) {
            return;
        }

        const selected_objectives: Objective[] = Object.keys(state.taskConfig.objectives).filter(
                (objective) => state.taskConfig.objectives[objective]
            );

        const produceSiteRange = (builder: ComponentBuilderState): SiteRange => {
            // first get the components out of the ComponentBuilder
            const humanFriendlySiteRange = builder.getComponents();
            // Then expand {min,max,step} into arrays
            return expandSiteRange(humanFriendlySiteRange);
        }

        const payload: SubmitOptimisationRequest = {
            name: state.taskConfig.task_name,
            optimiser: {
                name: state.taskConfig.optimiser,
                hyperparameters: {}
            },
            objectives: selected_objectives,
            portfolio: Object.keys(state.portfolioMap).map((site_id: string) => ({
                name: "-",
                site_range: expandSiteRange(getSiteRange(site_id)),
                site_data: {
                    loc: "remote",
                    site_id: site_id,
                    start_ts: state.taskConfig.start_date,
                    duration: state.taskConfig.duration
                }
            })),
            portfolio_constraints: {},
            client_id: client_id

        }

        // ignore the response for now
        submitOptimisationJob(payload);
    }

    return (
        <div className="run-tab">
            <TaskConfigForm/>

            {Object.keys(state.portfolioMap).map((site_id) => (
                <Box
                    key={site_id}
                    sx={{
                        display: 'flex',
                        flexDirection: 'row',
                        alignItems: 'flex-start',
                        mb: 2, // margin bottom
                    }}
                >
                    <Box sx={{flex: 1}}>
                        <AccordionSection title={site_id}>
                            <ComponentBuilderForm
                                mode={"SiteRangeMode"}
                                componentsMap={state.portfolioMap[site_id]}
                                // supply versions of each zustand function that operate on the individual site
                                addComponent={(componentKey: string)=>addComponent(site_id, componentKey)}
                                removeComponent={(componentKey: string)=>removeComponent(site_id, componentKey)}
                                updateComponent={(componentKey: string, newData: any) => updateComponent(site_id, componentKey, newData)}
                                setComponents={(siteRange: any) => setSiteRange(site_id, siteRange)}
                                getComponents={()=>getSiteRange(site_id)}
                            />
                        </AccordionSection>
                    </Box>
                    <IconButton
                        onClick={()=>removeSite(site_id)}
                        aria-label="delete"
                        sx={{ml: 2}} // margin left
                    >
                        <DeleteIcon/>
                    </IconButton>
                </Box>
            ))}

            <Button
                variant="outlined"
                size="large"
                onClick={()=>setSiteModalOpen(true)}
            >Add Site
            </Button>
            <Button
                onClick={onRun}
                disabled={Object.keys(state.portfolioMap).length === 0}
                variant="contained"
                size="large"
            >Run Optimisation</Button>

            <AddSiteModal
                open={siteModalOpen}
                onClose={()=>setSiteModalOpen(false)}
                availableSites={client_sites}
                onAddSite={addSite}
            />
        </div>
    )
}

export default OptimisationContainer