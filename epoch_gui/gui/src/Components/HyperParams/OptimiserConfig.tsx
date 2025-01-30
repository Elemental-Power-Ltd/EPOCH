import "./OptimiserConfig.css"

import Form from '@rjsf/mui'
import { RJSFSchema } from '@rjsf/utils';
import validator from '@rjsf/validator-ajv8';

import { Select, SelectChangeEvent, MenuItem, InputLabel } from '@mui/material';

import GridSchema from '../../util/json/schema/GridConfigSchema.json';
import GASchema from '../../util/json/schema/GAConfigSchema.json';

import {useEpochStore} from "../../State/Store";


const HyperParamForm = () => {

    const state = useEpochStore((state) => state.optimise);

    const { setGridConfig, setGAConfig } = useEpochStore(state => ({
        setGridConfig: state.setGridConfig,
        setGAConfig: state.setGAConfig
    }));

    const changeGridConfig = (evt: any) => {setGridConfig(evt.formData);}
    const changeGAConfig = (evt: any) => {setGAConfig(evt.formData);}


    return (
        <div>
            {state.taskConfig.optimiser === "GridSearch" &&
                <Form
                    schema={GridSchema as RJSFSchema}
                    uiSchema={{"ui:submitButtonOptions": {"norender": true}}}
                    validator={validator}
                    formData={state.hyperparameters.gridSearch}
                    onChange={changeGridConfig}
                />
            }

            {state.taskConfig.optimiser === "GeneticAlgorithm" &&
                <Form
                    schema={GASchema as RJSFSchema}
                    uiSchema={{"ui:submitButtonOptions": {"norender": true}}}
                    validator={validator}
                    formData={state.hyperparameters.geneticAlgorithm}
                    onSubmit={changeGAConfig}

                />
            }
        </div>
    )
}

export default HyperParamForm;
