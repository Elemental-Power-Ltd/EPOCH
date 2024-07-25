import "./OptimiserConfig.css"

import Form from '@rjsf/mui'
import { RJSFSchema } from '@rjsf/utils';
import validator from '@rjsf/validator-ajv8';

import Select, { SelectChangeEvent } from '@mui/material/Select';
import MenuItem from "@mui/material/MenuItem";
import {InputLabel} from "@mui/material";

import GridSchema from '../../util/json/schema/GridConfigSchema.json';
import GASchema from '../../util/json/schema/GAConfigSchema.json';



import { submitConfig } from '../../endpoints';
import {useEpochStore} from "../../State/state";


const submitForm = data => {
    submitConfig(data.formData).then(
        result => console.log(result)
    );
}

enum Optimiser {
    GridSearch = "Grid Search",
    GeneticAlgorithm = "Genetic Algorithm"
}


const ConfigForm = () => {

    const state = useEpochStore((state) => state.run);

    const { setSite, setOptimiser, setGridConfig, setGAConfig } = useEpochStore(state => ({
        setSite: state.setSite,
        setOptimiser: state.setOptimiser,
        setGridConfig: state.setGridConfig,
        setGAConfig: state.setGAConfig
    }));

    const changeOptimiser = (evt: SelectChangeEvent) => {setOptimiser(evt.target.value as Optimiser);}
    const changeSite = (evt: SelectChangeEvent) => {setSite(evt.target.value);}
    const changeGridConfig = (evt: any) => {setGridConfig(evt.formData);}
    const changeGAConfig = (evt: any) => {setGAConfig(evt.formData);}


    return (
        <div>
            <h2>CONFIG</h2>
            <h3>{state.selectedSite}</h3>
            <div className="optimiser-key-details">
                <InputLabel id="opt-select">Optimiser</InputLabel>

                <Select id="optimiser" labelId="opt-select" value={state.selectedOptimiser} onChange={changeOptimiser}>
                    <MenuItem value={Optimiser.GridSearch}>{Optimiser.GridSearch}</MenuItem>
                    <MenuItem value={Optimiser.GeneticAlgorithm}>{Optimiser.GeneticAlgorithm}</MenuItem>
                </Select>

                <InputLabel id="site-select">Site</InputLabel>
                <Select id="site" labelId="site-select" value={state.selectedSite} onChange={changeSite}>
                    {state.availableSites.map(site =>
                        <MenuItem value={site} key={site}>{site}</MenuItem>)
                    }
                </Select>
            </div>

            {state.selectedOptimiser === Optimiser.GridSearch &&
                <Form
                    schema={GridSchema as RJSFSchema}
                    uiSchema={{"ui:submitButtonOptions": {"norender": true}}}
                    validator={validator}
                    formData={state.optimisers.gridSearch}
                    onChange={changeGridConfig}
                />
            }

            {state.selectedOptimiser === Optimiser.GeneticAlgorithm &&
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

export default ConfigForm;
