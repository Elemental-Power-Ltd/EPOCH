#pragma once

#include "../epoch_lib/Simulation/SiteData.hpp"
#include "../epoch_lib/io/FileHandling.hpp"
#include <Eigen/Core>
#include <chrono>
#include <vector>

/**
* Make a Generic SiteData of Eigen::Ones of length n
* With a start_ts and end_ts 
*/
inline SiteData makeNHourSiteData(int n) {
    FabricIntervention fi;
    fi.cost = 999.0f;
    fi.reduced_hload = Eigen::VectorXf::Ones(n);

    Eigen::MatrixXf inMat(2, 2);
    inMat << 1.0f, 2.0f, 3.0f, 4.0f;
    Eigen::MatrixXf outMat(2, 2);
    outMat << 4.0f, 8.0f, 12.0f, 16.0f;

    // start_ts: 1st Jan 2022, midnight
    std::chrono::system_clock::time_point start = fromIso8601("2022-01-01T00:00:00Z");
    // end_ts: n hours later
    std::chrono::system_clock::time_point end = start + std::chrono::hours(n);

    return SiteData(
        start,
        end,
        Eigen::VectorXf::Ones(n), // building_eload
        Eigen::VectorXf::Ones(n), // building_hload
        Eigen::VectorXf::Ones(n), // ev_eload
        Eigen::VectorXf::Ones(n), // dhw_demand
        Eigen::VectorXf::Ones(n), // air_temperature
        Eigen::VectorXf::Ones(n), // grid_co2
        {
            Eigen::VectorXf::Ones(n),
            Eigen::VectorXf::Ones(n)
        }, // solar_yields
        {
            Eigen::VectorXf::Ones(n),
            Eigen::VectorXf::Ones(n)
        }, // import_tariffs
        std::vector<FabricIntervention>{ fi },
        inMat,
        outMat
    );
}

/*
* Construct a SiteData over 24 hours where every vector is made using Eigen::Ones
*/
inline SiteData make24HourSiteData() {
    return makeNHourSiteData(24);
}


/**
* Construct a minimal TaskData that should be valid when paired with make24HourSiteData()
*/
inline TaskData makeValidTaskData() {
    TaskData taskData;

    Building building;
    building.fabric_intervention_index = 0;

    GridData grid;
    grid.tariff_index = 0;

    // We provide 2 yield_scalars to match make24HourSiteData()
    Renewables renewables;
    renewables.yield_scalars = { 1.0f, 1.0f };

    taskData.building = building;
    taskData.grid = grid;
    taskData.renewables = renewables;

    return taskData;
}