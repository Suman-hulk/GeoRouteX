# -*- coding: utf-8 -*-

"""
GeoRouteX
Advanced Routing Visualizer for QGIS

@author: Suman Saurabh

"""

import os

from PyQt5.QtWidgets import QAction, QSplashScreen
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QTimer

from .dialog import GeoRouteXDialog


# =========================================================
# MAIN PLUGIN CLASS
# =========================================================

class GeoRouteXPlugin:

    # =====================================================
    # INIT
    # =====================================================

    def __init__(self, iface):

        self.iface = iface

        self.action = None

        self.dialog = None

    # =====================================================
    # INIT GUI
    # =====================================================

    def initGui(self):

        # -------------------------------------------------
        # ICON PATH
        # -------------------------------------------------

        icon_path = os.path.join(
            os.path.dirname(__file__),
            "icon.png"
        )

        # -------------------------------------------------
        # ACTION
        # -------------------------------------------------

        self.action = QAction(
            QIcon(icon_path),
            "GeoRouteX",
            self.iface.mainWindow()
        )

        # -------------------------------------------------
        # TOOLTIP
        # -------------------------------------------------

        self.action.setToolTip(
            "GeoRouteX - Advanced Routing Visualizer for QGIS"
        )

        # -------------------------------------------------
        # CONNECT
        # -------------------------------------------------

        self.action.triggered.connect(
            self.run
        )

        # -------------------------------------------------
        # ADD TO MENU
        # -------------------------------------------------

        self.iface.addPluginToMenu(
            "&GeoRouteX",
            self.action
        )

        # -------------------------------------------------
        # ADD TOOLBAR ICON
        # -------------------------------------------------

        self.iface.addToolBarIcon(
            self.action
        )

    # =====================================================
    # UNLOAD
    # =====================================================

    def unload(self):

        self.iface.removePluginMenu(
            "&GeoRouteX",
            self.action
        )

        self.iface.removeToolBarIcon(
            self.action
        )

    # =====================================================
    # RUN
    # =====================================================

    def run(self):

        # -------------------------------------------------
        # SPLASH IMAGE
        # -------------------------------------------------
    
        splash_path = os.path.join(
            os.path.dirname(__file__),
            "splash.png"
        )
    
        pixmap = QPixmap(splash_path)

        # Resize splash image
        pixmap = pixmap.scaled(
            700,   # width
            500,   # height
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        splash = QSplashScreen(
            pixmap,
            Qt.WindowStaysOnTopHint
        )
    
        splash.show()
        screen = self.iface.mainWindow().screen().geometry()

        x = (screen.width() - splash.width()) // 2
        y = (screen.height() - splash.height()) // 2
        
        splash.move(x, y)
        
        splash.showMessage(
            "Initializing GeoRouteX...",
            Qt.AlignBottom | Qt.AlignCenter,
            Qt.white
        )
    
        # -------------------------------------------------
        # OPEN MAIN WINDOW
        # -------------------------------------------------
    
        def open_dialog():
    
            splash.close()
    
            if not self.dialog:
    
                self.dialog = GeoRouteXDialog(
                    self.iface
                )
    
            self.dialog.show()
    
            self.dialog.raise_()
    
            self.dialog.activateWindow()
    
        # -------------------------------------------------
        # TIMER
        # -------------------------------------------------
    
        QTimer.singleShot(
            2000,
            open_dialog
        )