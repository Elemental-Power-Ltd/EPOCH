import React, {FC} from 'react';
import Form from '@rjsf/mui';
import {RJSFSchema} from '@rjsf/utils';
import validator from '@rjsf/validator-ajv8';

import SiteRangeSchema from "../../util/json/schema/HumanFriendlySiteRangeSchema.json";

import {Button} from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import DownloadIcon from '@mui/icons-material/Download';
import {SiteRange} from "../../State/types";

interface SearchFormProps {
    site_id: string;
    siteRange: SiteRange
    updateSiteRange: (site_id: string, siteRange: SiteRange) => void;
}

const SearchForm: FC<SearchFormProps> = ({site_id, siteRange, updateSiteRange}) => {
    const changeSiteRange = (evt: any) => {
        updateSiteRange(site_id, evt.formData);
    }

    const handleDownload = () => {
        const jsonData = JSON.stringify(siteRange, null, 2);
        const blob = new Blob([jsonData], {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'siteRange.json';
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

                    const validationResult = validator.validateFormData(json, SiteRangeSchema as RJSFSchema);

                    if (validationResult.errors.length === 0) {
                        updateSiteRange(site_id, json);
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
                schema={SiteRangeSchema as RJSFSchema}
                uiSchema={{
                    "ASHP_HSource": {"ui:widget": "checkboxes"},
                    "ui:submitButtonOptions": {"norender": true}
                }}
                validator={validator}
                formData={siteRange}
                onChange={changeSiteRange}
            />
        </div>
    );
}

export default SearchForm;
