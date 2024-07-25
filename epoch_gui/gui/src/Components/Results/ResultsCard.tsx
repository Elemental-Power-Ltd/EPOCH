import React from 'react';
import './ResultsCard.css';

const ResultsCard = ({ data }) => {
  const {
    CAPEX,
    annualised,
    payback_horizon,
    scenario_carbon_balance,
    scenario_cost_balance,
    time_taken
  } = data;

  return (
    <div className="results-card">
      <h2>Results</h2>
      <div className="results-grid">
        <div className="result-item">
          <span className="label">CAPEX:</span>
          <span className="value">£{CAPEX.toLocaleString()}</span>
        </div>
        <div className="result-item">
          <span className="label">Annualised:</span>
          <span className="value">£{annualised.toFixed(2)}</span>
        </div>
        <div className="result-item">
          <span className="label">Payback Horizon:</span>
          <span className="value">{payback_horizon.toFixed(2)} years</span>
        </div>
        <div className="result-item">
          <span className="label">Carbon Balance:</span>
          <span className="value">{scenario_carbon_balance.toFixed(2)} tons</span>
        </div>
        <div className="result-item">
          <span className="label">Cost Balance:</span>
          <span className="value">£{scenario_cost_balance.toFixed(2)}</span>
        </div>
        <div className="result-item">
          <span className="label">Time Taken:</span>
          <span className="value">{time_taken.toFixed(2)} seconds</span>
        </div>
      </div>
    </div>
  );
};

export default ResultsCard;
