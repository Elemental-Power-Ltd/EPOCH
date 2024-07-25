import Form from '@rjsf/mui'
import { RJSFSchema } from '@rjsf/utils';
import validator from '@rjsf/validator-ajv8';

import InputSchema from '../../util/json/schema/InputSchema.json';
import {useEpochStore} from "../../State/state";


const SearchForm = () => {

    const state = useEpochStore((state) => state.run);
    const setSearchSpace = useEpochStore((state) => state.setSearchSpace);

    const changeSearchSpace = (evt: any) => {
        setSearchSpace(evt.formData);
    }


    return (
        <div>
            <h2>SEARCH</h2>

            <Form
                schema={InputSchema as RJSFSchema}
                uiSchema={{
                    "ASHP_HSource": {"ui:widget": "checkboxes"},
                    "ui:submitButtonOptions": {"norender": true}
                }}
                validator={validator}
                formData={state.searchSpace}
                onChange={changeSearchSpace}
            />

            {/*<div>*/}
            {/*    <button>Submit</button>*/}
            {/*    <button>Save</button>*/}
            {/*</div>*/}
        </div>
    )
}

export default SearchForm;