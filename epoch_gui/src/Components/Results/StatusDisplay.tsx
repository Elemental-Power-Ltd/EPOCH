import "./Results.css"

interface Result {
    CAPEX: number;
    scenario_carbon_balance: number;
    scenario_cost_balance: number;
    payback_horizon: number;
    annualised: number;
    // Add additional properties as needed
}

const RunningStatus = () => {
    return (
        <div className="indicator running">Running
            <span>Scenarios: 999*</span>
        </div>
    )
};

const Results = ({results}: {results: Result}) => {
    return (
        <div className="indicator finished">
            Finished
            <div>Carbon: {results.scenario_carbon_balance}</div>
            <div>CAPEX: {results.CAPEX}</div>
            <div>Payback: {results.payback_horizon}</div>
            <div>Annualised: {results.annualised}</div>
            <div>Cost: {results.scenario_cost_balance}</div>
        </div>
    )
}

const StatusDisplay = ({serverStatus}) => {
    const status = serverStatus.status;

    return (
        <div className="status-container">
            RESULTS:
            {status === 'READY' && <div className="indicator ready">Ready</div>}
            {status === 'RUNNING' && <RunningStatus/>}
            {status === 'FINISHED' && <Results results={serverStatus.results}/>}
            {status !== 'READY' && status !== 'RUNNING' && status !== 'FINISHED' &&
             <div className="indicator unknown">Unknown Status</div>}
        </div>
    )
};


export default StatusDisplay