import {FC, useState} from "react";

import {Dialog, DialogTitle, DialogContent, Button, Box, FormControlLabel, Checkbox, Divider} from '@mui/material';
import SettingsIcon from '@mui/icons-material/Settings';

import Form from '@rjsf/mui';
import {RJSFSchema} from "@rjsf/utils";
import validator from '@rjsf/validator-ajv8';

import TaskConfigSchema from "../../../util/json/schema/TaskConfigSchema.json"
import {CostModelPicker} from "../../CostModel/CostModelPicker.tsx";
import {CostModelResponse} from "../../../Models/Endpoints.ts";


interface TaskDataConfigFormProps {
    config: any;
    changeConfig: (config: any) => void;
}

const TaskDataConfigForm: FC<TaskDataConfigFormProps> = ({config, changeConfig}) => {

    const [open, setOpen] = useState(false);
    const handleOpen = () => setOpen(true);
    const handleClose = () => setOpen(false);

    // this is a bit of a hack
    // we only want to allow cost model overriding in contexts where there is a portfolio
    // SiteRange configs will have the inherit_cost_model property
    // TaskData configs will not
    const hasCostModel = config.inherit_cost_model !== undefined;

    const setSiteCostModel = (cost_model: CostModelResponse | null) => {
        changeConfig({...config, site_cost_model: cost_model})
    }

    const renderCostInheritor = () => {
        const inherits = config.inherit_cost_model;

        return (
            <Box>
                <FormControlLabel
                    control={
                        <Checkbox
                            checked={inherits}
                            onChange={(e) => {
                                const checked = e.target.checked;
                                changeConfig({...config, inherit_cost_model: checked, site_cost_model: null})
                            }}
                        />
                    }
                    label="Inherit Portfolio Cost-Model"
                />
                { !inherits && <CostModelPicker costModel={config.site_cost_model} setCostModel={setSiteCostModel}/> }
            </Box>
        )
    }

    return (
        <>
            <Button variant="text" onClick={handleOpen} sx={{margin: "1em"}} startIcon={<SettingsIcon/>}>
                    Settings
            </Button>

            <Dialog open={open} onClose={handleClose}>
                <DialogTitle>Settings</DialogTitle>
                <DialogContent>
                    <Form
                        schema={TaskConfigSchema as RJSFSchema}
                        uiSchema={{ "ui:submitButtonOptions": { "norender": true } }}
                        validator={validator}
                        formData={config}
                        onChange={(evt) => changeConfig(evt.formData)}
                    />
                    {hasCostModel &&
                        <>
                            <Divider sx={{mb: 2}}/>
                            {renderCostInheritor()}
                        </>
                    }
                </DialogContent>
            </Dialog>

        </>
    )
}

export default TaskDataConfigForm;
