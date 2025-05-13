import { useState } from 'react';

import { Dialog, DialogTitle, DialogContent, Button, MenuItem, Select, FormControl, InputLabel } from '@mui/material';

import Form from '@rjsf/mui'
import { RJSFSchema } from '@rjsf/utils';
import validator from '@rjsf/validator-ajv8';

import GridSchema from '../../util/json/schema/GridConfigSchema.json';
import NSGA2Schema from "../../util/json/schema/NSGA2Schema.json";

import {useEpochStore} from "../../State/Store";
import {OptimisationApproach} from "../../State/types"


const HyperParamForm = () => {

    const state = useEpochStore((state) => state.optimise);

    const setOptimiser = useEpochStore(state => state.setOptimiser);
    const setHyperparameters = useEpochStore(state => state.setHyperparameters);
    const changeParams = (evt: any) => {setHyperparameters(state.taskConfig.optimiser, evt.formData)}

    const [open, setOpen] = useState(false);
    const handleOpen = () => setOpen(true);
    const handleClose = () => setOpen(false);
    
    return (
        <>
            <Button variant="text" onClick={handleOpen} sx={{ margin: "1em" }}>
                Advanced Settings
            </Button>

            <Dialog open={open} onClose={handleClose} fullWidth>
                <DialogTitle>Hyperparameters</DialogTitle>
                <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
                    
                    <FormControl fullWidth variant="outlined" margin="dense">
                        <InputLabel id="optimiser-select-label">Algorithm</InputLabel>
                        <Select
                            labelId="optimiser-select-label"
                            value={state.taskConfig.optimiser}
                            label="Algorithm"
                            onChange={(e) => setOptimiser(e.target.value as OptimisationApproach)}
                        >
                            <MenuItem value="GridSearch">Grid Search</MenuItem>
                            <MenuItem value="NSGA2">NSGA-II</MenuItem>
                        </Select>
                    </FormControl>

                    {state.taskConfig.optimiser === "GridSearch" && (
                        <Form
                            schema={GridSchema as RJSFSchema}
                            uiSchema={{ "ui:submitButtonOptions": { "norender": true }, "ui:options": { label: false }}}
                            validator={validator}
                            formData={state.hyperparameters.GridSearch}
                            onChange={changeParams}
                        />
                    )}

                    {state.taskConfig.optimiser === "NSGA2" && (
                        <Form
                            schema={NSGA2Schema as RJSFSchema}
                            uiSchema={{ "ui:submitButtonOptions": { "norender": true }, "ui:options": { label: false }}}
                            validator={validator}
                            formData={state.hyperparameters.NSGA2}
                            onChange={changeParams}
                        />
                    )}
                </DialogContent>
            </Dialog>
        </>
    );
};

export default HyperParamForm;