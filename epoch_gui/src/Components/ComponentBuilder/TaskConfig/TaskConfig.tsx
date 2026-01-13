import {FC, useState} from "react";

import {Dialog, DialogTitle, DialogContent, Button } from '@mui/material';
import SettingsIcon from '@mui/icons-material/Settings';

import Form from '@rjsf/mui';
import {RJSFSchema} from "@rjsf/utils";
import validator from '@rjsf/validator-ajv8';

import TaskConfigSchema from "../../../util/json/schema/TaskConfigSchema.json"


interface TaskDataConfigFormProps {
    config: any;
    changeConfig: (config: any) => void;
}

const TaskDataConfigForm: FC<TaskDataConfigFormProps> = ({config, changeConfig}) => {

    const [open, setOpen] = useState(false);
    const handleOpen = () => setOpen(true);
    const handleClose = () => setOpen(false);


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
                        onChange={changeConfig}
                    />
                </DialogContent>
            </Dialog>
        </>
    )
}

export default TaskDataConfigForm;
