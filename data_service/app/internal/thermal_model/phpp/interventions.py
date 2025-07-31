"""List of all U-values for structural elements that THIRD_PARTY might consider."""

from enum import StrEnum
from typing import TypedDict

# ruff: noqa: E501
MATERIAL_U_VALUES: dict[str, float] = {
    "19mm Render, 75mm foam board, Brick 102mm, Plaster": 0.3,
    "19mm Render, 75mm foam board, Brick 228mm, Plaster": 0.28,
    "19mm Render, 75mm foam board, Brick 343mm, Plaster": 0.27,
    "19mm Render, 75mm foam board, concrete 102mm, Plaster": 0.31,
    "19mm Render, 75mm foam board, concrete 152mm, Plaster": 0.3,
    "19mm Render, 75mm foam board, concrete 204mm, Plaster": 0.3,
    "19mm Render, 75mm foam board, concrete 254mm, Plaster": 0.3,
    "Brick 102mm, plaster": 2.97,
    "Brick 102.5mm, cavity, membrane, plywood 10mm, studding 100mm, with infill insulation 80mm, vapour membrane, plasterboard 12.5mm": 0.32,
    "Brick 102.5mm, cavity, membrane, plywood 10mm, studding 100mm, with infill insulation 60mm, vapour membrane, plasterboard 12.5mm": 0.43,
    "Brick 102mm, 50mm  mineral slab, brick 102mm, 13mm plaster": 0.56,
    "Brick 102mm, 50mm mineral slab, brick 102mm, 12.5mm plasterboard on dabs": 0.53,
    "Brick 102mm, 75mm foam board, 12.5mm plasterboard": 0.3,
    "Brick 102mm, cavity, 100mm standard aerated block, 12.5mm plasterboard on dabs": 0.8,
    "Brick 102mm, cavity, 100mm standard aerated block, 13mm plaster": 0.87,
    "Brick 102mm, cavity, 125mm standard aerated block, 12.5mm plasterboard on dabs": 0.72,
    "Brick 102mm, cavity, 125mm standard aerated block, 13mm plaster": 0.77,
    "Brick 102mm, cavity, 100mm high performance aerated block, 12.5mm plasterboard on dabs": 0.64,
    "Brick 102mm, cavity, 100mm high performance aerated bloc, 13mm plaster": 0.68,
    "Brick 102mm, cavity, 125mm high performance aerated block, 12.5mm plasterboard on dabs": 0.56,
    "Brick 102mm, cavity, 125mm high performance aerated block, 13mm plaster": 0.59,
    "Brick 102mm, cavity, brick 102mm, 12.5mm plasterboard on dabs": 1.21,
    "Brick 102mm, cavity, brick 102mm, 13mm plaster": 1.37,
    "Brick 102mm, mineral wool slab in cavity 50mm, 100mm standard aerated block, 13mm plaster": 0.45,
    "Brick 102mm, mineral wool slab in cavity 50mm, 100mm standard aerated block, 12.5mm plasterboard on dabs": 0.43,
    "Brick 102mm, mineral wool slab in cavity 50mm, 120mm standard aerated block, 13mm plaster": 0.42,
    "Brick 102mm, mineral wool slab in cavity 50mm, 125mm standard aerated block, 12.5mm plasterboard on dabs": 0.41,
    "Brick 102mm, mineral wool slab in cavity 50mm, 100mm high performance aerated block, 13mm plaster": 0.39,
    "Brick 102mm, mineral wool slab in cavity 50mm, 120mm high performance aerated block, 13mm plaster": 0.36,
    "Brick 102mm, mineral wool slab in cavity 50mm, 100mm high performance aerated block, 12.5mm plasterboard on dabs": 0.38,
    "Brick 102mm, mineral wool slab in cavity 50mm, 125mm high performance aerated block, 12.5mm plasterboard on dabs": 0.35,
    "Brick 228mm, plaster": 2.11,
    "Brick 228mm, 75mm foam board, 12.5mm plasterboard": 0.29,
    "Brick 343mm, plaster": 1.64,
    "Brick 343mm, 75mm foam board, 12.5mm plasterboard": 0.28,
    "Concrete 102mm, plaster": 3.51,
    "Concrete 152mm, plaster": 3.12,
    "Concrete 204mm, plaster": 2.8,
    "Concrete 254mm, plaster": 2.54,
    # Ground Floor
    "Screed 50mm, concrete slab 150mm, 100mm insulation between battens, 6mm sheeting, heat flow downward - exposed to outside air or unheated space": 0.57,
    "Screed 50mm, concrete slab 150mm, no insulation between battens, 6mm sheeting, heat flow downward - exposed to outside air or unheated space": 1.82,
    # Intermediate floors
    "Intermediate floors, boarding 19mm, airspace between joists, 9.5mm plasterboard heat flow downward": 1.41,
    "Intermediate floors, boarding 19mm, airspace 100mm insulation between joists, 9.5mm plasterboard heat flow downward": 0.31,
    "Intermediate floors, boarding 19mm, airspace between joists, 9.5mm plasterboard heat flow upward": 1.73,
    "Intermediate floors, boarding 19mm, airspace 100mm insulation between joists, 9.5mm plasterboard heat flow upward": 0.32,
    "Boarding 19mm, airspace between joists, no insulation, 6mm sheeting - heat flow downward exposed to outside air or unheated space": 1.75,
    "Boarding 19mm, airspace between joists, 100mm insulation, 6mm sheeting - heat flow downward exposed to outside air or unheated space": 0.33,
    "Boarding 19mm, airspace between joists, 150mm insulation, 6mm sheeting - heat flow downward exposed to outside air or unheated space": 0.23,
    # Pitched roof, no sarking
    "Pitched roof - Slates or tiles, ventilated air space, no insulation, 9.5mm plasterboard": 3.13,
    "Pitched roof - Slates or tiles, ventilated air space, 50mm insulation between joists, 9.5mm plasterboard": 0.62,
    "Pitched roof - Slates or tiles, ventilated air space, 100mm insulation between joists, 9.5mm plasterboard": 0.35,
    "Pitched roof - Slates or tiles, ventilated air space, 200mm insulation between joists, 9.5mm plasterboard": 0.18,
    "Pitched roof - Slates or tiles, ventilated air space, 300mm insulation between joists, 9.5mm plasterboard": 0.12,
    # Pitched roof with sarking
    "Pitched roof - Slates or tiles, sarking felt, ventilated air space, no insulation, 9.5mm plasterboard": 2.51,
    "Pitched roof - Slates or tiles, sarking felt, ventilated air space, 50mm insulation between joists, 9.5mm plasterboard": 0.6,
    "Pitched roof - Slates or tiles, sarking felt, ventilated air space, 50mm insulation between rafters, 9.5mm plasterboard": 0.6,
    "Pitched roof - Slates or tiles, sarking felt, ventilated air space, 100mm insulation between joists, 9.5mm plasterboard": 0.34,
    "Pitched roof - Slates or tiles, sarking felt, ventilated air space, 100mm insulation between rafters, 9.5mm plasterboard": 0.34,
    "Pitched roof - Slates or tiles, sarking felt, ventilated air space, 200mm insulation between joists, 9.5mm plasterboard": 0.18,
    "Pitched roof - Slates or tiles, sarking felt, ventilated air space, 200mm insulation between rafters, 9.5mm plasterboard": 0.18,
    "Pitched roof - Slates or tiles, sarking felt, ventilated air space, 300mm insulation between joists, 9.5mm plasterboard": 0.12,
    "Pitched roof - Slates or tiles, sarking felt, ventilated air space, 300mm insulation between rafters, 9.5mm plasterboard": 0.12,
    # Flat roof
    "Chippings, 3 layers of felt, boarding, air space, no insulation, 9.5mm plasterboard": 1.69,
    "Chippings, 3 layers of felt, boarding, air space, 50mm insulation, 9.5mm plasterboard": 0.53,
    "Chippings, 3 layers of felt, boarding, air space, 100mm insulation, 9.5mm plasterboard": 0.32,
    "Chippings, 3 layers of felt, boarding, air space, 200mm insulation, 9.5mm plasterboard": 0.17,
    "Chippings, 3 layers of felt, boarding, air space, 300mm insulation, 9.5mm plasterboard": 0.12,
    #  Doubly plastered solid walls
    "Plaster 13mm, block 10mm, cavity, block 100mm, plaster 13mm": 1.02,
    "Plaster 13mm, brick 102.5mm, plaster 13mm": 1.76,
    "Plaster 13mm, brick 215mm, plaster 13mm": 1.33,
    "Plaster 13mm, standard aerated block 100mm, plaster 13mm": 1.66,
    "Plaster 13mm, standard aerated block 125mm, plaster 13mm": 1.53,
    "Plaster 13mm, breeze block 100mm, plaster 13mm": 1.58,
    "Plasterboard 12.5mm, studding 75mm, plasterboard 12.5mm": 1.72,
    "Render 19mm, brick 102mm, 50mm mineral wool slab,  brick 102mm, 13mm plaster": 0.54,
    "Render 19mm, brick 102mm, 50mm mineral wool slab, brick 102mm, 12.5mm plasterboard on dabs": 0.51,
    "Render 19mm, brick 102mm, cavity, 100mm standard aerated block, 13mm plaster": 0.82,
    "Render 19mm, brick 102mm, cavity, 125mm standard aerated block, 13mm plaster": 0.73,
    "Render 19mm, brick 102mm, cavity, brick 102mm, 12.5mm plasterboard on dabs": 1.11,
    "Render 19mm, brick 102mm, cavity, brick 102mm, 13mm plaster": 1.25,
    "Render 19mm, brick 102mm, mineral wool slab in cavity 50mm, 100mm standard aerated block, 13mm plaster": 0.44,
    "Render 19mm, brick 102mm, mineral wool slab in cavity 50mm, 125mm standard aerated block, 13mm plaster": 0.41,
    "Render 19mm, high performance aerated block 215mm, 13mm plaster": 0.44,
    "Render 19mm, standard aerated block 100mm, cavity, 100mm  high performance aerated block, 13mm plaster": 0.51,
    "Render 19mm, standard aerated block 100mm, cavity, 100mm standard aerated block, 13mm plaster": 0.61,
    "Render 19mm, standard aerated block 100mm, cavity, 125mm high performance aerated block, 13mm plaster": 0.45,
    "Render 19mm, standard aerated block 100mm, cavity, 125mm standard aerated block, 13mm plaster": 0.56,
    "Render 19mm, standard aerated block 100mm, mineral wool slab in cavity 50mm, 100mm high performance aerated block, 13mm plaster": 0.33,
    "Render 19mm, standard aerated block 100mm, mineral wool slab in cavity 50mm, 100mm standard aerated block, 13mm plaster": 0.37,
    "Render 19mm, standard aerated block 100mm, mineral wool slab in cavity 50mm, 125mm high performance aerated block, 13mm plaster": 0.31,
    "Render 19mm, standard aerated block 100mm, mineral wool slab in cavity 50mm, 125mm standard aerated block, 13mm plaster": 0.35,
    "Stone 305mm": 2.78,
    "Stone 305mm, 100mm mineral wool, plasterboard on battens": 0.33,
    "Stone 457mm": 2.23,
    "Stone 457mm, 100mm mineral wool, plasterboard on battens": 0.32,
    "Stone 610mm": 1.86,
    "Stone 610mm, 100mm mineral wool, plasterboard on battens": 0.32,
    # EXTERNAL WALL INSULATION
    # Tiled external walls
    "Tiles, airspace, cavity, membrane, plywood 10mm, studding 100mm, with infill insulation 60mm, vapour membrane, plasterboard 12.5mm": 0.47,
    "Tiles, airspace, cavity, membrane, plywood 10mm, studding 100mm, with infill insulation 80mm, vapour membrane, plasterboard 12.5mm": 0.38,
    "Tiles, airspace, high performance aerated block, 215mm, 13mm plaster": 0.43,
    "Tiles, airspace, standard aerated block 100mm, 13mm plaster": 0.58,
    "Tiles, airspace, standard aerated block 100mm, cavity, 100mm high performance aerated block, 13mm plaster": 0.49,
    "Tiles, airspace, standard aerated block 100mm, cavity, 125mm high performance aerated block, 13mm plaster": 0.44,
    "Tiles, airspace, standard aerated block 100mm, mineral wool slab in cavity 50mm, 100mm standard aerated block, 13mm plaster": 0.36,
    "Tiles, airspace, standard aerated block 100mm, mineral wool slab in cavity 50mm, 120mm standard aerated block, 13mm plaster": 0.34,
    "Tiles, airspace, standard aerated block 100mm, mineral wool slab in cavity 50mm, 100mm high performance aerated block, 13mm plaster": 0.32,
    "Tiles, airspace, standard aerated block 100mm, mineral wool slab in cavity 50mm, 125mm high performance aerated block, 13mm plaster": 0.3,
    "Tiles, airspace, standard aerated block 125mm, 13mm plaster": 0.53,
    # Shiplap external wall insulation
    "Shiplap boards, airspace, cavity, membrane, plywood 10mm, studding 100mm, with infill insulation 60mm, vapour membrane, plasterboard 12.5mm": 0.44,
    "Shiplap boards, airspace, cavity, membrane, plywood 10mm, studding 100mm, with infill insulation 80mm, vapour membrane, plasterboard 12.5mm": 0.36,
    "Shiplap boards, airspace, standard aerated block 100mm, cavity, standard aerated block 100mm, 13mm plaster": 0.53,
    "Shiplap boards, airspace, standard aerated block 100mm, cavity, standard aerated block 125mm, 13mm plaster": 0.49,
    "Shiplap boards, airspace, standard aerated block 100mm, cavity, 100mm high performance block, 13mm plaster": 0.45,
    "Shiplap boards, airspace, standard aerated block 100mm, cavity, 125mm high performance block, 13mm plaster": 0.41,
    "Shiplap boards, airspace, standard aerated block 100mm, mineral wool slab in cavity 50mm, standard aerated block 100mm, 13mm plaster": 0.34,
    "Shiplap boards, airspace, standard aerated block 100mm, mineral wool slab in cavity 50mm, standard aerated block 125mm, 13mm plaster": 0.32,
    "Shiplap boards, airspace, standard aerated block 100mm, mineral wool slab in cavity 50mm, 125mm high performance block, 13mm plaster": 0.29,
    "Shiplap boards, airspace, standard aerated block 125mm, mineral wool slab in cavity 50mm, 100mm high performance block, 13mm plaster": 0.31,
    # Genericised interventions from building regs
    "Solid Floor Insulation": 0.25,
    "Flat Roof Insulation": 0.35,
    # WINDOWS AND DOORS
    # Doors
    "Glazed wood or PVC-U door Metal Single Glazed": 5.7,
    "Glazed wood or PVC-U door Metal Double Glazed": 3.4,
    "Glazed wood or PVC-U door Metal Double Glazed, low-E glass": 2.8,
    "Glazed wood or PVC-U door Metal Double Glazed, low-E glass, argon filled": 2.6,
    "Glazed wood or PVC-U door Metal Triple Glazed": 2.6,
    "Solid wood door to unheated corridor": 1.4,
    # Windows
    "Single glazed window with Secondary Glazing": 2.4,
    "Metal Single Glazed": 5.7,
    "Metal Double Glazed": 3.4,
    "Metal Double Glazed, low-E glass": 2.8,
    "Metal Double Glazed, low-E glass, argon filled": 2.6,
    "Metal Triple Glazed": 2.6,
    "Metal Triple Glazed, low-E glass": 2.1,
    "Fineo Glazing": 0.7,
}


class StructuralArea(StrEnum):
    """Different parts of a building an intervention could act on."""

    ExteriorWallArea = "exterior_wall_area"
    FloorArea = "floor_area"
    WindowArea = "window_area"
    RoofArea = "roof_area"
    ThermalBridge = "thermal_bridge"


class CostedIntervention(TypedDict):
    """TypedDict representing an intervention with a cost and the associated part of a building it acts on."""

    acts_on: StructuralArea
    cost: float
    u_value: float | None


THIRD_PARTY_INTERVENTIONS = {
    # External Fabric - Wall Interventions
    "Internal Insulation to external solid wall": CostedIntervention(
        acts_on=StructuralArea.ExteriorWallArea, cost=118.38, u_value=0.7
    ),
    "External Insulation to external solid wall (EWI)": CostedIntervention(
        acts_on=StructuralArea.ExteriorWallArea,
        cost=415.68,
        u_value=MATERIAL_U_VALUES[
            "Shiplap boards, airspace, standard aerated block 100mm, mineral wool slab in cavity 50mm, standard aerated block 125mm, 13mm plaster"
        ],
    ),
    "Internal Insulation to external cavity wall": CostedIntervention(
        acts_on=StructuralArea.ExteriorWallArea, cost=118.38, u_value=0.7
    ),
    "External Insulation to external cavity wall": CostedIntervention(
        acts_on=StructuralArea.ExteriorWallArea,
        cost=415.68,
        u_value=MATERIAL_U_VALUES[
            "Shiplap boards, airspace, standard aerated block 100mm, mineral wool slab in cavity 50mm, standard aerated block 125mm, 13mm plaster"
        ],
    ),
    "External Overbuild": CostedIntervention(acts_on=StructuralArea.ExteriorWallArea, cost=884.66, u_value=0.11),
    "Cavity Wall insulation (Full fill)": CostedIntervention(
        acts_on=StructuralArea.ExteriorWallArea,
        cost=33.70,
        u_value=MATERIAL_U_VALUES[
            "Shiplap boards, airspace, standard aerated block 100mm, mineral wool slab in cavity 50mm, standard aerated block 125mm, 13mm plaster"
        ],
    ),
    # External Fabric - Roof Interventions
    "Pitched Roof Insulation (between and over roof structure)": CostedIntervention(
        acts_on=StructuralArea.RoofArea,
        cost=487.42,
        u_value=MATERIAL_U_VALUES[
            "Pitched roof - Slates or tiles, sarking felt, ventilated air space, 300mm insulation between rafters, 9.5mm plasterboard"
        ],
    ),
    "Pitched Roof Insulation (between and under roof structure)": CostedIntervention(
        acts_on=StructuralArea.RoofArea,
        cost=411.50,
        u_value=MATERIAL_U_VALUES[
            "Pitched roof - Slates or tiles, sarking felt, ventilated air space, 300mm insulation between rafters, 9.5mm plasterboard"
        ],
    ),
    "Flat Roof Insulation (Between and over roof structure)": CostedIntervention(
        acts_on=StructuralArea.RoofArea, cost=487.42, u_value=MATERIAL_U_VALUES["Flat Roof Insulation"]
    ),
    "Flat Roof Insulation (Between and under roof structure)": CostedIntervention(
        acts_on=StructuralArea.RoofArea, cost=411.50, u_value=MATERIAL_U_VALUES["Flat Roof Insulation"]
    ),
    "Insulation to ceiling void": CostedIntervention(
        acts_on=StructuralArea.RoofArea,
        cost=150.00,
        u_value=MATERIAL_U_VALUES[
            "Pitched roof - Slates or tiles, sarking felt, ventilated air space, 300mm insulation between rafters, 9.5mm plasterboard"
        ],
    ),
    # External Fabric - Floor Interventions
    "Ground Floor Insulation (Suspended)": CostedIntervention(
        acts_on=StructuralArea.FloorArea,
        cost=170.07,
        u_value=MATERIAL_U_VALUES[
            "Intermediate floors, boarding 19mm, airspace 100mm insulation between joists, 9.5mm plasterboard heat flow downward"
        ],
    ),
    "Ground Floor Insulation (Solid/ ground bearing)": CostedIntervention(
        acts_on=StructuralArea.FloorArea, cost=92.41, u_value=MATERIAL_U_VALUES["Solid Floor Insulation"]
    ),
    # External Fabric - Window and Door Interventions
    "Replacement External Doors": CostedIntervention(
        acts_on=StructuralArea.WindowArea,
        cost=1888.21,
        u_value=MATERIAL_U_VALUES["Glazed wood or PVC-U door Metal Double Glazed, low-E glass"],
    ),
    "Replacement External Windows": CostedIntervention(
        acts_on=StructuralArea.WindowArea, cost=1001.83, u_value=MATERIAL_U_VALUES["Metal Double Glazed"]
    ),
    "Secondary Glazing": CostedIntervention(
        acts_on=StructuralArea.WindowArea, cost=275.37, u_value=MATERIAL_U_VALUES["Metal Double Glazed"]
    ),
    "Fineo Glazing": CostedIntervention(
        acts_on=StructuralArea.WindowArea, cost=586.74, u_value=MATERIAL_U_VALUES["Fineo Glazing"]
    ),
    # Airtightness Interventions
    "Air tightness to external building fabric": CostedIntervention(
        acts_on=StructuralArea.ExteriorWallArea, cost=86.26, u_value=None
    ),
    "Air tightness to external doors and windows": CostedIntervention(
        acts_on=StructuralArea.WindowArea, cost=129.52, u_value=None
    ),
    "Air tightness to external voids and penetrations": CostedIntervention(
        acts_on=StructuralArea.FloorArea, cost=21.59, u_value=None
    ),
    # Heating Interventions (per floor area)
    "Boiler Replacement": CostedIntervention(acts_on=StructuralArea.FloorArea, cost=72.37, u_value=None),
    "Boiler Repair": CostedIntervention(acts_on=StructuralArea.FloorArea, cost=1562.50, u_value=None),
    "Radiator panel Replacement": CostedIntervention(acts_on=StructuralArea.FloorArea, cost=197.90, u_value=None),
    "Radiator Control value replacement": CostedIntervention(acts_on=StructuralArea.FloorArea, cost=72.19, u_value=None),
    "Underfloor heating": CostedIntervention(acts_on=StructuralArea.FloorArea, cost=221.44, u_value=None),
    "Waste water heat recovery": CostedIntervention(acts_on=StructuralArea.FloorArea, cost=946.95, u_value=None),
    "Solar water heating": CostedIntervention(acts_on=StructuralArea.FloorArea, cost=67.85, u_value=None),
    # Ventilation Interventions
    "Air source heat exchanger": CostedIntervention(acts_on=StructuralArea.FloorArea, cost=77.87, u_value=None),
    "Mechanical heating and cooling": CostedIntervention(acts_on=StructuralArea.FloorArea, cost=77.87, u_value=None),
    "Mechanical Ventilation and Heat Recovery": CostedIntervention(acts_on=StructuralArea.FloorArea, cost=117.59, u_value=None),
    "Single room heat recovery ventilators": CostedIntervention(acts_on=StructuralArea.FloorArea, cost=101.33, u_value=None),
    # Energy Interventions
    "Solar Photovoltaics": CostedIntervention(acts_on=StructuralArea.FloorArea, cost=46.88, u_value=None),
    # Lighting Interventions
    "Energy efficient lighting": CostedIntervention(acts_on=StructuralArea.FloorArea, cost=70.25, u_value=None),
    "Proximity Detection": CostedIntervention(acts_on=StructuralArea.FloorArea, cost=64.76, u_value=None),
    # Solar Gain Control
    "External Blinds or Louvers": CostedIntervention(acts_on=StructuralArea.WindowArea, cost=148.70, u_value=None),
    "Increase glazing specification": CostedIntervention(
        acts_on=StructuralArea.WindowArea, cost=78.80, u_value=MATERIAL_U_VALUES["Metal Triple Glazed"]
    ),
    "Internal Blinds and controls": CostedIntervention(acts_on=StructuralArea.WindowArea, cost=148.70, u_value=None),
}

# Generic Interventions
THIRD_PARTY_INTERVENTIONS["loft"] = THIRD_PARTY_INTERVENTIONS["Insulation to ceiling void"]
THIRD_PARTY_INTERVENTIONS["double_glazing"] = THIRD_PARTY_INTERVENTIONS["Replacement External Windows"]
THIRD_PARTY_INTERVENTIONS["cladding"] = THIRD_PARTY_INTERVENTIONS["External Overbuild"]

# Make it case insensitive
THIRD_PARTY_INTERVENTIONS |= {key.lower(): value for key, value in THIRD_PARTY_INTERVENTIONS.items()}
