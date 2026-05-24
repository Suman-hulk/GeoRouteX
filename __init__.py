# -*- coding: utf-8 -*-

"""
GeoRouteX
Advanced Routing Visualizer for QGIS

@author: Suman Saurabh

"""

from .plugin import GeoRouteXPlugin

def classFactory(iface):
    return GeoRouteXPlugin(iface)