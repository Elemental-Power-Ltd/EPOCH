import {useComponentBuilderState} from "../ComponentBuilder/useComponentBuilderState.ts";
import {GasType, TaskData} from "../TaskDataViewer/TaskData.ts";
import {Button, CircularProgress, GridLegacy as Grid, Typography} from "@mui/material";
import ComponentBuilderForm from "../ComponentBuilder/ComponentBuilderForm.tsx";
import {addSiteBaseline} from "../../endpoints.tsx";


interface BaselineFormProps {
    selectedSite: string;
    baselineLoading: boolean;
    setBaselineLoading: (value: boolean) => void;
    baselineError: string | null;
    setBaselineError: (value: string | null) => void;
}


const BaselineForm = ({
                          selectedSite,
                          baselineLoading,
                          setBaselineLoading,
                          baselineError,
                          setBaselineError
                      }: BaselineFormProps) => {


    const defaultBaseline: TaskData = {
        building: {
            scalar_heat_load: 1,
            scalar_electrical_load: 1,
            fabric_intervention_index: 0,
            floor_area: undefined,
            incumbent: false,
            age: 0,
            lifetime: 30
        },
        gas_heater: {
            maximum_output: 40,
            gas_type: "NATURAL_GAS" as GasType,
            boiler_efficiency: 0.9,
            fixed_gas_price: 0.068,
            incumbent: false,
            age: 0,
            lifetime: 10
        },
        grid: {
            grid_export: 23,
            grid_import: 23,
            import_headroom: 0.25,
            tariff_index: 0,
            export_tariff: 0.05,
            incumbent: false,
            age: 0,
            lifetime: 25
        }
    }


    const componentBuilderState = useComponentBuilderState("TaskDataMode", defaultBaseline);
    const getTaskData = componentBuilderState.getComponents;

    const submitBaseline = async () => {
        if (!selectedSite) {
            return
        }

        setBaselineLoading(true);
        setBaselineError(null);

        try {
            const res = await addSiteBaseline(selectedSite, getTaskData());
            if (!res.success) {
                setBaselineError(res.error ?? "Unknown error");
            }
        } catch (error) {
            setBaselineError(error instanceof Error ? error.message : "Unknown Error");
        } finally {
            setBaselineLoading(false);
        }
    }

    return (
        <>
            <Typography variant="h5" gutterBottom mt={2}>
                Configure Baseline
            </Typography>

            <ComponentBuilderForm
                mode="TaskDataMode"
                siteInfo={componentBuilderState.siteInfo}
                addComponent={componentBuilderState.addComponent}
                removeComponent={componentBuilderState.removeComponent}
                updateComponent={componentBuilderState.updateComponent}
                setComponents={componentBuilderState.setComponents}
                getComponents={getTaskData}
                setConfig={null}
                site_id={"site"}
            />
            <Button
                fullWidth
                variant="contained"
                color="primary"
                disabled={selectedSite === ""}
                onClick={submitBaseline}
            >
                {baselineLoading ? <CircularProgress size={24}/> : 'Add Site Baseline'}
            </Button>
            {baselineError && (
                <Grid item xs={12}>
                    <Typography variant="body2" color="error">
                        {baselineError}
                    </Typography>
                </Grid>
            )}
        </>
    )
}

export default BaselineForm;
