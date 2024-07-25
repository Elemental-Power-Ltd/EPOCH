import ResultCard from "../Components/Results/ResultsCard";

function ResultsContainer() {
    return (
        <div>
            <ResultCard data={{
              "CAPEX": 751955,
              "annualised": 54265.05078125,
              "payback_horizon": 8.984713554382324,
              "scenario_carbon_balance": 133667.28125,
              "scenario_cost_balance": 83692.703125,
              "time_taken": 9.769560813903809
            }}/>

            <ResultCard data={{
              "CAPEX": 751955,
              "annualised": 54265.05078125,
              "payback_horizon": 8.984713554382324,
              "scenario_carbon_balance": 133667.28125,
              "scenario_cost_balance": 83692.703125,
              "time_taken": 9.769560813903809
            }}/>


            <ResultCard data={{
              "CAPEX": 751955,
              "annualised": 54265.05078125,
              "payback_horizon": 8.984713554382324,
              "scenario_carbon_balance": 133667.28125,
              "scenario_cost_balance": 83692.703125,
              "time_taken": 9.769560813903809
            }}/>

        </div>
    )
}

export default ResultsContainer;