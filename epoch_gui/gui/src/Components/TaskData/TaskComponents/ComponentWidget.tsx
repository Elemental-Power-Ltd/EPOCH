import React, {FC} from "react";
import {IconButton} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";

import {ComponentType} from "../../../Models/Core/TaskData";

import Form from "@rjsf/mui";
import validator from '@rjsf/validator-ajv8';
import TaskDataSchema from "../../../util/json/schema/TaskDataSchema.json";
import {RJSFSchema} from "@rjsf/utils";


interface ComponentWidgetProps {
    componentKey: ComponentType;
    displayName: string;
    onRemove: (component: ComponentType) => void;
    data: any;
    onFormChange: (component: ComponentType, event: any) => void;
}

export const ComponentWidget: FC<ComponentWidgetProps> = (
    {componentKey, displayName, onRemove, data, onFormChange}
) => (
    <div
        style={{
            flex: "1 1 300px",
            minWidth: "240px",
            maxWidth: "400px",
            border: "1px solid #ccc",
            borderRadius: "4px",
            padding: "16px",
            display: "flex",
            flexDirection: "column",
            gap: "12px",
            position: "relative",
        }}
    >
        {/* Close Button in Top-Right Corner */}
        <IconButton
            onClick={() => onRemove(componentKey)}
            style={{
                position: "absolute",
                top: "8px",
                right: "8px",
                zIndex: 10,
            }}
            size="small"
        >
            <CloseIcon/>
        </IconButton>

        <h3 style={{margin: 0, textAlign: "center"}}>{displayName}</h3>


        <Form
            // We only pass in the part of the schema that corresponds to this component
            // Note: this is technically not correct as it strips out all the metadata and
            // definition sections of the schema
            // TODO - it would be more correct to write a function to filter out all the other components each time

            schema={TaskDataSchema["properties"][componentKey] as RJSFSchema}
            uiSchema={{"ui:submitButtonOptions": {"norender": true}}}
            validator={validator}

            formData={data}
            onChange={evt => onFormChange(componentKey, evt)}
        />

    </div>
);
