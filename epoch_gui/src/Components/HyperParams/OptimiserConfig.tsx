import { useState } from 'react';

import { Dialog, DialogTitle, DialogContent, Button } from '@mui/material';

import Form from '@rjsf/mui'
import { RJSFSchema } from '@rjsf/utils';
import validator from '@rjsf/validator-ajv8';

import GridSchema from '../../util/json/schema/GridConfigSchema.json';
import NSGA2Schema from "../../util/json/schema/NSGA2Schema.json";

import {useEpochStore} from "../../State/Store";


const HyperParamForm = () => {

    const state = useEpochStore((state) => state.optimise);

    const setHyperparameters = useEpochStore(state => state.setHyperparameters);
    const changeParams = (evt: any) => {setHyperparameters(state.taskConfig.optimiser, evt.formData)}

    const [open, setOpen] = useState(false);
    const handleOpen = () => setOpen(true);
    const handleClose = () => setOpen(false);

    return (
        <>
            <Button variant="text" onClick={handleOpen} sx={{margin: "1em"}}>
                Advanced Settings
            </Button>

            <Dialog open={open} onClose={handleClose}>
                <DialogTitle>Hyperparameters</DialogTitle>
                <DialogContent>
                    {state.taskConfig.optimiser === "GridSearch" &&
                        <Form
                            schema={GridSchema as RJSFSchema}
                            uiSchema={{ "ui:submitButtonOptions": { "norender": true } }}
                            validator={validator}
                            formData={state.hyperparameters.GridSearch}
                            onChange={changeParams}
                        />
                    }

                    {state.taskConfig.optimiser === "NSGA2" &&
                        <Form
                            schema={NSGA2Schema as RJSFSchema}
                            uiSchema={{ "ui:submitButtonOptions": { "norender": true } }}
                            validator={validator}
                            formData={state.hyperparameters.NSGA2}
                            onChange={changeParams}
                        />
                    }

                </DialogContent>
            </Dialog>
        </>
    );
};


export default HyperParamForm;
