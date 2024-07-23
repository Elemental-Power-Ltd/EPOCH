import "./OptimiserConfig.css"

import {useState} from "react";
import Form from '@rjsf/mui'
import { RJSFSchema } from '@rjsf/utils';
import validator from '@rjsf/validator-ajv8';

import Select, { SelectChangeEvent } from '@mui/material/Select';
import MenuItem from "@mui/material/MenuItem";
import {InputLabel} from "@mui/material";

import GridSchema from '../../util/json/schema/GridConfigSchema.json';
import DefaultGrid from '../../util/json/default/DefaultGridConfig.json'

import GASchema from '../../util/json/schema/GAConfigSchema.json';
import DefaultGA from '../../util/json/default/DefaultGAConfig.json'


import { submitConfig } from '../../endpoints';


const submitForm = data => {
    submitConfig(data.formData).then(
        result => console.log(result)
    );
}

enum Optimiser {
    GridSearch = "Grid Search",
    GeneticAlgorithm = "Genetic Algorithm"
}

const sites: string[] = ["Mount Hotel", "Retford Town Hall", "10 Downing Street", "Sydney Opera House"]


const ConfigForm = () => {

    const [optimiser, setOptimiser] = useState<Optimiser>(Optimiser.GridSearch);
    const [siteData, setSiteData] = useState<string>(sites[0]);

    const changeOptimiser = (evt: SelectChangeEvent) => {
        setOptimiser(evt.target.value as Optimiser);
    }

    const changeSite = (evt: SelectChangeEvent) => {
        setSiteData(evt.target.value);
    }


    return (
        <div>
            <h2>CONFIG</h2>
            <div className="optimiser-key-details">
                <InputLabel id="opt-select">Optimiser</InputLabel>
                <Select id="optimiser" labelId="opt-select" value={optimiser} onChange={changeOptimiser}>
                    <MenuItem value={Optimiser.GridSearch}>{Optimiser.GridSearch}</MenuItem>
                    <MenuItem value={Optimiser.GeneticAlgorithm}>{Optimiser.GeneticAlgorithm}</MenuItem>
                </Select>

                <InputLabel id="site-select">Site</InputLabel>
                <Select id="site" labelId="site-select" value={siteData} onChange={changeSite}>
                    {sites.map(site => <MenuItem value={site}>{site}</MenuItem>)}
                </Select>
            </div>

            {/*FIXME: This conditional rendering approach isn't very good
            because it will reset to the default values whenever you switch forms*/}
            {optimiser===Optimiser.GridSearch &&
            <Form
                schema={GridSchema as RJSFSchema}
                validator={validator}
                formData={DefaultGrid}
                onSubmit={submitForm}
            />
            }

            {optimiser===Optimiser.GeneticAlgorithm &&
            <Form
                schema={GASchema as RJSFSchema}
                validator={validator}
                formData={DefaultGA}
                onSubmit={submitForm}
            />
            }
        </div>
    )
}

export default ConfigForm;