import {useState} from "react";

import AccordionSection from "../util/Widgets/AccordionSection";
import AddSiteModal from "../Components/SearchParameters/AddSite";

import {
    Button,
    Box,
    IconButton,
    Container,
    TextField,
    Paper,
    CircularProgress,
    Typography,
    Stack
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';

import {submitOptimisationJob} from "../endpoints";

import {useEpochStore} from "../State/Store";
import OptimiserConfigForm from "../Components/TaskConfig/OptimiserConfigForm.tsx";
import {SubmitOptimisationRequest, Objective, CostModelResponse, Constraints} from "../Models/Endpoints";
import expandSiteRange, {PortfolioValidationResult} from "../Components/ComponentBuilder/ConvertSiteRange";
import ComponentBuilderForm from "../Components/ComponentBuilder/ComponentBuilderForm";
import ErrorList from "../Components/ComponentBuilder/ErrorList";
import {CostModelPicker} from "../Components/CostModel/CostModelPicker.tsx";
import {useNavigate} from "react-router-dom";


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

    const [portfolioCapexBudget, setPortfolioCapexBudget] = useState<number | undefined>(undefined);

    const [costModel, setCostModel] = useState<CostModelResponse | null>(null);

    const setConfig = useEpochStore((state) => state.setConfig);

    const handlePortfolioCapexChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const val = e.target.value;
        setPortfolioCapexBudget(val === '' ? undefined : Number(val));
    };

    const [submitLoading, setSubmitLoading] = useState<boolean>(false);
    const [submitError, setSubmitError] = useState<string | null>(null);
    const navigate = useNavigate();

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

        // A cost model must be loaded
        if (!costModel?.capex_model || !costModel?.opex_model) {
            return false;
        }

        // each site must either inherit the parent cost model or set their own

        const sitesHaveCostModels = Object.keys(state.portfolioMap).every((site_id) => {
            const siteConfig = state.portfolioMap[site_id].config;
            return siteConfig.inherit_cost_model === true || siteConfig.site_cost_model !== null;
        });

        if (!sitesHaveCostModels) {
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

    // either return the portfolio cost model or use the site-specific one
    // depending on the value of config.inherit_cost_model
    const manipulateConfig = (site_id: string) => {
        const {inherit_cost_model, site_cost_model, ...remainingConfig} = state.portfolioMap[site_id].config;

        if (inherit_cost_model) {
            return {
                ...remainingConfig,
                capex_model: costModel!.capex_model,
                opex_model: costModel!.opex_model,
            }
        } else {
            return {
                ...remainingConfig,
                capex_model: site_cost_model.capex_model,
                opex_model: site_cost_model.opex_model,
            }
        }
    }

    // form site-level constraints
    // for now we simply read the capex_limit and transform it into the Optimisation Service format for constraints
    const makeSiteConstraints = (site_id: string) => {
        let constraints: Constraints = {};

        const capex_limit: number | undefined = state.portfolioMap[site_id].config.capex_limit;

        if (capex_limit) {
            constraints["capex"] = {"max": capex_limit};
        }

        return constraints;
    }

    const onRun = async () => {

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

        const portfolio_constraints =
            portfolioCapexBudget ? {"capex": {"max": portfolioCapexBudget}} : {};


        const payload: SubmitOptimisationRequest = {
            name: state.taskConfig.task_name,
            optimiser: {
                name: state.taskConfig.optimiser,
                hyperparameters: state.hyperparameters[state.taskConfig.optimiser],
            },
            objectives: selected_objectives,
            portfolio: Object.keys(state.portfolioMap).map((site_id: string) => ({
                name: "-",
                site_range: portfolioSiteRanges[site_id],
                site_data: {
                    site_id: site_id,
                    start_ts: state.taskConfig.start_date!.toISOString(),
                    // an EPOCH year is exactly 8760 hours (irrespective of leap years)
                    end_ts: state.taskConfig.start_date!.add(8760, "hour").toISOString()
                },
                constraints: makeSiteConstraints(site_id),
                config: manipulateConfig(site_id)
            })),
            portfolio_constraints: portfolio_constraints,
            client_id: client_id!
        }

        setSubmitLoading(true);
        setSubmitError(null);

        const submitResult = await submitOptimisationJob(payload);
        if (submitResult.success) {
            setSubmitError(null);
            navigate("/results")
        } else {
            setSubmitError(submitResult.error || "Unknown error");
        }
        setSubmitLoading(false);

    }

    const renderSiteBuilder = (site_id: string) => {
        const hasErrors = site_id in portfolioRangeErrors

        const siteName = client_sites.find((site) => site.site_id === site_id)?.name || site_id;

        return (
            <Box
                key={site_id}
                sx={{display: 'flex', flexDirection: 'row', alignItems: 'flex-start', mb: 2 }}
            >
                <Box sx={{flex: 1}}>
                    <AccordionSection title={siteName} error={hasErrors}>
                        {hasErrors && <ErrorList errors={portfolioRangeErrors[site_id]}/>}
                        <ComponentBuilderForm
                            mode={"SiteRangeMode"}
                            siteInfo={state.portfolioMap[site_id]}
                            // supply versions of each zustand function that operate on the individual site
                            addComponent={(componentKey: string) => addComponent(site_id, componentKey)}
                            removeComponent={(componentKey: string) => removeComponent(site_id, componentKey)}
                            updateComponent={(componentKey: string, newData: any) => updateComponent(site_id, componentKey, newData)}
                            setComponents={(siteRange: any) => setSiteRange(site_id, siteRange)}
                            getComponents={() => getSiteRange(site_id)}
                            setConfig={(config: any) => setConfig(site_id, config)}
                            site_id={site_id}
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

    const renderPortfolioCapexLimit = () => (
        <Container maxWidth="sm">
            <Box
                component="form"
                noValidate
                autoComplete="off"
                sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mb: '1em'
                }}
            >
                <TextField
                    label="Portfolio Capex Limit"
                    type="number"
                    value={portfolioCapexBudget ?? ''}
                    onChange={handlePortfolioCapexChange}
                    fullWidth
                    variant="outlined"
                    inputProps={{inputMode: 'numeric', step: 10000}}
                />
            </Box>
        </Container>
    )

    // @ts-ignore
    return (
        <Container maxWidth={"xl"}>
            <OptimiserConfigForm/>

            {Object.keys(state.portfolioMap).map((site_id) => renderSiteBuilder(site_id))}

            <Button variant="outlined" size="large" onClick={()=>setSiteModalOpen(true)}>
                Add Site
            </Button>

            <Box my={2}>
                <Paper variant="outlined" sx={{ p: 1 }}>
                    <CostModelPicker costModel={costModel} setCostModel={setCostModel}/>
                </Paper>
            </Box>

            {renderPortfolioCapexLimit()}

            {submitError &&
                <Typography variant="body2" color="error">
                    {submitError}
                </Typography>
            }

            <Button
                onClick={onRun}
                disabled={!canRun() || submitLoading}
                variant="contained"
                size="large"
            >
                {submitLoading ? (
                    <Stack direction="row" spacing={1.5} alignItems="center">
                        <CircularProgress size={18} color="inherit"/>
                        <Typography variant="button">
                            Submitting task…
                        </Typography>
                    </Stack>
                ) : (
                    "Run Optimisation"
                )}
            </Button>

            <AddSiteModal
                open={siteModalOpen}
                onClose={()=>setSiteModalOpen(false)}
                availableSites={client_sites}
                onAddSite={addSite}
            />
        </Container>
    )
}

export default OptimisationContainer