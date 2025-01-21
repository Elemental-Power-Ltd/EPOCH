import React, {FC, useState, useEffect} from "react";
import {Select, MenuItem, SelectChangeEvent} from "@mui/material";
import {Button} from "@mui/material";

import {ComponentType, ComponentsMap} from "../../Models/Core/TaskData"

interface TaskComponentSelectorProps {
    componentsState: ComponentsMap;
    onAddComponent: (component: ComponentType) => void;
}

const TaskComponentSelector: FC<TaskComponentSelectorProps> = ({
                                                                   componentsState,
                                                                   onAddComponent,
                                                               }) => {
    const availableComponents = Object.entries(componentsState)
        .filter(([_, {selected}]) => !selected)
        .map(([key]) => key as ComponentType);

    const [selectedValue, setSelectedValue] = useState<ComponentType | "">(
        availableComponents[0] || ""
    );

    // If the currently selected component is no longer available,
    // reset it to the first available component or an empty string.
    useEffect(() => {
        if (selectedValue && !availableComponents.includes(selectedValue)) {
            setSelectedValue(availableComponents[0] || "");
        }
    }, [availableComponents, selectedValue]);

    const noMoreComponents = availableComponents.length === 0;

    const handleSelectChange = (e: SelectChangeEvent<ComponentType | "">) => {
        setSelectedValue(e.target.value as ComponentType);
    };

    const handleAddClick = () => {
        if (selectedValue && typeof selectedValue === "string") {
            onAddComponent(selectedValue as ComponentType);
        }
    };

    return (
        <div>
            <Select
                label="Component"
                value={selectedValue}
                onChange={handleSelectChange}
                disabled={noMoreComponents}
            >
                {availableComponents.map((component) => (
                    <MenuItem key={component} value={component}>
                        {componentsState[component].displayName}
                    </MenuItem>
                ))}
            </Select>
            <Button onClick={handleAddClick} disabled={noMoreComponents}>
                Add Component
            </Button>
        </div>
    );
};

export default TaskComponentSelector;
