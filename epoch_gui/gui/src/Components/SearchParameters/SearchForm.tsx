import React from 'react';
import Form from '@rjsf/mui';
import {RJSFSchema} from '@rjsf/utils';
import validator from '@rjsf/validator-ajv8';

import InputSchema from '../../util/json/schema/SearchParametersSchema.json';
import {useEpochStore} from "../../State/state";

import {Button, IconButton} from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import DownloadIcon from '@mui/icons-material/Download';

const SearchForm = () => {
    const state = useEpochStore((state) => state.run);
    const setSearchParameters = useEpochStore((state) => state.setSearchParameters);

    const changeSearchParameters = (evt: any) => {
        setSearchParameters(evt.formData);
    }

    const handleDownload = () => {
        const jsonData = JSON.stringify(state.searchParameters, null, 2);
        const blob = new Blob([jsonData], {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'search_parameters.json';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };

    const handleUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const json = JSON.parse(e.target?.result as string);

                    // try and validate the uploaded JSON against the schema

                    // TODO - the schema is currently too permissive as there are no required fields at the top level
                    //  so almost any JSON is parsed as valid

                    const validationResult = validator.validateFormData(json, InputSchema as RJSFSchema);

                    if (validationResult.errors.length === 0) {
                        setSearchParameters(json);
                    } else {
                        console.error("Invalid Search Parameters");
                        console.error(validationResult.errors);
                        alert("Failed to parse search parameters!")
                    }
                } catch (error) {
                    console.error("Invalid JSON file");
                    alert("Invalid JSON file");
                }
            };
            reader.readAsText(file);
        }
    };

    return (
        <div>
            <div style={{marginTop: '20px'}}>
                <Button
                    variant="outlined"
                    onClick={handleDownload}
                    startIcon={<DownloadIcon/>}
                    style={{marginRight: '10px'}}
                >
                    Download Parameters
                </Button>

                <label htmlFor="upload-json-file">
                    <input
                        id="upload-json-file"
                        type="file"
                        accept=".json"
                        onChange={handleUpload}
                        style={{display: 'none'}}
                    />
                    <Button
                        variant="outlined"
                        component="span"
                        startIcon={<UploadFileIcon/>}
                    >
                        Upload Parameters
                    </Button>
                </label>
            </div>
            <h2>SEARCH</h2>
            <Form
                schema={InputSchema as RJSFSchema}
                uiSchema={{
                    "ASHP_HSource": {"ui:widget": "checkboxes"},
                    "ui:submitButtonOptions": {"norender": true}
                }}
                validator={validator}
                formData={state.searchParameters}
                onChange={changeSearchParameters}
            />
        </div>
    );
}

export default SearchForm;
