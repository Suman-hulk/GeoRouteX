# -*- coding: utf-8 -*-

"""
GeoRouteX
Advanced Routing Visualizer for QGIS

@author: Suman Saurabh

"""
 

# =============================================================
# dialog.py
# GeoRouteX
# Advanced Routing Visualizer for QGIS
# Full Stable Version
# =============================================================

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QSlider,
    QComboBox,
    QFileDialog,
    QMessageBox
)

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor

from qgis.PyQt.QtCore import QVariant

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsMapLayer,
    QgsWkbTypes,
    QgsPointXY,
    QgsDistanceArea,
    QgsSpatialIndex,
    QgsFeatureRequest,
    QgsGeometry,
    QgsFeature,
    QgsVectorFileWriter,
    QgsField,
    QgsMessageLog,
    Qgis
)

from qgis.gui import (
    QgsVertexMarker,
    QgsRubberBand,
    QgsMapToolEmitPoint
)

import heapq


class GeoRouteXDialog(QWidget):

    # =========================================================
    # INIT
    # =========================================================

    def __init__(self, iface):

        super().__init__()

        self.iface = iface

        self.setWindowTitle(
            "GeoRouteX - Advanced Routing Visualizer for QGIS"
        )

        self.setMinimumWidth(400)

        # =====================================================
        # LAYOUT
        # =====================================================

        layout = QVBoxLayout()

        # =====================================================
        # LAYER SECTION
        # =====================================================

        self.layer_label = QLabel("Select Road Layer")
        layout.addWidget(self.layer_label)

        self.layer_combo = QComboBox()
        layout.addWidget(self.layer_combo)

        self.load_btn = QPushButton("📂 Load Layer From File")
        self.load_btn.clicked.connect(self.load_layer)
        layout.addWidget(self.load_btn)

        self.refresh_btn = QPushButton("🔄 Refresh Layers")
        self.refresh_btn.clicked.connect(self.refresh_layers)
        layout.addWidget(self.refresh_btn)

        # =====================================================
        # LIVE COORDS
        # =====================================================

        self.coord_label = QLabel("Lat: --- | Lon: ---")
        layout.addWidget(self.coord_label)

        # =====================================================
        # INFO PANEL
        # =====================================================

        self.info_label = QLabel(
            "Start: ---\n"
            "End: ---\n"
            "Distance: ---\n"
            "ETA: ---"
        )

        layout.addWidget(self.info_label)

        # =====================================================
        # BUTTONS
        # =====================================================

        self.build_btn = QPushButton("⚙ Build Graph")
        self.build_btn.clicked.connect(self.build_graph)
        layout.addWidget(self.build_btn)

        self.start_btn = QPushButton("▶ Start Routing")
        self.start_btn.clicked.connect(self.activate_tool)
        layout.addWidget(self.start_btn)

        self.export_btn = QPushButton("💾 Export Shortest Path")
        self.export_btn.clicked.connect(self.export_path)
        layout.addWidget(self.export_btn)

        self.clear_btn = QPushButton("🧹 Clear")
        self.clear_btn.clicked.connect(self.clear_all)
        layout.addWidget(self.clear_btn)

        # =====================================================
        # SPEED SLIDER
        # =====================================================

        layout.addWidget(QLabel("Animation Speed"))

        self.slider = QSlider(Qt.Horizontal)

        self.slider.setMinimum(10)
        self.slider.setMaximum(200)
        self.slider.setValue(30)

        layout.addWidget(self.slider)

        self.setLayout(layout)

        # =====================================================
        # STORAGE
        # =====================================================

        self.graph = {}

        self.spatial_index = QgsSpatialIndex()

        self.clicks = []

        self.steps = []

        self.path = []

        self.markers = []

        self.i = 0

        self.live_length = 0

        self.total_eta_min = 0

        self.start_point = None

        self.end_point = None

        # =====================================================
        # DISTANCE CALCULATOR
        # =====================================================

        self.distance_calculator = QgsDistanceArea()

        self.distance_calculator.setEllipsoid("WGS84")

        self.distance_calculator.setSourceCrs(
            self.iface.mapCanvas().mapSettings().destinationCrs(),
            QgsProject.instance().transformContext()
        )

        # =====================================================
        # TIMER
        # =====================================================

        self.timer = QTimer()

        self.timer.timeout.connect(self.animate)

        # =====================================================
        # MAP TOOL
        # =====================================================

        self.tool = QgsMapToolEmitPoint(
            self.iface.mapCanvas()
        )

        self.tool.canvasClicked.connect(
            self.handle_click
        )

        # =====================================================
        # LIVE COORDS
        # =====================================================

        self.iface.mapCanvas().xyCoordinates.connect(
            self.update_coords
        )

        # =====================================================
        # RUBBER BAND
        # =====================================================

        self.rubber = QgsRubberBand(
            self.iface.mapCanvas(),
            QgsWkbTypes.LineGeometry
        )

        self.rubber.setColor(QColor(0, 255, 0))

        self.rubber.setWidth(4)

        # =====================================================
        # INITIALIZE
        # =====================================================

        self.refresh_layers()

    # =========================================================
    # LOAD LAYER
    # =========================================================
    
    def load_layer(self):
    
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select GIS Layer",
            "",
            (
                "GIS Files (*.shp *.gpkg *.geojson *.json "
                "*.kml *.sqlite *.gdb);;"
                "All Files (*)"
            )
        )
    
        if not file_path:
            return
    
        # =====================================================
        # LAYER NAME
        # =====================================================
    
        layer_name = file_path.split("/")[-1]
    
        # =====================================================
        # LOAD VECTOR LAYER
        # =====================================================
    
        layer = QgsVectorLayer(
            file_path,
            layer_name,
            "ogr"
        )
    
        # =====================================================
        # VALIDATION
        # =====================================================
    
        if not layer.isValid():
    
            QMessageBox.warning(
                self,
                "Error",
                "Failed to load layer."
            )
    
            return
    
        # =====================================================
        # GEOMETRY CHECK
        # =====================================================
    
        if layer.geometryType() != QgsWkbTypes.LineGeometry:
    
            QMessageBox.warning(
                self,
                "Error",
                "Please load a LINE layer."
            )
    
            return
    
        # =====================================================
        # ADD TO PROJECT
        # =====================================================
    
        QgsProject.instance().addMapLayer(layer)
    
        # =====================================================
        # REFRESH COMBO
        # =====================================================
    
        self.refresh_layers()
    
        # =====================================================
        # AUTO SELECT NEW LAYER
        # =====================================================
    
        index = self.layer_combo.findText(layer.name())
    
        if index >= 0:
            self.layer_combo.setCurrentIndex(index)
    
        # =====================================================
        # STATUS
        # =====================================================
    
        self.layer_label.setText(
            f"✅ Loaded: {layer.name()}"
        )

    # =========================================================
    # REFRESH LAYERS
    # =========================================================

    def refresh_layers(self):

        self.layer_combo.clear()

        for layer in QgsProject.instance().mapLayers().values():

            if (
                layer.type() == QgsMapLayer.VectorLayer
                and
                layer.geometryType() == QgsWkbTypes.LineGeometry
            ):

                self.layer_combo.addItem(
                    layer.name(),
                    layer
                )

    # =========================================================
    # GET LAYER
    # =========================================================

    def get_selected_layer(self):

        return self.layer_combo.currentData()

    # =========================================================
    # UPDATE COORDS
    # =========================================================

    def update_coords(self, point):

        self.coord_label.setText(
            f"Lat: {point.y():.6f} | "
            f"Lon: {point.x():.6f}"
        )

    # =========================================================
    # AUTO SPEED FIELD
    # =========================================================

    def generate_speed_field(self, layer):

        provider = layer.dataProvider()

        provider.addAttributes([
            QgsField("speed", QVariant.Double)
        ])

        layer.updateFields()

        speed_map = {
            "motorway": 100,
            "trunk": 90,
            "primary": 70,
            "secondary": 60,
            "tertiary": 50,
            "residential": 30,
            "service": 20
        }

        field_names = [f.name() for f in layer.fields()]

        if "highway" not in field_names:

            QMessageBox.warning(
                self,
                "Error",
                "No highway field found."
            )

            return False

        layer.startEditing()

        speed_idx = layer.fields().indexOf("speed")

        for feature in layer.getFeatures():

            highway = feature["highway"]

            if highway is None:
                highway = ""

            highway = str(highway).lower()

            speed = speed_map.get(highway, 40)

            layer.changeAttributeValue(
                feature.id(),
                speed_idx,
                speed
            )

        layer.commitChanges()

        QMessageBox.information(
            self,
            "Success",
            "Speed field generated."
        )

        return True

    # =========================================================
    # BUILD GRAPH
    # =========================================================

    def build_graph(self):

        self.graph.clear()

        self.spatial_index = QgsSpatialIndex()

        layer = self.get_selected_layer()

        if not layer:

            QMessageBox.warning(
                self,
                "Error",
                "Please select a layer."
            )

            return

        field_names = [f.name() for f in layer.fields()]

        # =====================================================
        # AUTO SPEED FIELD
        # =====================================================

        if "speed" not in field_names:

            reply = QMessageBox.question(
                self,
                "Generate Speed",
                "No speed field found.\n\n"
                "Generate automatically from "
                "OSM highway types?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:

                success = self.generate_speed_field(layer)

                if not success:
                    return

            else:

                QMessageBox.warning(
                    self,
                    "Error",
                    "Speed field required."
                )

                return

        # =====================================================
        # BUILD GRAPH
        # =====================================================

        for f in layer.getFeatures():

            self.spatial_index.addFeature(f)

            geom = f.geometry()

            if not geom:
                continue

            if geom.isEmpty():
                continue

            # =================================================
            # SPEED
            # =================================================

            try:
                speed = float(f["speed"])

            except:
                speed = 40

            if speed <= 0:
                speed = 1

            speed_mps = speed * 1000 / 3600

            # =================================================
            # GET LINES
            # =================================================

            lines = (
                geom.asMultiPolyline()
                if geom.isMultipart()
                else [geom.asPolyline()]
            )

            for line in lines:

                if len(line) < 2:
                    continue

                for i in range(len(line) - 1):

                    p1 = line[i]

                    p2 = line[i + 1]

                    start = (p1.x(), p1.y())

                    end = (p2.x(), p2.y())

                    distance = (
                        self.distance_calculator.measureLine(
                            QgsPointXY(p1),
                            QgsPointXY(p2)
                        )
                    )

                    travel_time = distance / speed_mps

                    self.graph.setdefault(
                        start,
                        []
                    ).append(
                        (end, distance, travel_time)
                    )

                    self.graph.setdefault(
                        end,
                        []
                    ).append(
                        (start, distance, travel_time)
                    )

        if not self.graph:

            QMessageBox.warning(
                self,
                "Error",
                "Graph is empty."
            )

            return

        QgsMessageLog.logMessage(
            f"Graph built: {len(self.graph)} nodes",
            "GeoRouteX",
            Qgis.Info
        )

        self.layer_label.setText(
            f"✅ Graph built: {len(self.graph)} nodes"
        )

    # =========================================================
    # ACTIVATE TOOL
    # =========================================================

    def activate_tool(self):

        if not self.graph:

            QMessageBox.warning(
                self,
                "Error",
                "Build graph first."
            )

            return

        self.iface.mapCanvas().setMapTool(
            self.tool
        )

        self.layer_label.setText(
            "🖱 Click start and end points"
        )

    # =========================================================
    # HANDLE CLICK
    # =========================================================

    def handle_click(self, point, button):

        if not self.graph:
            return

        layer = self.get_selected_layer()

        if not layer:
            return

        click_point = QgsPointXY(
            point.x(),
            point.y()
        )

        # =====================================================
        # NEAREST FEATURE
        # =====================================================

        nearest_ids = self.spatial_index.nearestNeighbor(
            click_point,
            1
        )

        if not nearest_ids:
            return

        feature_id = nearest_ids[0]

        request = QgsFeatureRequest(feature_id)

        feature = next(layer.getFeatures(request))

        geom = feature.geometry()

        # =====================================================
        # SNAP TO ROAD SEGMENT
        # =====================================================

        result = geom.closestSegmentWithContext(
            click_point
        )

        snapped_point = result[1]

        # =====================================================
        # FIND NEAREST NODE
        # =====================================================

        node = min(
            self.graph.keys(),
            key=lambda n:
            (n[0] - snapped_point.x())**2 +
            (n[1] - snapped_point.y())**2
        )

        self.clicks.append(node)

        # =====================================================
        # VISUAL MARKER
        # =====================================================

        marker = QgsVertexMarker(
            self.iface.mapCanvas()
        )

        marker.setCenter(
            QgsPointXY(node[0], node[1])
        )

        marker.setColor(QColor(0, 0, 255))

        marker.setIconSize(8)

        self.markers.append(marker)

        if len(self.clicks) == 2:

            self.iface.mapCanvas().unsetMapTool(
                self.tool
            )

            self.start_animation()

    # =========================================================
    # DIJKSTRA
    # =========================================================

    def dijkstra(self, start, end):

        queue = [(0, start)]

        visited = set()

        parents = {}

        steps = []

        cost_so_far = {
            start: 0
        }

        while queue:

            current_cost, node = heapq.heappop(
                queue
            )

            if node in visited:
                continue

            visited.add(node)

            steps.append(node)

            if node == end:
                break

            for neigh, dist, travel_time in self.graph[node]:

                new_cost = current_cost + travel_time

                if (
                    neigh not in cost_so_far
                    or
                    new_cost < cost_so_far[neigh]
                ):

                    cost_so_far[neigh] = new_cost

                    parents[neigh] = node

                    heapq.heappush(
                        queue,
                        (new_cost, neigh)
                    )

        return steps, parents, cost_so_far

    # =========================================================
    # GET PATH
    # =========================================================

    def get_path(self, parents, end):

        if end not in parents:
            return []

        path = [end]

        while end in parents:

            end = parents[end]

            path.append(end)

        return path[::-1]

    # =========================================================
    # START ANIMATION
    # =========================================================

    def start_animation(self):

        if len(self.clicks) < 2:
            return

        start, end = self.clicks

        self.start_point = start

        self.end_point = end

        self.live_length = 0

        self.clear_visuals()

        self.steps, parents, costs = self.dijkstra(
            start,
            end
        )

        self.path = self.get_path(
            parents,
            end
        )

        if not self.path:

            QMessageBox.warning(
                self,
                "Routing Error",
                "No valid route found."
            )

            return

        total_time_sec = costs.get(end, 0)

        self.total_eta_min = total_time_sec / 60

        self.info_label.setText(
            f"Start: ({start[1]:.5f}, {start[0]:.5f})\n"
            f"End: ({end[1]:.5f}, {end[0]:.5f})\n"
            f"Distance: 0.00 m\n"
            f"ETA: {self.total_eta_min:.2f} min"
        )

        self.clicks.clear()

        self.i = 0

        self.timer.start(
            self.slider.value()
        )

    # =========================================================
    # ANIMATE
    # =========================================================

    def animate(self):

        if self.i < len(self.steps):

            pt = self.steps[self.i]

            marker = QgsVertexMarker(
                self.iface.mapCanvas()
            )

            marker.setCenter(
                QgsPointXY(pt[0], pt[1])
            )

            marker.setColor(
                QColor(255, 0, 0)
            )

            marker.setIconSize(4)

            self.markers.append(marker)

        elif self.i - len(self.steps) < len(self.path):

            idx = self.i - len(self.steps)

            p = self.path[idx]

            self.rubber.addPoint(
                QgsPointXY(p[0], p[1])
            )

            if idx > 0:

                prev = self.path[idx - 1]

                p1 = QgsPointXY(
                    prev[0],
                    prev[1]
                )

                p2 = QgsPointXY(
                    p[0],
                    p[1]
                )

                segment_length = (
                    self.distance_calculator.measureLine(
                        p1,
                        p2
                    )
                )

                self.live_length += segment_length

                self.info_label.setText(
                    f"Start: ({self.start_point[1]:.5f}, {self.start_point[0]:.5f})\n"
                    f"End: ({self.end_point[1]:.5f}, {self.end_point[0]:.5f})\n"
                    f"Distance: {self.live_length:.2f} m\n"
                    f"ETA: {self.total_eta_min:.2f} min"
                )

        else:

            self.timer.stop()

            self.layer_label.setText(
                "✅ Fastest route complete"
            )

        self.i += 1

    # =========================================================
    # EXPORT PATH
    # =========================================================

    def export_path(self):

        if not self.path:

            QMessageBox.warning(
                self,
                "Export Error",
                "No path available."
            )

            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Path",
            "",
            "Shapefile (*.shp)"
        )

        if not file_path:
            return

        layer = QgsVectorLayer(
            "LineString?crs=EPSG:4326",
            "Shortest Path",
            "memory"
        )

        provider = layer.dataProvider()

        provider.addAttributes([
            QgsField("distance", QVariant.Double),
            QgsField("eta_min", QVariant.Double)
        ])

        layer.updateFields()

        feature = QgsFeature()

        points = [
            QgsPointXY(p[0], p[1])
            for p in self.path
        ]

        geometry = QgsGeometry.fromPolylineXY(
            points
        )

        feature.setGeometry(geometry)

        feature.setAttributes([
            round(self.live_length, 2),
            round(self.total_eta_min, 2)
        ])

        provider.addFeature(feature)

        layer.updateExtents()

        QgsVectorFileWriter.writeAsVectorFormat(
            layer,
            file_path,
            "UTF-8",
            layer.crs(),
            "ESRI Shapefile"
        )

        self.layer_label.setText(
            "✅ Path exported"
        )

    # =========================================================
    # CLEAR VISUALS
    # =========================================================

    def clear_visuals(self):

        self.timer.stop()

        self.steps.clear()

        self.path.clear()

        self.i = 0

        for marker in self.markers:

            self.iface.mapCanvas().scene().removeItem(
                marker
            )

        self.markers.clear()

        self.rubber.reset(
            QgsWkbTypes.LineGeometry
        )

    # =========================================================
    # CLEAR ALL
    # =========================================================

    def clear_all(self):

        self.clear_visuals()

        self.clicks.clear()

        self.live_length = 0

        self.total_eta_min = 0

        self.info_label.setText(
            "Start: ---\n"
            "End: ---\n"
            "Distance: ---\n"
            "ETA: ---"
        )

        self.layer_label.setText(
            "Cleared"
        )