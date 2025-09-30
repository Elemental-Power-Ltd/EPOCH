import "./ComponentBuilderForm.css"
import {FC, useId, useState} from "react";
import ComponentSelector from "./ComponentSelector";
import {ComponentWidget} from "./ComponentWidget";
import {Button} from "@mui/material";
import FileUploadIcon from "@mui/icons-material/FileUpload";
import FileDownloadIcon from "@mui/icons-material/FileDownload";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import Masonry from "react-masonry-css";

import {BuilderMode, ComponentsMap, ComponentType} from "../../Models/Core/ComponentBuilder";
import {useComponentBuilderFileHandlers} from "./useComponentBuilderFileHandlers";

import TaskDataSchema from "../../util/json/schema/TaskDataSchema.json";
import SiteRangeSchema from "../../util/json/schema/HumanFriendlySiteRangeSchema.json";
import TaskDataConfigForm from "./TaskConfig/TaskConfig.tsx";

interface ComponentBuilderFormProps {
    mode: BuilderMode;
    componentsMap: ComponentsMap;
    addComponent: (component: ComponentType) => void;
    removeComponent: (component: ComponentType) => void;
    updateComponent: (component: ComponentType, data: any) => void;
    setComponents: (data: any) => void;
    getComponents: () => any;
    site_id: string;
}


const ComponentBuilderForm: FC<ComponentBuilderFormProps> = (props) => {

    const {
        mode,
        componentsMap,
        addComponent,
        removeComponent,
        updateComponent,
        setComponents,
        getComponents,
        site_id
    } = props;

    const {onUpload, onDownload, onCopy} = useComponentBuilderFileHandlers({
        mode,
        setData: setComponents
    });

    // We have to give each html form a distinct ID to prevent the wrong upload/download button being used
    const formSpecificId = useId();
    const formSpecificLabel = `upload-${formSpecificId}`

    const selectedComponents = Object.entries(componentsMap)
        // we filter out the config as we display this in a different way
        .filter(([key, _])=> key !== "config")
        .filter(([_, {selected}]) => selected)
        .map(([key]) => key as ComponentType);


    const handleTaskComponentChange = (component: ComponentType, evt: any) => {
        updateComponent(component, evt.formData);
    };

    const schema = (mode === "TaskDataMode") ? TaskDataSchema : SiteRangeSchema;

    // start with all components expanded (selected or not)
    const [expandedMap, setExpandedMap] = useState<Record<ComponentType, boolean>>({
        building: true,
        data_centre: true,
        domestic_hot_water: true,
        electric_vehicles: true,
        energy_storage_system: true,
        gas_heater: true,
        grid: true,
        heat_pump: true,
        mop: true,
        solar_panels: true,
        config: true
    });

    const handleAccordionToggle = (componentKey: ComponentType) => {
        setExpandedMap((prev) => ({
            ...prev,
            [componentKey]: !prev[componentKey]
        }));
    };

    const config = componentsMap["config"].data;
    const changeConfig = (evt: any) => handleTaskComponentChange("config", evt);

    return (
        <>
            <ComponentSelector
                componentsState={componentsMap}
                onAddComponent={addComponent}
                onRemoveComponent={removeComponent}
            />
            <TaskDataConfigForm config={config} changeConfig={changeConfig}/>

            <Masonry
                breakpointCols={{
                    default: 3,  // 3 columns for large screens
                    1100: 2,     // 2 columns for >= 1100px
                    700: 1       // 1 column for >= 700px
                }}
                className="component-builder-masonry"
                columnClassName="component-builder-masonry-column"
            >
                {selectedComponents.map((component) => (
                        <ComponentWidget
                            key={component}
                            componentKey={component}
                            displayName={componentsMap[component].displayName}
                            data={componentsMap[component].data}
                            schema={schema}
                            onRemove={removeComponent}
                            onFormChange={handleTaskComponentChange}
                            isExpanded={expandedMap[component]}
                            toggleExpanded={()=>handleAccordionToggle(component)}
                        />
                ))}
            </Masonry>

            <div style={{marginTop: "1rem", display: "flex", gap: "8px"}}>
                <label htmlFor={formSpecificLabel}>
                    <input
                        id={formSpecificLabel}
                        type="file"
                        accept=".json"
                        onChange={onUpload}
                        style={{display: "none"}}
                    />
                    <Button
                        variant="outlined"
                        component="span"
                        size="large"
                        startIcon={<FileUploadIcon/>}
                    >
                        Upload
                    </Button>
                </label>
                <Button
                    variant="outlined"
                    startIcon={<FileDownloadIcon/>}
                    onClick={() => onDownload(getComponents(), site_id)}
                >
                    Download
                </Button>

                <Button
                    variant="outlined"
                    startIcon={<ContentCopyIcon/>}
                    onClick={async () => await onCopy(getComponents())}
                >
                    Copy
                </Button>
            </div>
        </>
    );
}

export default ComponentBuilderForm;