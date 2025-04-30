import {FC} from "react";
import { Button, Box } from "@mui/material";

import {ComponentType, ComponentsMap, defaultExcludedComponents} from "../../Models/Core/ComponentBuilder"

import {getComponentInfo} from "./ComponentDisplayInfo";

interface ComponentSelectorProps {
    componentsState: ComponentsMap;
    onAddComponent: (component: ComponentType) => void;
    onRemoveComponent: (component: ComponentType) => void;
}

const ComponentSelector: FC<ComponentSelectorProps> = (
    {componentsState, onAddComponent, onRemoveComponent}) => {

    const allComponentTypes = Object.keys(componentsState) as ComponentType[];

    const componentTypes = allComponentTypes
        // filter out the config as we display this in a different way
        .filter((component) => component !== "config")
        // filter out the excluded components
        .filter((component) => !defaultExcludedComponents.includes(component));


    const onToggle = (type: ComponentType) => {
        if (componentsState[type].selected) {
            onRemoveComponent(type);
        } else {
            onAddComponent(type);
        }
    }

    return (
        <Box display="flex" flexWrap="wrap" justifyContent="center" align-items="center" gap={2}>
            {componentTypes.map((type) => {
                const {displayName, icon} = getComponentInfo(type);
                const isSelected = componentsState[type].selected;

                return (
                    <Button
                        key={type}
                        variant={isSelected ? "contained" : "outlined"}
                        color={isSelected ? "primary" : "inherit"}
                        onClick={() => onToggle(type)}
                        startIcon={icon}
                        sx={{
                            minWidth: 120,
                            textTransform: "none",
                            whiteSpace: "nowrap",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                        }}
                    >
                        {displayName}
                    </Button>
                );
            })}
        </Box>
    );
};

export default ComponentSelector;
