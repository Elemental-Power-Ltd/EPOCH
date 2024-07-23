import Form from '@rjsf/mui'
import { RJSFSchema } from '@rjsf/utils';
import validator from '@rjsf/validator-ajv8';

import InputSchema from '../../util/json/schema/InputSchema2.json';
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
                uiSchema={{"ASHP_HSource": {"ui:widget": "checkboxes"}}}
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