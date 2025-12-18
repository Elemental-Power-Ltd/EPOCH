// Holds the cost models for each varying parameter within a component
// This is a stateless component, the stateful behaviour should be handled by the parent 'CostModelEditor'

import {FC} from "react";

import {PiecewiseCostModel} from "./Types.ts";
import {Stack} from "@mui/material";
import {CostModelElement} from "./CostModelElement.tsx";


interface ElementInfo {
    model: PiecewiseCostModel;
    onChange: (next: PiecewiseCostModel) => void;
    unitHint?: string;
    fieldName?: string;
    readOnly?: boolean;
}


type Props = {
    params: Record<string, ElementInfo>
}

export const CostModelComponent: FC<Props> = ({params}) => {

    return (
        <Stack direction="column" spacing={2}>
            {Object.entries(params).map(([paramName, info]) => (
                <CostModelElement
                    key={paramName}
                    model={info.model}
                    onChange={info.onChange}
                    unitHint={info.unitHint}
                    fieldName={info.fieldName}
                />
            ))}
        </Stack>

    )
}
