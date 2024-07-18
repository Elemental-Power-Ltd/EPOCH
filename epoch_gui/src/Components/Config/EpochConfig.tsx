import Form from '@rjsf/mui'
import { RJSFSchema } from '@rjsf/utils';
import validator from '@rjsf/validator-ajv8';

import ConfigSchema from '../../util/json/schema/ConfigSchema.json';
import DefaultConfig from '../../util/json/default/DefaultConfig.json'

import { submitConfig } from '../../endpoints';


const submitForm = data => {
    submitConfig(data.formData).then(
        result => console.log(result)
    );
}


const ConfigForm = () => {

    return (
        <div>
            <h2>CONFIG</h2>

            <Form 
                schema={ConfigSchema as RJSFSchema}
                validator={validator}
                formData={DefaultConfig}
                onSubmit={submitForm}
            />
            {/*
            <div>
                <button>Submit</button>
                <button>Save</button>
            </div>
            */}
        </div>
    )
}

export default ConfigForm;