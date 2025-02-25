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
import expandSiteRange, {PortfolioValidationResult} from "../Components/ComponentBuilder/ConvertSiteRange";
import ComponentBuilderForm from "../Components/ComponentBuilder/ComponentBuilderForm";
import ErrorList from "../Components/ComponentBuilder/ErrorList";
import {validateSiteRange} from "../Components/ComponentBuilder/ValidateBuilders";


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
    const [portfolioRangeErrors, setPortfolioRangeErrors] = useState<Record<string, string[]>>({});

    /**
     * perform simple checks about the validity of the task configuration
     * (checks in this function will be run on every state update so must be quick)
     */
    const canRun = (): boolean => {
        if (!client_id) {
            return false;
        }

        if (!state.taskConfig.start_date) {
            return false;
        }

        // at least one objective must be true
        if (Object.values(state.taskConfig.objectives).every(value => value === false)) {
            return false;
        }

        // Task must contain at least one site
        if (Object.keys(state.portfolioMap).length === 0) {
            return false;
        }

        return true;
    }

    /**
     * perform more detailed validation of the SiteRange properties to check everything is valid
     * These checks are more expensive and update the display with errors
     * so we don't want to run them on every state update
     */
    const validatePortfolioRange = (): PortfolioValidationResult  => {

        const portfolioSiteRanges: Record<string, any> = {};
        const newPortfolioRangeErrors: Record<string, string[]> = {};

        Object.keys(state.portfolioMap).forEach((site_id: string) => {
            const siteRange = getSiteRange(site_id);

            const expandResult = expandSiteRange(siteRange);
            if (!expandResult.success) {
                newPortfolioRangeErrors[site_id] = expandResult.errors;
            } else {
                portfolioSiteRanges[site_id] = expandResult.data;
            }
        })

        if (Object.keys(newPortfolioRangeErrors).length) {
            // We have encountered errors with at least one SiteRange in the portfolio
            // set the errors so that we can display them in the appropriate place
            console.error(newPortfolioRangeErrors);
            setPortfolioRangeErrors(newPortfolioRangeErrors);
            return {success: false};
        }

        // clear any errors that were displayed before submitting this task
        setPortfolioRangeErrors({});
        return {success: true, data: portfolioSiteRanges};
    }

    const onRun = () => {

        if (!canRun()) {
            return;
        }

        const selected_objectives: Objective[] = (Object.keys(state.taskConfig.objectives) as Objective[]).filter(
                (objective) => state.taskConfig.objectives[objective]
            );

        const result = validatePortfolioRange();

        if (!result.success) {
            return;
        }
        const portfolioSiteRanges = result.data!;


        const payload: SubmitOptimisationRequest = {
            name: state.taskConfig.task_name,
            optimiser: {
                name: state.taskConfig.optimiser,
                hyperparameters: {}
            },
            objectives: selected_objectives,
            portfolio: Object.keys(state.portfolioMap).map((site_id: string) => ({
                name: "-",
                site_range: portfolioSiteRanges[site_id],
                site_data: {
                    loc: "remote",
                    site_id: site_id,
                    start_ts: state.taskConfig.start_date!.toISOString(),
                    // an EPOCH year is exactly 8760 hours (irrespective of leap years)
                    end_ts: state.taskConfig.start_date!.add(8760, "hour").toISOString()
                }
            })),
            portfolio_constraints: {},
            client_id: client_id!
        }

        submitOptimisationJob(payload);
    }

    const renderSiteBuilder = (site_id: string) => {
        const hasErrors = site_id in portfolioRangeErrors

        return (
            <Box
                key={site_id}
                sx={{display: 'flex', flexDirection: 'row', alignItems: 'flex-start', mb: 2 }}
            >
                <Box sx={{flex: 1}}>
                    <AccordionSection title={site_id} error={hasErrors}>
                        {hasErrors && <ErrorList errors={portfolioRangeErrors[site_id]}/>}
                        <ComponentBuilderForm
                            mode={"SiteRangeMode"}
                            componentsMap={state.portfolioMap[site_id]}
                            // supply versions of each zustand function that operate on the individual site
                            addComponent={(componentKey: string) => addComponent(site_id, componentKey)}
                            removeComponent={(componentKey: string) => removeComponent(site_id, componentKey)}
                            updateComponent={(componentKey: string, newData: any) => updateComponent(site_id, componentKey, newData)}
                            setComponents={(siteRange: any) => setSiteRange(site_id, siteRange)}
                            getComponents={() => getSiteRange(site_id)}
                        />
                    </AccordionSection>
                </Box>
                <IconButton
                    onClick={() => removeSite(site_id)}
                    aria-label="delete"
                    sx={{ml: 2}} // margin left
                >
                    <DeleteIcon/>
                </IconButton>
            </Box>
        )
    }

    return (
        <div className="run-tab">
            <TaskConfigForm/>

            {Object.keys(state.portfolioMap).map((site_id) => renderSiteBuilder(site_id))}

            <Button variant="outlined" size="large" onClick={()=>setSiteModalOpen(true)}>
                Add Site
            </Button>
            <Button onClick={onRun} disabled={!canRun()} variant="contained" size="large">
                Run Optimisation
            </Button>

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