import Form from '@rjsf/mui'
import { RJSFSchema } from '@rjsf/utils';
import validator from '@rjsf/validator-ajv8';

import InputSchema from '../../util/json/schema/InputSchema.json';
import DefaultInput from '../../util/json/default/DefaultInput.json'


const submitForm = data => {
    console.log(data.formData);
    // submitConfig(data.formData).then(
    //     result => console.log(result)
    // );
}


const SearchForm = () => {

    return (
        <div>
            <h2>SEARCH</h2>

            <Form
                schema={InputSchema as RJSFSchema}
                validator={validator}
                formData={DefaultInput}
                onSubmit={submitForm}
            />

            <div>
                <button>Submit</button>
                <button>Save</button>
            </div>
        </div>
    )
}

export default SearchForm;