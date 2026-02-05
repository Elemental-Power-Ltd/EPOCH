BEGIN;

CREATE TABLE IF NOT EXISTS optimisation.cost_models (
    cost_model_id UUID PRIMARY KEY,
    model_name TEXT,
    capex_model JSONB,
    opex_model JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE optimisation.site_task_config ADD COLUMN site_config JSONB;

INSERT INTO optimisation.cost_models (cost_model_id, model_name, capex_model, opex_model)
VALUES (
    uuidv7(),
    'Default Cost Model',
    '{
    "dhw_prices": {
      "fixed_cost": 1000,
      "segments": [
        {
          "upper": 300,
          "rate": 6.5
        },
        {
          "upper": 800,
          "rate": 5
        }
      ],
      "final_rate": 3
    },
    "gas_heater_prices": {
      "fixed_cost": 1000,
      "segments": [
        {
          "upper": 100,
          "rate": 250
        },
        {
          "upper": 200,
          "rate": 225
        }
      ],
      "final_rate": 200
    },
    "grid_prices": {
      "fixed_cost": 0,
      "segments": [
        {
          "upper": 50,
          "rate": 240
        },
        {
          "upper": 1000,
          "rate": 160
        }
      ],
      "final_rate": 120
    },
    "heatpump_prices": {
      "fixed_cost": 4000,
      "segments": [
        {
          "upper": 15,
          "rate": 800
        },
        {
          "upper": 100,
          "rate": 2500
        }
      ],
      "final_rate": 1500
    },
    "ess_pcs_prices": {
      "fixed_cost": 0,
      "segments": [
        {
          "upper": 50,
          "rate": 250
        },
        {
          "upper": 1000,
          "rate": 125
        }
      ],
      "final_rate": 75
    },
    "ess_enclosure_prices": {
      "fixed_cost": 0,
      "segments": [
        {
          "upper": 100,
          "rate": 480
        },
        {
          "upper": 2000,
          "rate": 360
        }
      ],
      "final_rate": 300
    },
    "ess_enclosure_disposal_prices": {
      "fixed_cost": 0,
      "segments": [
        {
          "upper": 100,
          "rate": 30
        },
        {
          "upper": 2000,
          "rate": 20
        }
      ],
      "final_rate": 15
    },
    "pv_panel_prices": {
      "fixed_cost": 0,
      "segments": [
        {
          "upper": 50,
          "rate": 150
        },
        {
          "upper": 1000,
          "rate": 110
        }
      ],
      "final_rate": 95
    },
    "pv_roof_prices": {
      "fixed_cost": 4250,
      "segments": [
        {
          "upper": 50,
          "rate": 850
        },
        {
          "upper": 1000,
          "rate": 750
        }
      ],
      "final_rate": 600
    },
    "pv_ground_prices": {
      "fixed_cost": 4250,
      "segments": [
        {
          "upper": 50,
          "rate": 800
        },
        {
          "upper": 1000,
          "rate": 600
        }
      ],
      "final_rate": 500
    },
    "pv_BoP_prices": {
      "fixed_cost": 0,
      "segments": [
        {
          "upper": 50,
          "rate": 120
        },
        {
          "upper": 1000,
          "rate": 88
        }
      ],
      "final_rate": 76
    }
  }'::jsonb,
    '{
    "ess_pcs_prices": {
      "fixed_cost": 0,
      "segments": [
        {
          "upper": 50,
          "rate": 8
        },
        {
          "upper": 1000,
          "rate": 4
        }
      ],
      "final_rate": 1
    },
    "ess_enclosure_prices": {
      "fixed_cost": 0,
      "segments": [
        {
          "upper": 100,
          "rate": 10
        },
        {
          "upper": 2000,
          "rate": 4
        }
      ],
      "final_rate": 2
    },
    "gas_heater_prices": {
      "fixed_cost": 0,
      "segments": [],
      "final_rate": 0
    },
    "heatpump_prices": {
      "fixed_cost": 0,
      "segments": [],
      "final_rate": 0
    },
    "pv_prices": {
      "fixed_cost": 0,
      "segments": [
        {
          "upper": 50,
          "rate": 2
        },
        {
          "upper": 1000,
          "rate": 1
        }
      ],
      "final_rate": 0.5
    }
  }'::jsonb
)
ON CONFLICT (cost_model_id) DO NOTHING;

END;
