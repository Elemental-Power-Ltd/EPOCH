import "./OptimiserConfig.css"

import Form from '@rjsf/mui'
import { RJSFSchema } from '@rjsf/utils';
import validator from '@rjsf/validator-ajv8';

import { Select, SelectChangeEvent, MenuItem, InputLabel } from '@mui/material';

import GridSchema from '../../util/json/schema/GridConfigSchema.json';
import GASchema from '../../util/json/schema/GAConfigSchema.json';

import {useEpochStore} from "../../State/state";


const HyperParamForm = () => {

    const state = useEpochStore((state) => state.run);

    const { setSite, setOptimiser, setGridConfig, setGAConfig } = useEpochStore(state => ({
        setSite: state.setSite,
        setOptimiser: state.setOptimiser,
        setGridConfig: state.setGridConfig,
        setGAConfig: state.setGAConfig
    }));

    const changeOptimiser = (evt: SelectChangeEvent) => {setOptimiser(evt.target.value);}
    const changeSite = (evt: SelectChangeEvent) => {setSite(evt.target.value);}
    const changeGridConfig = (evt: any) => {setGridConfig(evt.formData);}
    const changeGAConfig = (evt: any) => {setGAConfig(evt.formData);}


    return (
        <div>
            {state.taskConfig.optimiser === "GridSearch" &&
                <Form
                    schema={GridSchema as RJSFSchema}
                    uiSchema={{"ui:submitButtonOptions": {"norender": true}}}
                    validator={validator}
                    formData={state.optimisers.gridSearch}
                    onChange={changeGridConfig}
                />
            }

            {state.taskConfig.optimiser === "GeneticAlgorithm" &&
                <Form
                    schema={GASchema as RJSFSchema}
                    uiSchema={{"ui:submitButtonOptions": {"norender": true}}}
                    validator={validator}
                    formData={state.optimisers.geneticAlgorithm}
                    onSubmit={changeGAConfig}

                />
            }
        </div>
    )
}

export default HyperParamForm;
