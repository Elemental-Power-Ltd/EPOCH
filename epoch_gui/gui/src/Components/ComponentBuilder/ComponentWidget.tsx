import { FC } from "react";
import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Box,
  IconButton,
  Typography,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import CloseIcon from "@mui/icons-material/Close";
import Form from "@rjsf/mui";
import validator from "@rjsf/validator-ajv8";
import { RJSFSchema } from "@rjsf/utils";

import { ComponentType } from "../../Models/Core/ComponentBuilder";

interface ComponentWidgetProps {
  componentKey: ComponentType;
  displayName: string;
  data: any;
  schema: any;
  onRemove: (component: ComponentType) => void;
  onFormChange: (component: ComponentType, event: any) => void;
  isExpanded: boolean;
  toggleExpanded: () => void;
}

export const ComponentWidget: FC<ComponentWidgetProps> = ({
  componentKey,
  displayName,
  data,
  schema,
  onRemove,
  onFormChange,
  isExpanded,
  toggleExpanded
}) => {

  return (
    <Accordion expanded={isExpanded} onChange={toggleExpanded}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ flexDirection: 'row-reverse' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
          <Typography variant="h6" sx={{ flex: 1, textAlign: 'center' }}>
            {displayName}
          </Typography>
          <IconButton
            onClick={(e) => {
              e.stopPropagation();
              onRemove(componentKey);
            }}
            size="small"
          >
            <CloseIcon />
          </IconButton>
        </Box>
      </AccordionSummary>

      <AccordionDetails>
        <Form
          schema={getSingleComponentSchema(schema, componentKey) as RJSFSchema}
          uiSchema={{ "ui:submitButtonOptions": { norender: true } }}
          validator={validator}
          formData={data}
          onChange={(evt) => onFormChange(componentKey, evt)}
        />
      </AccordionDetails>
    </Accordion>
  );
};


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
