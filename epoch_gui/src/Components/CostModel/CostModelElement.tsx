// A simple wrapper for one 'element' in the cost model
// This wrapper places the cost model editor and a plot alongside one another
import {FC} from "react";

import {Card, CardContent, CardHeader, Stack, Typography} from "@mui/material";

import {PiecewiseEditor} from "./PiecewiseEditor.tsx";
import {CostModelPlot} from "./CostModelPlot";
import {PiecewiseCostModel} from "./Types.ts";


type Props = {
    model: PiecewiseCostModel;
    onChange: (next: PiecewiseCostModel) => void;
    unitHint?: string;
    fieldName?: string;
    readOnly?: boolean;
}


export const CostModelElement: FC<Props> = ({model, onChange, unitHint, fieldName, readOnly}) => {

    return (
        <Card variant="outlined" sx={{borderRadius: 4, boxShadow: "sm"}}>
            <CardHeader
                title={<Typography variant="h6">{fieldName ?? "Cost Model"}</Typography>}
            />


            <CardContent>
                <Stack direction="row" spacing={2}>
                    <PiecewiseEditor model={model} onChange={onChange} readOnly={readOnly}/>
                    <CostModelPlot model={model} unitHint={unitHint}/>
                </Stack>
            </CardContent>

        </Card>

    )
};

