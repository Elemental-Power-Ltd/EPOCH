"""
Dynamic thermal model functions.

The dynamic thermal model aims to predict temperature variations and heat losses.
"""

from .network import add_heating_system_to_graph as add_heating_system_to_graph
from .network import add_structure_to_graph as add_structure_to_graph
from .network import initialise_outdoors as initialise_outdoors
