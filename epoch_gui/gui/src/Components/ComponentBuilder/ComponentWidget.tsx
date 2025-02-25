import React, {FC} from "react";
import {IconButton} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";

import {ComponentType} from "../../Models/Core/ComponentBuilder";

import Form from "@rjsf/mui";
import validator from '@rjsf/validator-ajv8';
import {RJSFSchema} from "@rjsf/utils";


interface ComponentWidgetProps {
    componentKey: ComponentType;
    displayName: string;
    data: any;
    schema: any;

    onRemove: (component: ComponentType) => void;
    onFormChange: (component: ComponentType, event: any) => void;
}

export const ComponentWidget: FC<ComponentWidgetProps> = (
    {componentKey, displayName, data, schema, onRemove, onFormChange}
) => (
    <div
        style={{
            maxWidth: "500px",
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
            schema={getSingleComponentSchema(schema, componentKey) as RJSFSchema}
            uiSchema={{"ui:submitButtonOptions": {"norender": true}}}
            validator={validator}
            // note: we have to wrap the data up in this form
            // as the schema expects a top-level property of [componentKey]
            formData={data}
            onChange={evt => onFormChange(componentKey, evt)}
        />

    </div>
);

// We only pass in the part of the schema that corresponds to this component
// We do this by swapping the top-level properties and required fields for those inside the target component
const getSingleComponentSchema = (schema: any, componentKey: string) => {
    return {
        ...schema,
        properties: {
            ...schema.properties[componentKey].properties
        },
        required: schema.properties[componentKey].required || [],

        // we also unset the title, purely for display purposes
        title: undefined
    };
}
