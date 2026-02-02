// This is the top-level cost model Component

import {FC} from "react";

import {CapexModel, OpexModel, PiecewiseCostModel} from "./Types.ts";
import {Box, Stack, Typography} from "@mui/material";

import AccordionSection from "../../util/Widgets/AccordionSection.tsx";
import {CostModelComponent} from "./CostModelComponent.tsx";
import JsonViewer from "../../util/Widgets/JsonViewer.tsx";


type Props = {
    capexModel: CapexModel;
    onChangeCapex: (next: CapexModel) => void;
    opexModel: OpexModel;
    onChangeOpex: (next: OpexModel) => void;
};


export const CostModelEditor: FC<Props> = ({
    capexModel,
    onChangeCapex,
    opexModel,
    onChangeOpex
}) => {


    const updateCapexField =
        (key: keyof CapexModel) => (next: PiecewiseCostModel): void => {
            onChangeCapex({
                ...capexModel,
                [key]: next
            });
        };

    const dhwParams = {
        dhw: {
            model: capexModel.dhw_prices,
            onChange: updateCapexField("dhw_prices"),
            unitHint: "L",
            fieldName: "Hot Water Cylinder"
        }
    };

    const gasBoilerCapexParams = {
        gasBoiler: {
            model: capexModel.gas_heater_prices,
            onChange: updateCapexField("gas_heater_prices"),
            unitHint: "kW",
            fieldName: "Gas Boiler"
        }
    };

    const heatPumpCapexParams = {
        heatPump: {
            model: capexModel.heatpump_prices,
            onChange: updateCapexField("heatpump_prices"),
            unitHint: "kW",
            fieldName: "Heat Pump"
        }
    };

    const gridParams = {
        gridConnection: {
            model: capexModel.grid_prices,
            onChange: updateCapexField("grid_prices"),
            unitHint: "kW",
            fieldName: "Grid Connection"
        }
    };

    const essCapexParams = {
        essPcs: {
            model: capexModel.ess_pcs_prices,
            onChange: updateCapexField("ess_pcs_prices"),
            unitHint: "kW",
            fieldName: "Power Conversion System"
        },
        essEnclosure: {
            model: capexModel.ess_enclosure_prices,
            onChange: updateCapexField("ess_enclosure_prices"),
            unitHint: "kWh",
            fieldName: "Enclosure"
        },
        essEnclosureDisposal: {
            model: capexModel.ess_enclosure_disposal_prices,
            onChange: updateCapexField("ess_enclosure_disposal_prices"),
            unitHint: "kWh",
            fieldName: "Enclosure Disposal"
        }
    };

    const solarCapexParams = {
        pvPanels: {
            model: capexModel.pv_panel_prices,
            onChange: updateCapexField("pv_panel_prices"),
            unitHint: "kWp",
            fieldName: "PV Panels"
        },
        pvRoof: {
            model: capexModel.pv_roof_prices,
            onChange: updateCapexField("pv_roof_prices"),
            unitHint: "kWp",
            fieldName: "Roof Mounting"
        },
        pvGround: {
            model: capexModel.pv_ground_prices,
            onChange: updateCapexField("pv_ground_prices"),
            unitHint: "£/kWp",
            fieldName: "Ground Mounting"
        },
        pvBoP: {
            model: capexModel.pv_BoP_prices,
            onChange: updateCapexField("pv_BoP_prices"),
            unitHint: "kWp",
            fieldName: "Balance of Plant"
        }
    };


    const updateOpexField =
        (key: keyof OpexModel) =>
            (next: PiecewiseCostModel): void => {
                onChangeOpex({
                    ...opexModel,
                    [key]: next
                });
            };

    const gasBoilerOpexParams = {
        gasBoiler: {
            model: opexModel.gas_heater_prices,
            onChange: updateOpexField("gas_heater_prices"),
            unitHint: "kW",
            fieldName: "Gas Boiler Opex"
        }
    };

    const heatPumpOpexParams = {
        heatPump: {
            model: opexModel.heatpump_prices,
            onChange: updateOpexField("heatpump_prices"),
            unitHint: "kW",
            fieldName: "Heat Pump Opex"
        }
    };

    const essOpexParams = {
        essPcs: {
            model: opexModel.ess_pcs_prices,
            onChange: updateOpexField("ess_pcs_prices"),
            unitHint: "kW",
            fieldName: "PCS Opex"
        },
        essEnclosure: {
            model: opexModel.ess_enclosure_prices,
            onChange: updateOpexField("ess_enclosure_prices"),
            unitHint: "kWh",
            fieldName: "Enclosure Opex"
        }
    };

    const pvOpexParams = {
        pv: {
            model: opexModel.pv_prices,
            onChange: updateOpexField("pv_prices"),
            unitHint: "kWp",
            fieldName: "PV Opex"
        }
    };


    return (
        <Stack spacing={2} my={2} sx={{position: "relative"}}>
            {/* capex */}
            <Typography variant="h6">Cost Model</Typography>
            <Box sx={{position: 'absolute', top: '0', right: '0.5em'}}>
                <JsonViewer data={{"capex_model": capexModel, "opex_model": opexModel}} name={"Cost Model"}/>
            </Box>

            <AccordionSection title={"Capex"} error={false}>
                <AccordionSection title="Domestic Hot Water" error={false}>
                    <CostModelComponent params={dhwParams}/>
                </AccordionSection>

                <AccordionSection title="Gas Boiler" error={false}>
                    <CostModelComponent params={gasBoilerCapexParams}/>
                </AccordionSection>

                <AccordionSection title="Heat Pump" error={false}>
                    <CostModelComponent params={heatPumpCapexParams}/>
                </AccordionSection>

                <AccordionSection title="Grid Connection" error={false}>
                    <CostModelComponent params={gridParams}/>
                </AccordionSection>

                <AccordionSection title="Energy Storage System" error={false}>
                    <CostModelComponent params={essCapexParams}/>
                </AccordionSection>

                <AccordionSection title="Solar PV" error={false}>
                    <CostModelComponent params={solarCapexParams}/>
                </AccordionSection>
            </AccordionSection>

            {/* opex */}
            <AccordionSection title={"Opex"} error={false}>
                <AccordionSection title="Gas Boiler" error={false}>
                    <CostModelComponent params={gasBoilerOpexParams} />
                </AccordionSection>

                <AccordionSection title="Heat Pump" error={false}>
                    <CostModelComponent params={heatPumpOpexParams} />
                </AccordionSection>

                <AccordionSection title="Energy Storage System" error={false}>
                    <CostModelComponent params={essOpexParams} />
                </AccordionSection>

                <AccordionSection title="Solar PV" error={false}>
                    <CostModelComponent params={pvOpexParams} />
                </AccordionSection>
            </AccordionSection>

        </Stack>
    );
};

export default CostModelEditor;
