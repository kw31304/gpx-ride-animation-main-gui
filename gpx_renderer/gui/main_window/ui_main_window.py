# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox,
    QFrame, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMenu,
    QMenuBar, QPushButton, QSizePolicy, QSpacerItem,
    QSpinBox, QTabWidget, QToolBar, QVBoxLayout,
    QWidget)

from gpx_renderer.gui.widgets.py_circular_progress import PyCircularProgress

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(880, 600)
        MainWindow.setMinimumSize(QSize(880, 0))
        MainWindow.setMaximumSize(QSize(16777215, 16777215))
        self.action_open_gpx = QAction(MainWindow)
        self.action_open_gpx.setObjectName(u"action_open_gpx")
        self.action_save_output = QAction(MainWindow)
        self.action_save_output.setObjectName(u"action_save_output")
        self.action_select_media = QAction(MainWindow)
        self.action_select_media.setObjectName(u"action_select_media")
        self.action_media_dialog = QAction(MainWindow)
        self.action_media_dialog.setObjectName(u"action_media_dialog")
        self.action_open_log_folder = QAction(MainWindow)
        self.action_open_log_folder.setObjectName(u"action_open_log_folder")
        self.action_exit = QAction(MainWindow)
        self.action_exit.setObjectName(u"action_exit")
        self.action_benchmark = QAction(MainWindow)
        self.action_benchmark.setObjectName(u"action_benchmark")
        self.action_apply_benchmark = QAction(MainWindow)
        self.action_apply_benchmark.setObjectName(u"action_apply_benchmark")
        self.action_apply_benchmark.setEnabled(False)
        self.action_clear_cache = QAction(MainWindow)
        self.action_clear_cache.setObjectName(u"action_clear_cache")
        self.action_refresh_distance = QAction(MainWindow)
        self.action_refresh_distance.setObjectName(u"action_refresh_distance")
        self.action_toggle_toolbar = QAction(MainWindow)
        self.action_toggle_toolbar.setObjectName(u"action_toggle_toolbar")
        self.action_toggle_toolbar.setCheckable(True)
        self.action_toggle_toolbar.setChecked(True)
        self.action_toggle_advanced = QAction(MainWindow)
        self.action_toggle_advanced.setObjectName(u"action_toggle_advanced")
        self.action_toggle_advanced.setCheckable(True)
        self.action_toggle_summary = QAction(MainWindow)
        self.action_toggle_summary.setObjectName(u"action_toggle_summary")
        self.action_toggle_summary.setCheckable(True)
        self.action_toggle_summary.setChecked(True)
        self.action_toggle_workers = QAction(MainWindow)
        self.action_toggle_workers.setObjectName(u"action_toggle_workers")
        self.action_toggle_workers.setCheckable(True)
        self.action_toggle_workers.setChecked(True)
        self.action_profile_fast = QAction(MainWindow)
        self.action_profile_fast.setObjectName(u"action_profile_fast")
        self.action_profile_balanced = QAction(MainWindow)
        self.action_profile_balanced.setObjectName(u"action_profile_balanced")
        self.action_profile_quality = QAction(MainWindow)
        self.action_profile_quality.setObjectName(u"action_profile_quality")
        self.action_show_speed = QAction(MainWindow)
        self.action_show_speed.setObjectName(u"action_show_speed")
        self.action_show_speed.setCheckable(True)
        self.action_show_speed.setChecked(True)
        self.action_show_minimap = QAction(MainWindow)
        self.action_show_minimap.setObjectName(u"action_show_minimap")
        self.action_show_minimap.setCheckable(True)
        self.action_show_minimap.setChecked(True)
        self.action_show_elevation = QAction(MainWindow)
        self.action_show_elevation.setObjectName(u"action_show_elevation")
        self.action_show_elevation.setCheckable(True)
        self.action_show_elevation.setChecked(True)
        self.action_dynamic_speed_zoom = QAction(MainWindow)
        self.action_dynamic_speed_zoom.setObjectName(u"action_dynamic_speed_zoom")
        self.action_dynamic_speed_zoom.setCheckable(True)
        self.action_dynamic_speed_zoom.setChecked(True)
        self.action_real_speed = QAction(MainWindow)
        self.action_real_speed.setObjectName(u"action_real_speed")
        self.action_real_speed.setCheckable(True)
        self.action_basemap = QAction(MainWindow)
        self.action_basemap.setObjectName(u"action_basemap")
        self.action_basemap.setCheckable(True)
        self.action_basemap.setChecked(True)
        self.action_parallel = QAction(MainWindow)
        self.action_parallel.setObjectName(u"action_parallel")
        self.action_parallel.setCheckable(True)
        self.action_parallel.setChecked(True)
        self.action_enable_media = QAction(MainWindow)
        self.action_enable_media.setObjectName(u"action_enable_media")
        self.action_enable_media.setCheckable(True)
        self.action_enable_media.setChecked(True)
        self.action_preview = QAction(MainWindow)
        self.action_preview.setObjectName(u"action_preview")
        self.action_preview.setCheckable(True)
        self.action_cache_session = QAction(MainWindow)
        self.action_cache_session.setObjectName(u"action_cache_session")
        self.action_cache_session.setCheckable(True)
        self.action_cache_persistent = QAction(MainWindow)
        self.action_cache_persistent.setObjectName(u"action_cache_persistent")
        self.action_cache_persistent.setCheckable(True)
        self.action_start_render = QAction(MainWindow)
        self.action_start_render.setObjectName(u"action_start_render")
        self.action_stop_render = QAction(MainWindow)
        self.action_stop_render.setObjectName(u"action_stop_render")
        self.action_stop_render.setEnabled(False)
        self.action_help_shortcuts = QAction(MainWindow)
        self.action_help_shortcuts.setObjectName(u"action_help_shortcuts")
        self.action_about = QAction(MainWindow)
        self.action_about.setObjectName(u"action_about")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_main = QVBoxLayout(self.centralwidget)
        self.verticalLayout_main.setSpacing(4)
        self.verticalLayout_main.setObjectName(u"verticalLayout_main")
        self.verticalLayout_main.setContentsMargins(6, 6, 6, 6)
        self.groupBox_files = QGroupBox(self.centralwidget)
        self.groupBox_files.setObjectName(u"groupBox_files")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_files.sizePolicy().hasHeightForWidth())
        self.groupBox_files.setSizePolicy(sizePolicy)
        self.groupBox_files.setMinimumSize(QSize(0, 0))
        self.gridLayout_files = QGridLayout(self.groupBox_files)
        self.gridLayout_files.setObjectName(u"gridLayout_files")
        self.lbl_gpx = QLabel(self.groupBox_files)
        self.lbl_gpx.setObjectName(u"lbl_gpx")

        self.gridLayout_files.addWidget(self.lbl_gpx, 0, 0, 1, 1)

        self.lineEdit_gpx = QLineEdit(self.groupBox_files)
        self.lineEdit_gpx.setObjectName(u"lineEdit_gpx")

        self.gridLayout_files.addWidget(self.lineEdit_gpx, 0, 1, 1, 1)

        self.btn_browse_gpx = QPushButton(self.groupBox_files)
        self.btn_browse_gpx.setObjectName(u"btn_browse_gpx")

        self.gridLayout_files.addWidget(self.btn_browse_gpx, 0, 2, 1, 1)

        self.lbl_output = QLabel(self.groupBox_files)
        self.lbl_output.setObjectName(u"lbl_output")

        self.gridLayout_files.addWidget(self.lbl_output, 1, 0, 1, 1)

        self.lineEdit_output = QLineEdit(self.groupBox_files)
        self.lineEdit_output.setObjectName(u"lineEdit_output")

        self.gridLayout_files.addWidget(self.lineEdit_output, 1, 1, 1, 1)

        self.btn_browse_output = QPushButton(self.groupBox_files)
        self.btn_browse_output.setObjectName(u"btn_browse_output")

        self.gridLayout_files.addWidget(self.btn_browse_output, 1, 2, 1, 1)

        self.lbl_media = QLabel(self.groupBox_files)
        self.lbl_media.setObjectName(u"lbl_media")

        self.gridLayout_files.addWidget(self.lbl_media, 2, 0, 1, 1)

        self.lineEdit_media = QLineEdit(self.groupBox_files)
        self.lineEdit_media.setObjectName(u"lineEdit_media")

        self.gridLayout_files.addWidget(self.lineEdit_media, 2, 1, 1, 1)

        self.horizontalLayout_media = QHBoxLayout()
        self.horizontalLayout_media.setObjectName(u"horizontalLayout_media")
        self.btn_browse_media = QPushButton(self.groupBox_files)
        self.btn_browse_media.setObjectName(u"btn_browse_media")

        self.horizontalLayout_media.addWidget(self.btn_browse_media)

        self.btn_media_dialog = QPushButton(self.groupBox_files)
        self.btn_media_dialog.setObjectName(u"btn_media_dialog")

        self.horizontalLayout_media.addWidget(self.btn_media_dialog)


        self.gridLayout_files.addLayout(self.horizontalLayout_media, 2, 2, 1, 1)


        self.verticalLayout_main.addWidget(self.groupBox_files)

        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setMinimumSize(QSize(0, 0))
        self.tab_general = QWidget()
        self.tab_general.setObjectName(u"tab_general")
        self.verticalLayout_tab_general = QVBoxLayout(self.tab_general)
        self.verticalLayout_tab_general.setSpacing(4)
        self.verticalLayout_tab_general.setObjectName(u"verticalLayout_tab_general")
        self.verticalLayout_tab_general.setContentsMargins(4, 4, 4, 4)
        self.groupBox_settings_2 = QGroupBox(self.tab_general)
        self.groupBox_settings_2.setObjectName(u"groupBox_settings_2")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.groupBox_settings_2.sizePolicy().hasHeightForWidth())
        self.groupBox_settings_2.setSizePolicy(sizePolicy1)
        self.groupBox_settings_2.setMinimumSize(QSize(0, 0))
        self.gridLayout = QGridLayout(self.groupBox_settings_2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.chk_parallel_2 = QCheckBox(self.groupBox_settings_2)
        self.chk_parallel_2.setObjectName(u"chk_parallel_2")

        self.gridLayout.addWidget(self.chk_parallel_2, 1, 1, 1, 1)

        self.chk_real_speed_2 = QCheckBox(self.groupBox_settings_2)
        self.chk_real_speed_2.setObjectName(u"chk_real_speed_2")

        self.gridLayout.addWidget(self.chk_real_speed_2, 4, 1, 1, 1)

        self.chk_enable_media_2 = QCheckBox(self.groupBox_settings_2)
        self.chk_enable_media_2.setObjectName(u"chk_enable_media_2")

        self.gridLayout.addWidget(self.chk_enable_media_2, 3, 1, 1, 1)

        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.lbl_map_style_2 = QLabel(self.groupBox_settings_2)
        self.lbl_map_style_2.setObjectName(u"lbl_map_style_2")

        self.horizontalLayout_11.addWidget(self.lbl_map_style_2)

        self.combo_map_style_2 = QComboBox(self.groupBox_settings_2)
        self.combo_map_style_2.setObjectName(u"combo_map_style_2")

        self.horizontalLayout_11.addWidget(self.combo_map_style_2)


        self.gridLayout.addLayout(self.horizontalLayout_11, 2, 0, 1, 1)

        self.horizontalLayout_panels = QHBoxLayout()
        self.horizontalLayout_panels.setObjectName(u"horizontalLayout_panels")
        self.lbl_panels = QLabel(self.groupBox_settings_2)
        self.lbl_panels.setObjectName(u"lbl_panels")

        self.horizontalLayout_panels.addWidget(self.lbl_panels)

        self.chk_show_speed = QCheckBox(self.groupBox_settings_2)
        self.chk_show_speed.setObjectName(u"chk_show_speed")
        self.chk_show_speed.setChecked(True)

        self.horizontalLayout_panels.addWidget(self.chk_show_speed)

        self.chk_show_minimap = QCheckBox(self.groupBox_settings_2)
        self.chk_show_minimap.setObjectName(u"chk_show_minimap")
        self.chk_show_minimap.setChecked(True)

        self.horizontalLayout_panels.addWidget(self.chk_show_minimap)

        self.chk_show_elevation = QCheckBox(self.groupBox_settings_2)
        self.chk_show_elevation.setObjectName(u"chk_show_elevation")
        self.chk_show_elevation.setChecked(True)

        self.horizontalLayout_panels.addWidget(self.chk_show_elevation)


        self.gridLayout.addLayout(self.horizontalLayout_panels, 6, 0, 1, 1)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.lbl_camera_mode_2 = QLabel(self.groupBox_settings_2)
        self.lbl_camera_mode_2.setObjectName(u"lbl_camera_mode_2")

        self.horizontalLayout_10.addWidget(self.lbl_camera_mode_2)

        self.combo_camera_mode_2 = QComboBox(self.groupBox_settings_2)
        self.combo_camera_mode_2.setObjectName(u"combo_camera_mode_2")

        self.horizontalLayout_10.addWidget(self.combo_camera_mode_2)


        self.gridLayout.addLayout(self.horizontalLayout_10, 3, 0, 1, 1)

        self.chk_dynamic_speed_zoom = QCheckBox(self.groupBox_settings_2)
        self.chk_dynamic_speed_zoom.setObjectName(u"chk_dynamic_speed_zoom")
        self.chk_dynamic_speed_zoom.setChecked(True)

        self.gridLayout.addWidget(self.chk_dynamic_speed_zoom, 5, 1, 1, 1)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.lbl_resolution_2 = QLabel(self.groupBox_settings_2)
        self.lbl_resolution_2.setObjectName(u"lbl_resolution_2")

        self.horizontalLayout_7.addWidget(self.lbl_resolution_2)

        self.combo_resolution_2 = QComboBox(self.groupBox_settings_2)
        self.combo_resolution_2.setObjectName(u"combo_resolution_2")

        self.horizontalLayout_7.addWidget(self.combo_resolution_2)


        self.gridLayout.addLayout(self.horizontalLayout_7, 4, 0, 1, 1)

        self.chk_basemap_2 = QCheckBox(self.groupBox_settings_2)
        self.chk_basemap_2.setObjectName(u"chk_basemap_2")

        self.gridLayout.addWidget(self.chk_basemap_2, 2, 1, 1, 1)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.lbl_profile_2 = QLabel(self.groupBox_settings_2)
        self.lbl_profile_2.setObjectName(u"lbl_profile_2")

        self.horizontalLayout_9.addWidget(self.lbl_profile_2)

        self.combo_profile_2 = QComboBox(self.groupBox_settings_2)
        self.combo_profile_2.setObjectName(u"combo_profile_2")

        self.horizontalLayout_9.addWidget(self.combo_profile_2)


        self.gridLayout.addLayout(self.horizontalLayout_9, 1, 0, 1, 1)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.lbl_track_color_2 = QLabel(self.groupBox_settings_2)
        self.lbl_track_color_2.setObjectName(u"lbl_track_color_2")

        self.horizontalLayout_8.addWidget(self.lbl_track_color_2)

        self.combo_track_color_2 = QComboBox(self.groupBox_settings_2)
        self.combo_track_color_2.setObjectName(u"combo_track_color_2")

        self.horizontalLayout_8.addWidget(self.combo_track_color_2)


        self.gridLayout.addLayout(self.horizontalLayout_8, 5, 0, 1, 1)

        self.groupBox_summary = QGroupBox(self.groupBox_settings_2)
        self.groupBox_summary.setObjectName(u"groupBox_summary")
        self.gridLayout_summary = QGridLayout(self.groupBox_summary)
        self.gridLayout_summary.setObjectName(u"gridLayout_summary")
        self.label_cfg_map = QLabel(self.groupBox_summary)
        self.label_cfg_map.setObjectName(u"label_cfg_map")

        self.gridLayout_summary.addWidget(self.label_cfg_map, 1, 0, 1, 1)

        self.label_cfg_enc = QLabel(self.groupBox_summary)
        self.label_cfg_enc.setObjectName(u"label_cfg_enc")

        self.gridLayout_summary.addWidget(self.label_cfg_enc, 1, 1, 1, 1)

        self.label_cfg_res = QLabel(self.groupBox_summary)
        self.label_cfg_res.setObjectName(u"label_cfg_res")

        self.gridLayout_summary.addWidget(self.label_cfg_res, 0, 0, 1, 1)

        self.label_cfg_perf = QLabel(self.groupBox_summary)
        self.label_cfg_perf.setObjectName(u"label_cfg_perf")

        self.gridLayout_summary.addWidget(self.label_cfg_perf, 0, 1, 1, 1)


        self.gridLayout.addWidget(self.groupBox_summary, 0, 0, 1, 2)


        self.verticalLayout_tab_general.addWidget(self.groupBox_settings_2)

        self.tabWidget.addTab(self.tab_general, "")
        self.tab_advanced = QWidget()
        self.tab_advanced.setObjectName(u"tab_advanced")
        self.verticalLayout_tab_advanced = QVBoxLayout(self.tab_advanced)
        self.verticalLayout_tab_advanced.setSpacing(4)
        self.verticalLayout_tab_advanced.setObjectName(u"verticalLayout_tab_advanced")
        self.verticalLayout_tab_advanced.setContentsMargins(4, 4, 4, 4)
        self.groupBox = QGroupBox(self.tab_advanced)
        self.groupBox.setObjectName(u"groupBox")
        sizePolicy1.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy1)
        self.groupBox.setMinimumSize(QSize(0, 0))
        self.gridLayout_3 = QGridLayout(self.groupBox)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.lbl_custom_res = QLabel(self.groupBox)
        self.lbl_custom_res.setObjectName(u"lbl_custom_res")

        self.horizontalLayout_12.addWidget(self.lbl_custom_res)

        self.horizontalLayout_custom_res = QHBoxLayout()
        self.horizontalLayout_custom_res.setObjectName(u"horizontalLayout_custom_res")
        self.spin_width = QSpinBox(self.groupBox)
        self.spin_width.setObjectName(u"spin_width")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.spin_width.sizePolicy().hasHeightForWidth())
        self.spin_width.setSizePolicy(sizePolicy2)
        self.spin_width.setValue(99)

        self.horizontalLayout_custom_res.addWidget(self.spin_width)

        self.lbl_x = QLabel(self.groupBox)
        self.lbl_x.setObjectName(u"lbl_x")

        self.horizontalLayout_custom_res.addWidget(self.lbl_x)

        self.spin_height = QSpinBox(self.groupBox)
        self.spin_height.setObjectName(u"spin_height")
        sizePolicy2.setHeightForWidth(self.spin_height.sizePolicy().hasHeightForWidth())
        self.spin_height.setSizePolicy(sizePolicy2)
        self.spin_height.setValue(99)

        self.horizontalLayout_custom_res.addWidget(self.spin_height)


        self.horizontalLayout_12.addLayout(self.horizontalLayout_custom_res)


        self.verticalLayout.addLayout(self.horizontalLayout_12)

        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.lbl_view_margin = QLabel(self.groupBox)
        self.lbl_view_margin.setObjectName(u"lbl_view_margin")

        self.horizontalLayout_13.addWidget(self.lbl_view_margin)

        self.lineEdit_view_margin = QLineEdit(self.groupBox)
        self.lineEdit_view_margin.setObjectName(u"lineEdit_view_margin")

        self.horizontalLayout_13.addWidget(self.lineEdit_view_margin)


        self.verticalLayout.addLayout(self.horizontalLayout_13)

        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.lbl_local_zoom = QLabel(self.groupBox)
        self.lbl_local_zoom.setObjectName(u"lbl_local_zoom")

        self.horizontalLayout_14.addWidget(self.lbl_local_zoom)

        self.combo_local_zoom = QComboBox(self.groupBox)
        self.combo_local_zoom.setObjectName(u"combo_local_zoom")
        sizePolicy2.setHeightForWidth(self.combo_local_zoom.sizePolicy().hasHeightForWidth())
        self.combo_local_zoom.setSizePolicy(sizePolicy2)

        self.horizontalLayout_14.addWidget(self.combo_local_zoom)


        self.verticalLayout.addLayout(self.horizontalLayout_14)

        self.horizontalLayout_15 = QHBoxLayout()
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.lbl_preset = QLabel(self.groupBox)
        self.lbl_preset.setObjectName(u"lbl_preset")

        self.horizontalLayout_15.addWidget(self.lbl_preset)

        self.combo_preset = QComboBox(self.groupBox)
        self.combo_preset.setObjectName(u"combo_preset")
        sizePolicy2.setHeightForWidth(self.combo_preset.sizePolicy().hasHeightForWidth())
        self.combo_preset.setSizePolicy(sizePolicy2)

        self.horizontalLayout_15.addWidget(self.combo_preset)


        self.verticalLayout.addLayout(self.horizontalLayout_15)


        self.gridLayout_3.addLayout(self.verticalLayout, 0, 0, 1, 1)

        self.line_2 = QFrame(self.groupBox)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.VLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout_3.addWidget(self.line_2, 0, 1, 1, 1)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout_16 = QHBoxLayout()
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.lbl_fps = QLabel(self.groupBox)
        self.lbl_fps.setObjectName(u"lbl_fps")

        self.horizontalLayout_16.addWidget(self.lbl_fps)

        self.spin_fps = QSpinBox(self.groupBox)
        self.spin_fps.setObjectName(u"spin_fps")
        sizePolicy2.setHeightForWidth(self.spin_fps.sizePolicy().hasHeightForWidth())
        self.spin_fps.setSizePolicy(sizePolicy2)
        self.spin_fps.setValue(60)

        self.horizontalLayout_16.addWidget(self.spin_fps)


        self.verticalLayout_2.addLayout(self.horizontalLayout_16)

        self.horizontalLayout_17 = QHBoxLayout()
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.lbl_zoomout = QLabel(self.groupBox)
        self.lbl_zoomout.setObjectName(u"lbl_zoomout")

        self.horizontalLayout_17.addWidget(self.lbl_zoomout)

        self.lineEdit_zoomout = QLineEdit(self.groupBox)
        self.lineEdit_zoomout.setObjectName(u"lineEdit_zoomout")

        self.horizontalLayout_17.addWidget(self.lineEdit_zoomout)


        self.verticalLayout_2.addLayout(self.horizontalLayout_17)

        self.horizontalLayout_18 = QHBoxLayout()
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.lbl_end_hold = QLabel(self.groupBox)
        self.lbl_end_hold.setObjectName(u"lbl_end_hold")

        self.horizontalLayout_18.addWidget(self.lbl_end_hold)

        self.horizontalLayout_19 = QHBoxLayout()
        self.horizontalLayout_19.setObjectName(u"horizontalLayout_19")
        self.lineEdit_end_hold = QLineEdit(self.groupBox)
        self.lineEdit_end_hold.setObjectName(u"lineEdit_end_hold")

        self.horizontalLayout_19.addWidget(self.lineEdit_end_hold)


        self.horizontalLayout_18.addLayout(self.horizontalLayout_19)


        self.verticalLayout_2.addLayout(self.horizontalLayout_18)

        self.horizontalLayout_20 = QHBoxLayout()
        self.horizontalLayout_20.setObjectName(u"horizontalLayout_20")
        self.lbl_bitrate = QLabel(self.groupBox)
        self.lbl_bitrate.setObjectName(u"lbl_bitrate")

        self.horizontalLayout_20.addWidget(self.lbl_bitrate)

        self.combo_bitrate = QComboBox(self.groupBox)
        self.combo_bitrate.setObjectName(u"combo_bitrate")
        sizePolicy2.setHeightForWidth(self.combo_bitrate.sizePolicy().hasHeightForWidth())
        self.combo_bitrate.setSizePolicy(sizePolicy2)

        self.horizontalLayout_20.addWidget(self.combo_bitrate)


        self.verticalLayout_2.addLayout(self.horizontalLayout_20)


        self.gridLayout_3.addLayout(self.verticalLayout_2, 0, 2, 1, 1)

        self.line_3 = QFrame(self.groupBox)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.Shape.VLine)
        self.line_3.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout_3.addWidget(self.line_3, 0, 3, 6, 1)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.chk_auto_duration = QCheckBox(self.groupBox)
        self.chk_auto_duration.setObjectName(u"chk_auto_duration")

        self.gridLayout_2.addWidget(self.chk_auto_duration, 0, 0, 1, 1)

        self.horizontalSpacer = QSpacerItem(73, 13, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_2.addItem(self.horizontalSpacer, 0, 1, 1, 2)

        self.horizontalLayout_21 = QHBoxLayout()
        self.horizontalLayout_21.setObjectName(u"horizontalLayout_21")
        self.lbl_rate = QLabel(self.groupBox)
        self.lbl_rate.setObjectName(u"lbl_rate")

        self.horizontalLayout_21.addWidget(self.lbl_rate)

        self.horizontalLayout_rate = QHBoxLayout()
        self.horizontalLayout_rate.setObjectName(u"horizontalLayout_rate")
        self.spin_seconds_per_100km = QSpinBox(self.groupBox)
        self.spin_seconds_per_100km.setObjectName(u"spin_seconds_per_100km")
        sizePolicy2.setHeightForWidth(self.spin_seconds_per_100km.sizePolicy().hasHeightForWidth())
        self.spin_seconds_per_100km.setSizePolicy(sizePolicy2)
        self.spin_seconds_per_100km.setMinimum(1)
        self.spin_seconds_per_100km.setMaximum(9999)
        self.spin_seconds_per_100km.setValue(60)

        self.horizontalLayout_rate.addWidget(self.spin_seconds_per_100km)

        self.lbl_rate_unit = QLabel(self.groupBox)
        self.lbl_rate_unit.setObjectName(u"lbl_rate_unit")

        self.horizontalLayout_rate.addWidget(self.lbl_rate_unit)


        self.horizontalLayout_21.addLayout(self.horizontalLayout_rate)


        self.gridLayout_2.addLayout(self.horizontalLayout_21, 1, 0, 1, 3)

        self.horizontalSpacer_2 = QSpacerItem(37, 13, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_2.addItem(self.horizontalSpacer_2, 1, 3, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.lbl_duration = QLabel(self.groupBox)
        self.lbl_duration.setObjectName(u"lbl_duration")

        self.horizontalLayout.addWidget(self.lbl_duration)

        self.lineEdit_duration = QLineEdit(self.groupBox)
        self.lineEdit_duration.setObjectName(u"lineEdit_duration")

        self.horizontalLayout.addWidget(self.lineEdit_duration)


        self.gridLayout_2.addLayout(self.horizontalLayout, 2, 0, 1, 2)

        self.horizontalSpacer_3 = QSpacerItem(110, 13, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_2.addItem(self.horizontalSpacer_3, 2, 2, 1, 2)

        self.label_distance_info = QLabel(self.groupBox)
        self.label_distance_info.setObjectName(u"label_distance_info")

        self.gridLayout_2.addWidget(self.label_distance_info, 3, 0, 1, 2)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_2.addItem(self.horizontalSpacer_4, 3, 2, 1, 1)


        self.verticalLayout_4.addLayout(self.gridLayout_2)

        self.line_4 = QFrame(self.groupBox)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setFrameShape(QFrame.Shape.HLine)
        self.line_4.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_4.addWidget(self.line_4)

        self.chk_preview = QCheckBox(self.groupBox)
        self.chk_preview.setObjectName(u"chk_preview")

        self.verticalLayout_4.addWidget(self.chk_preview)

        self.combo_cache_mode = QComboBox(self.groupBox)
        self.combo_cache_mode.setObjectName(u"combo_cache_mode")

        self.verticalLayout_4.addWidget(self.combo_cache_mode)

        self.horizontalLayout_cache_actions = QHBoxLayout()
        self.horizontalLayout_cache_actions.setObjectName(u"horizontalLayout_cache_actions")
        self.lbl_cache_size = QLabel(self.groupBox)
        self.lbl_cache_size.setObjectName(u"lbl_cache_size")

        self.horizontalLayout_cache_actions.addWidget(self.lbl_cache_size)

        self.btn_clear_cache = QPushButton(self.groupBox)
        self.btn_clear_cache.setObjectName(u"btn_clear_cache")

        self.horizontalLayout_cache_actions.addWidget(self.btn_clear_cache)


        self.verticalLayout_4.addLayout(self.horizontalLayout_cache_actions)


        self.gridLayout_3.addLayout(self.verticalLayout_4, 0, 4, 6, 1)

        self.line = QFrame(self.groupBox)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout_3.addWidget(self.line, 1, 0, 1, 3)

        self.horizontalLayout_22 = QHBoxLayout()
        self.horizontalLayout_22.setObjectName(u"horizontalLayout_22")
        self.lbl_hide_privacy = QLabel(self.groupBox)
        self.lbl_hide_privacy.setObjectName(u"lbl_hide_privacy")

        self.horizontalLayout_22.addWidget(self.lbl_hide_privacy)

        self.horizontalLayout_hide = QHBoxLayout()
        self.horizontalLayout_hide.setObjectName(u"horizontalLayout_hide")
        self.lbl_hide_start = QLabel(self.groupBox)
        self.lbl_hide_start.setObjectName(u"lbl_hide_start")

        self.horizontalLayout_hide.addWidget(self.lbl_hide_start)

        self.spin_hide_start = QDoubleSpinBox(self.groupBox)
        self.spin_hide_start.setObjectName(u"spin_hide_start")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.spin_hide_start.sizePolicy().hasHeightForWidth())
        self.spin_hide_start.setSizePolicy(sizePolicy3)

        self.horizontalLayout_hide.addWidget(self.spin_hide_start)

        self.lbl_hide_end = QLabel(self.groupBox)
        self.lbl_hide_end.setObjectName(u"lbl_hide_end")

        self.horizontalLayout_hide.addWidget(self.lbl_hide_end)

        self.spin_hide_end = QDoubleSpinBox(self.groupBox)
        self.spin_hide_end.setObjectName(u"spin_hide_end")
        sizePolicy3.setHeightForWidth(self.spin_hide_end.sizePolicy().hasHeightForWidth())
        self.spin_hide_end.setSizePolicy(sizePolicy3)

        self.horizontalLayout_hide.addWidget(self.spin_hide_end)

        self.lbl_hide_unit = QLabel(self.groupBox)
        self.lbl_hide_unit.setObjectName(u"lbl_hide_unit")

        self.horizontalLayout_hide.addWidget(self.lbl_hide_unit)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_hide.addItem(self.horizontalSpacer_5)


        self.horizontalLayout_22.addLayout(self.horizontalLayout_hide)


        self.gridLayout_3.addLayout(self.horizontalLayout_22, 2, 0, 1, 1)

        self.horizontalLayout_23 = QHBoxLayout()
        self.horizontalLayout_23.setObjectName(u"horizontalLayout_23")
        self.lbl_workers_chunks = QLabel(self.groupBox)
        self.lbl_workers_chunks.setObjectName(u"lbl_workers_chunks")

        self.horizontalLayout_23.addWidget(self.lbl_workers_chunks)

        self.horizontalLayout_wc = QHBoxLayout()
        self.horizontalLayout_wc.setObjectName(u"horizontalLayout_wc")
        self.spin_workers = QSpinBox(self.groupBox)
        self.spin_workers.setObjectName(u"spin_workers")
        sizePolicy3.setHeightForWidth(self.spin_workers.sizePolicy().hasHeightForWidth())
        self.spin_workers.setSizePolicy(sizePolicy3)
        self.spin_workers.setValue(6)

        self.horizontalLayout_wc.addWidget(self.spin_workers)

        self.lbl_wc_x = QLabel(self.groupBox)
        self.lbl_wc_x.setObjectName(u"lbl_wc_x")

        self.horizontalLayout_wc.addWidget(self.lbl_wc_x)

        self.spin_chunks = QSpinBox(self.groupBox)
        self.spin_chunks.setObjectName(u"spin_chunks")
        sizePolicy3.setHeightForWidth(self.spin_chunks.sizePolicy().hasHeightForWidth())
        self.spin_chunks.setSizePolicy(sizePolicy3)
        self.spin_chunks.setValue(4)

        self.horizontalLayout_wc.addWidget(self.spin_chunks)

        self.lbl_wc_unit = QLabel(self.groupBox)
        self.lbl_wc_unit.setObjectName(u"lbl_wc_unit")

        self.horizontalLayout_wc.addWidget(self.lbl_wc_unit)


        self.horizontalLayout_23.addLayout(self.horizontalLayout_wc)


        self.gridLayout_3.addLayout(self.horizontalLayout_23, 3, 0, 1, 1)

        self.horizontalLayout_24 = QHBoxLayout()
        self.horizontalLayout_24.setObjectName(u"horizontalLayout_24")
        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_24.addItem(self.horizontalSpacer_6)

        self.lbl_tile_connections = QLabel(self.groupBox)
        self.lbl_tile_connections.setObjectName(u"lbl_tile_connections")

        self.horizontalLayout_24.addWidget(self.lbl_tile_connections)

        self.spin_tile_connections = QSpinBox(self.groupBox)
        self.spin_tile_connections.setObjectName(u"spin_tile_connections")
        sizePolicy3.setHeightForWidth(self.spin_tile_connections.sizePolicy().hasHeightForWidth())
        self.spin_tile_connections.setSizePolicy(sizePolicy3)
        self.spin_tile_connections.setValue(4)

        self.horizontalLayout_24.addWidget(self.spin_tile_connections)


        self.gridLayout_3.addLayout(self.horizontalLayout_24, 3, 2, 1, 1)

        self.line_5 = QFrame(self.groupBox)
        self.line_5.setObjectName(u"line_5")
        self.line_5.setFrameShape(QFrame.Shape.HLine)
        self.line_5.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout_3.addWidget(self.line_5, 4, 0, 1, 3)

        self.horizontalLayout_autotune = QHBoxLayout()
        self.horizontalLayout_autotune.setObjectName(u"horizontalLayout_autotune")
        self.btn_autotune = QPushButton(self.groupBox)
        self.btn_autotune.setObjectName(u"btn_autotune")
        self.btn_autotune.setMaximumSize(QSize(150, 16777215))

        self.horizontalLayout_autotune.addWidget(self.btn_autotune)

        self.label_autotune_result = QLabel(self.groupBox)
        self.label_autotune_result.setObjectName(u"label_autotune_result")

        self.horizontalLayout_autotune.addWidget(self.label_autotune_result)

        self.btn_apply_benchmark = QPushButton(self.groupBox)
        self.btn_apply_benchmark.setObjectName(u"btn_apply_benchmark")
        self.btn_apply_benchmark.setEnabled(False)
        self.btn_apply_benchmark.setMaximumSize(QSize(150, 16777215))

        self.horizontalLayout_autotune.addWidget(self.btn_apply_benchmark)


        self.gridLayout_3.addLayout(self.horizontalLayout_autotune, 5, 0, 1, 3)


        self.verticalLayout_tab_advanced.addWidget(self.groupBox)

        self.tabWidget.addTab(self.tab_advanced, "")
        self.tab_workers = QWidget()
        self.tab_workers.setObjectName(u"tab_workers")
        self.verticalLayout_tab_workers = QVBoxLayout(self.tab_workers)
        self.verticalLayout_tab_workers.setSpacing(4)
        self.verticalLayout_tab_workers.setObjectName(u"verticalLayout_tab_workers")
        self.verticalLayout_tab_workers.setContentsMargins(4, 4, 4, 4)
        self.groupBox_workers = QGroupBox(self.tab_workers)
        self.groupBox_workers.setObjectName(u"groupBox_workers")
        self.gridLayout_5 = QGridLayout(self.groupBox_workers)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.verticalLayout_16 = QVBoxLayout()
        self.verticalLayout_16.setObjectName(u"verticalLayout_16")
        self.progressBar_main = PyCircularProgress(self.groupBox_workers)
        self.progressBar_main.setObjectName(u"progressBar_main")
        self.progressBar_main.setMinimumSize(QSize(110, 110))
        self.progressBar_main.setValue(0)

        self.verticalLayout_16.addWidget(self.progressBar_main)

        self.verticalLayout_9 = QVBoxLayout()
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label_eta_elapsed = QLabel(self.groupBox_workers)
        self.label_eta_elapsed.setObjectName(u"label_eta_elapsed")

        self.verticalLayout_3.addWidget(self.label_eta_elapsed)

        self.line_6 = QFrame(self.groupBox_workers)
        self.line_6.setObjectName(u"line_6")
        self.line_6.setFrameShape(QFrame.Shape.HLine)
        self.line_6.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_3.addWidget(self.line_6)


        self.verticalLayout_9.addLayout(self.verticalLayout_3)

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.label_eta_time = QLabel(self.groupBox_workers)
        self.label_eta_time.setObjectName(u"label_eta_time")

        self.verticalLayout_5.addWidget(self.label_eta_time)

        self.line_7 = QFrame(self.groupBox_workers)
        self.line_7.setObjectName(u"line_7")
        self.line_7.setFrameShape(QFrame.Shape.HLine)
        self.line_7.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_5.addWidget(self.line_7)


        self.verticalLayout_9.addLayout(self.verticalLayout_5)

        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.label_eta_clock = QLabel(self.groupBox_workers)
        self.label_eta_clock.setObjectName(u"label_eta_clock")

        self.verticalLayout_6.addWidget(self.label_eta_clock)

        self.line_8 = QFrame(self.groupBox_workers)
        self.line_8.setObjectName(u"line_8")
        self.line_8.setFrameShape(QFrame.Shape.HLine)
        self.line_8.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_6.addWidget(self.line_8)


        self.verticalLayout_9.addLayout(self.verticalLayout_6)

        self.verticalLayout_7 = QVBoxLayout()
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.label_eta_frames = QLabel(self.groupBox_workers)
        self.label_eta_frames.setObjectName(u"label_eta_frames")

        self.verticalLayout_7.addWidget(self.label_eta_frames)

        self.line_9 = QFrame(self.groupBox_workers)
        self.line_9.setObjectName(u"line_9")
        self.line_9.setFrameShape(QFrame.Shape.HLine)
        self.line_9.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_7.addWidget(self.line_9)


        self.verticalLayout_9.addLayout(self.verticalLayout_7)

        self.verticalLayout_8 = QVBoxLayout()
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.label_eta_speed = QLabel(self.groupBox_workers)
        self.label_eta_speed.setObjectName(u"label_eta_speed")

        self.verticalLayout_8.addWidget(self.label_eta_speed)

        self.line_10 = QFrame(self.groupBox_workers)
        self.line_10.setObjectName(u"line_10")
        self.line_10.setFrameShape(QFrame.Shape.HLine)
        self.line_10.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_8.addWidget(self.line_10)


        self.verticalLayout_9.addLayout(self.verticalLayout_8)


        self.verticalLayout_16.addLayout(self.verticalLayout_9)


        self.gridLayout_5.addLayout(self.verticalLayout_16, 0, 0, 1, 1)

        self.gridLayout_4 = QGridLayout()
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.verticalLayout_10 = QVBoxLayout()
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.progressBar_worker_1 = PyCircularProgress(self.groupBox_workers)
        self.progressBar_worker_1.setObjectName(u"progressBar_worker_1")
        self.progressBar_worker_1.setMinimumSize(QSize(65, 65))
        self.progressBar_worker_1.setValue(0)

        self.verticalLayout_10.addWidget(self.progressBar_worker_1)

        self.horizontalLayout_worker_1 = QHBoxLayout()
        self.horizontalLayout_worker_1.setObjectName(u"horizontalLayout_worker_1")
        self.lbl_worker_1 = QLabel(self.groupBox_workers)
        self.lbl_worker_1.setObjectName(u"lbl_worker_1")

        self.horizontalLayout_worker_1.addWidget(self.lbl_worker_1)

        self.lbl_worker_status_1 = QLabel(self.groupBox_workers)
        self.lbl_worker_status_1.setObjectName(u"lbl_worker_status_1")

        self.horizontalLayout_worker_1.addWidget(self.lbl_worker_status_1)


        self.verticalLayout_10.addLayout(self.horizontalLayout_worker_1)


        self.gridLayout_4.addLayout(self.verticalLayout_10, 0, 0, 1, 1)

        self.verticalLayout_13 = QVBoxLayout()
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")
        self.progressBar_worker_4 = PyCircularProgress(self.groupBox_workers)
        self.progressBar_worker_4.setObjectName(u"progressBar_worker_4")
        self.progressBar_worker_4.setMinimumSize(QSize(65, 65))
        self.progressBar_worker_4.setValue(0)

        self.verticalLayout_13.addWidget(self.progressBar_worker_4)

        self.horizontalLayout_worker_4 = QHBoxLayout()
        self.horizontalLayout_worker_4.setObjectName(u"horizontalLayout_worker_4")
        self.lbl_worker_4 = QLabel(self.groupBox_workers)
        self.lbl_worker_4.setObjectName(u"lbl_worker_4")

        self.horizontalLayout_worker_4.addWidget(self.lbl_worker_4)

        self.lbl_worker_status_4 = QLabel(self.groupBox_workers)
        self.lbl_worker_status_4.setObjectName(u"lbl_worker_status_4")

        self.horizontalLayout_worker_4.addWidget(self.lbl_worker_status_4)


        self.verticalLayout_13.addLayout(self.horizontalLayout_worker_4)


        self.gridLayout_4.addLayout(self.verticalLayout_13, 0, 1, 1, 1)

        self.verticalLayout_11 = QVBoxLayout()
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.progressBar_worker_2 = PyCircularProgress(self.groupBox_workers)
        self.progressBar_worker_2.setObjectName(u"progressBar_worker_2")
        self.progressBar_worker_2.setMinimumSize(QSize(65, 65))
        self.progressBar_worker_2.setValue(0)

        self.verticalLayout_11.addWidget(self.progressBar_worker_2)

        self.horizontalLayout_worker_2 = QHBoxLayout()
        self.horizontalLayout_worker_2.setObjectName(u"horizontalLayout_worker_2")
        self.lbl_worker_2 = QLabel(self.groupBox_workers)
        self.lbl_worker_2.setObjectName(u"lbl_worker_2")

        self.horizontalLayout_worker_2.addWidget(self.lbl_worker_2)

        self.lbl_worker_status_2 = QLabel(self.groupBox_workers)
        self.lbl_worker_status_2.setObjectName(u"lbl_worker_status_2")

        self.horizontalLayout_worker_2.addWidget(self.lbl_worker_status_2)


        self.verticalLayout_11.addLayout(self.horizontalLayout_worker_2)


        self.gridLayout_4.addLayout(self.verticalLayout_11, 1, 0, 1, 1)

        self.verticalLayout_14 = QVBoxLayout()
        self.verticalLayout_14.setObjectName(u"verticalLayout_14")
        self.progressBar_worker_5 = PyCircularProgress(self.groupBox_workers)
        self.progressBar_worker_5.setObjectName(u"progressBar_worker_5")
        self.progressBar_worker_5.setMinimumSize(QSize(65, 65))
        self.progressBar_worker_5.setValue(0)

        self.verticalLayout_14.addWidget(self.progressBar_worker_5)

        self.horizontalLayout_worker_5 = QHBoxLayout()
        self.horizontalLayout_worker_5.setObjectName(u"horizontalLayout_worker_5")
        self.lbl_worker_5 = QLabel(self.groupBox_workers)
        self.lbl_worker_5.setObjectName(u"lbl_worker_5")

        self.horizontalLayout_worker_5.addWidget(self.lbl_worker_5)

        self.lbl_worker_status_5 = QLabel(self.groupBox_workers)
        self.lbl_worker_status_5.setObjectName(u"lbl_worker_status_5")

        self.horizontalLayout_worker_5.addWidget(self.lbl_worker_status_5)


        self.verticalLayout_14.addLayout(self.horizontalLayout_worker_5)


        self.gridLayout_4.addLayout(self.verticalLayout_14, 1, 1, 1, 1)

        self.verticalLayout_12 = QVBoxLayout()
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.progressBar_worker_3 = PyCircularProgress(self.groupBox_workers)
        self.progressBar_worker_3.setObjectName(u"progressBar_worker_3")
        self.progressBar_worker_3.setMinimumSize(QSize(65, 65))
        self.progressBar_worker_3.setValue(0)

        self.verticalLayout_12.addWidget(self.progressBar_worker_3)

        self.horizontalLayout_worker_3 = QHBoxLayout()
        self.horizontalLayout_worker_3.setObjectName(u"horizontalLayout_worker_3")
        self.lbl_worker_3 = QLabel(self.groupBox_workers)
        self.lbl_worker_3.setObjectName(u"lbl_worker_3")

        self.horizontalLayout_worker_3.addWidget(self.lbl_worker_3)

        self.lbl_worker_status_3 = QLabel(self.groupBox_workers)
        self.lbl_worker_status_3.setObjectName(u"lbl_worker_status_3")

        self.horizontalLayout_worker_3.addWidget(self.lbl_worker_status_3)


        self.verticalLayout_12.addLayout(self.horizontalLayout_worker_3)


        self.gridLayout_4.addLayout(self.verticalLayout_12, 2, 0, 1, 1)

        self.verticalLayout_15 = QVBoxLayout()
        self.verticalLayout_15.setObjectName(u"verticalLayout_15")
        self.progressBar_worker_6 = PyCircularProgress(self.groupBox_workers)
        self.progressBar_worker_6.setObjectName(u"progressBar_worker_6")
        self.progressBar_worker_6.setMinimumSize(QSize(65, 65))
        self.progressBar_worker_6.setValue(0)

        self.verticalLayout_15.addWidget(self.progressBar_worker_6)

        self.horizontalLayout_worker_6 = QHBoxLayout()
        self.horizontalLayout_worker_6.setObjectName(u"horizontalLayout_worker_6")
        self.lbl_worker_6 = QLabel(self.groupBox_workers)
        self.lbl_worker_6.setObjectName(u"lbl_worker_6")

        self.horizontalLayout_worker_6.addWidget(self.lbl_worker_6)

        self.lbl_worker_status_6 = QLabel(self.groupBox_workers)
        self.lbl_worker_status_6.setObjectName(u"lbl_worker_status_6")

        self.horizontalLayout_worker_6.addWidget(self.lbl_worker_status_6)


        self.verticalLayout_15.addLayout(self.horizontalLayout_worker_6)


        self.gridLayout_4.addLayout(self.verticalLayout_15, 2, 1, 1, 1)


        self.gridLayout_5.addLayout(self.gridLayout_4, 0, 1, 1, 1)


        self.verticalLayout_tab_workers.addWidget(self.groupBox_workers)

        self.tabWidget.addTab(self.tab_workers, "")

        self.verticalLayout_main.addWidget(self.tabWidget)

        self.horizontalLayout_actions = QHBoxLayout()
        self.horizontalLayout_actions.setObjectName(u"horizontalLayout_actions")
        self.btn_start_render = QPushButton(self.centralwidget)
        self.btn_start_render.setObjectName(u"btn_start_render")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.btn_start_render.sizePolicy().hasHeightForWidth())
        self.btn_start_render.setSizePolicy(sizePolicy4)
        self.btn_start_render.setMinimumSize(QSize(0, 50))
        font = QFont()
        font.setPointSize(12)
        self.btn_start_render.setFont(font)

        self.horizontalLayout_actions.addWidget(self.btn_start_render)

        self.btn_stop_render = QPushButton(self.centralwidget)
        self.btn_stop_render.setObjectName(u"btn_stop_render")
        self.btn_stop_render.setEnabled(False)
        sizePolicy4.setHeightForWidth(self.btn_stop_render.sizePolicy().hasHeightForWidth())
        self.btn_stop_render.setSizePolicy(sizePolicy4)
        self.btn_stop_render.setMinimumSize(QSize(0, 50))
        self.btn_stop_render.setFont(font)

        self.horizontalLayout_actions.addWidget(self.btn_stop_render)


        self.verticalLayout_main.addLayout(self.horizontalLayout_actions)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 880, 33))
        self.menu_file = QMenu(self.menubar)
        self.menu_file.setObjectName(u"menu_file")
        self.menu_edit = QMenu(self.menubar)
        self.menu_edit.setObjectName(u"menu_edit")
        self.menu_view = QMenu(self.menubar)
        self.menu_view.setObjectName(u"menu_view")
        self.menu_settings = QMenu(self.menubar)
        self.menu_settings.setObjectName(u"menu_settings")
        self.menu_profile = QMenu(self.menu_settings)
        self.menu_profile.setObjectName(u"menu_profile")
        self.menu_hud_panels = QMenu(self.menu_settings)
        self.menu_hud_panels.setObjectName(u"menu_hud_panels")
        self.menu_cache_mode = QMenu(self.menu_settings)
        self.menu_cache_mode.setObjectName(u"menu_cache_mode")
        self.menu_help = QMenu(self.menubar)
        self.menu_help.setObjectName(u"menu_help")
        MainWindow.setMenuBar(self.menubar)
        self.toolBar = QToolBar(MainWindow)
        self.toolBar.setObjectName(u"toolBar")
        self.toolBar.setMovable(False)
        self.toolBar.setIconSize(QSize(22, 22))
        self.toolBar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        MainWindow.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolBar)

        self.menubar.addAction(self.menu_file.menuAction())
        self.menubar.addAction(self.menu_edit.menuAction())
        self.menubar.addAction(self.menu_view.menuAction())
        self.menubar.addAction(self.menu_settings.menuAction())
        self.menubar.addAction(self.menu_help.menuAction())
        self.menu_file.addAction(self.action_open_gpx)
        self.menu_file.addAction(self.action_save_output)
        self.menu_file.addAction(self.action_select_media)
        self.menu_file.addAction(self.action_media_dialog)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_open_log_folder)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_exit)
        self.menu_edit.addAction(self.action_benchmark)
        self.menu_edit.addAction(self.action_apply_benchmark)
        self.menu_edit.addSeparator()
        self.menu_edit.addAction(self.action_clear_cache)
        self.menu_edit.addAction(self.action_refresh_distance)
        self.menu_view.addAction(self.action_toggle_toolbar)
        self.menu_view.addAction(self.action_toggle_advanced)
        self.menu_view.addSeparator()
        self.menu_view.addAction(self.action_toggle_summary)
        self.menu_view.addAction(self.action_toggle_workers)
        self.menu_settings.addAction(self.menu_profile.menuAction())
        self.menu_settings.addSeparator()
        self.menu_settings.addAction(self.menu_hud_panels.menuAction())
        self.menu_settings.addAction(self.action_dynamic_speed_zoom)
        self.menu_settings.addAction(self.action_real_speed)
        self.menu_settings.addAction(self.action_basemap)
        self.menu_settings.addAction(self.action_parallel)
        self.menu_settings.addAction(self.action_enable_media)
        self.menu_settings.addAction(self.action_preview)
        self.menu_settings.addSeparator()
        self.menu_settings.addAction(self.menu_cache_mode.menuAction())
        self.menu_profile.addAction(self.action_profile_fast)
        self.menu_profile.addAction(self.action_profile_balanced)
        self.menu_profile.addAction(self.action_profile_quality)
        self.menu_hud_panels.addAction(self.action_show_speed)
        self.menu_hud_panels.addAction(self.action_show_minimap)
        self.menu_hud_panels.addAction(self.action_show_elevation)
        self.menu_cache_mode.addAction(self.action_cache_session)
        self.menu_cache_mode.addAction(self.action_cache_persistent)
        self.menu_help.addAction(self.action_help_shortcuts)
        self.menu_help.addAction(self.action_about)
        self.toolBar.addAction(self.action_open_gpx)
        self.toolBar.addAction(self.action_media_dialog)
        self.toolBar.addAction(self.action_benchmark)
        self.toolBar.addAction(self.action_clear_cache)
        self.toolBar.addAction(self.action_open_log_folder)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.action_toggle_advanced)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.action_start_render)
        self.toolBar.addAction(self.action_stop_render)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(2)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"GPX Ride Renderer V1.3.5", None))
        self.action_open_gpx.setText(QCoreApplication.translate("MainWindow", u"\u9078\u64c7 GPX \u6a94\u6848...", None))
#if QT_CONFIG(tooltip)
        self.action_open_gpx.setToolTip(QCoreApplication.translate("MainWindow", u"\u9078\u64c7\u6b32\u6e32\u67d3\u7684 GPX \u8ecc\u8de1\u8def\u5f91\u6a94\u6848 (.gpx) [Ctrl+O]", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.action_open_gpx.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+O", None))
#endif // QT_CONFIG(shortcut)
        self.action_save_output.setText(QCoreApplication.translate("MainWindow", u"\u6307\u5b9a\u8f38\u51fa\u5f71\u7247\u8def\u5f91...", None))
#if QT_CONFIG(tooltip)
        self.action_save_output.setToolTip(QCoreApplication.translate("MainWindow", u"\u6307\u5b9a\u8f38\u51fa\u7684 MP4 \u5f71\u7247\u6a94\u540d\u8207\u8def\u5f91 [Ctrl+S]", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.action_save_output.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+S", None))
#endif // QT_CONFIG(shortcut)
        self.action_select_media.setText(QCoreApplication.translate("MainWindow", u"\u9078\u64c7\u8def\u7dda\u5a92\u9ad4...", None))
#if QT_CONFIG(tooltip)
        self.action_select_media.setToolTip(QCoreApplication.translate("MainWindow", u"\u9078\u64c7\u8def\u7dda\u7167\u7247\u6216\u5f71\u7247\u8cc7\u6599\u593e/\u6a94\u6848", None))
#endif // QT_CONFIG(tooltip)
        self.action_media_dialog.setText(QCoreApplication.translate("MainWindow", u"\u958b\u555f\u5a92\u9ad4\u7ba1\u7406\u5668...", None))
#if QT_CONFIG(tooltip)
        self.action_media_dialog.setToolTip(QCoreApplication.translate("MainWindow", u"\u958b\u555f\u8def\u7dda\u7167\u7247\u8207\u5f71\u7247\u7ba1\u7406\u7de8\u8f2f\u5668\uff0c\u8a2d\u5b9a\u505c\u7559\u6642\u9593\u3001\u6a19\u7c64\u8207\u7cbe\u78ba\u4f4d\u7f6e [Ctrl+M]", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.action_media_dialog.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+M", None))
#endif // QT_CONFIG(shortcut)
        self.action_open_log_folder.setText(QCoreApplication.translate("MainWindow", u"\u958b\u555f Log \u8cc7\u6599\u593e", None))
#if QT_CONFIG(tooltip)
        self.action_open_log_folder.setToolTip(QCoreApplication.translate("MainWindow", u"\u958b\u555f\u5132\u5b58\u6e32\u67d3\u8a18\u9304\u8207\u5075\u932f\u8cc7\u8a0a\u7684 Log \u8cc7\u6599\u593e [Ctrl+L]", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.action_open_log_folder.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+L", None))
#endif // QT_CONFIG(shortcut)
        self.action_exit.setText(QCoreApplication.translate("MainWindow", u"\u7d50\u675f", None))
#if QT_CONFIG(shortcut)
        self.action_exit.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+Q", None))
#endif // QT_CONFIG(shortcut)
        self.action_benchmark.setText(QCoreApplication.translate("MainWindow", u"\u6548\u80fd\u6e2c\u8a66 / Auto Tune", None))
#if QT_CONFIG(tooltip)
        self.action_benchmark.setToolTip(QCoreApplication.translate("MainWindow", u"\u5be6\u6e2c\u4e0d\u540c Workers \u6578\u91cf\u7684\u6e32\u67d3 FPS\uff0c\u63a8\u85a6\u6700\u5408\u9069\u7684 Worker \u8a2d\u5b9a [Ctrl+T]", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.action_benchmark.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+T", None))
#endif // QT_CONFIG(shortcut)
        self.action_apply_benchmark.setText(QCoreApplication.translate("MainWindow", u"\u5957\u7528 Auto Tune \u6700\u4f73\u5efa\u8b70", None))
#if QT_CONFIG(tooltip)
        self.action_apply_benchmark.setToolTip(QCoreApplication.translate("MainWindow", u"\u81ea\u52d5\u5957\u7528\u6e2c\u8a66\u63a8\u85a6\u4e4b\u6700\u4f73 Worker \u6578\u91cf", None))
#endif // QT_CONFIG(tooltip)
        self.action_clear_cache.setText(QCoreApplication.translate("MainWindow", u"\u6e05\u9664\u672c\u6a5f\u5730\u5716\u8207\u9ad8\u7a0b\u5feb\u53d6...", None))
#if QT_CONFIG(tooltip)
        self.action_clear_cache.setToolTip(QCoreApplication.translate("MainWindow", u"\u7acb\u5373\u6e05\u9664\u6240\u6709\u672c\u6a5f\u78c1\u789f\u5e95\u5716\u8207\u9ad8\u7a0b\u5feb\u53d6\u8cc7\u6599", None))
#endif // QT_CONFIG(tooltip)
        self.action_refresh_distance.setText(QCoreApplication.translate("MainWindow", u"\u91cd\u65b0\u6574\u7406 GPX \u8ddd\u96e2\u8207\u6642\u9577", None))
#if QT_CONFIG(tooltip)
        self.action_refresh_distance.setToolTip(QCoreApplication.translate("MainWindow", u"\u91cd\u65b0\u8a08\u7b97 GPX \u8ecc\u8de1\u7e3d\u91cc\u7a0b\u8207\u9810\u4f30\u6642\u9577 [F5]", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.action_refresh_distance.setShortcut(QCoreApplication.translate("MainWindow", u"F5", None))
#endif // QT_CONFIG(shortcut)
        self.action_toggle_toolbar.setText(QCoreApplication.translate("MainWindow", u"\u986f\u793a\u5feb\u6377\u5de5\u5177\u5217", None))
#if QT_CONFIG(tooltip)
        self.action_toggle_toolbar.setToolTip(QCoreApplication.translate("MainWindow", u"\u5207\u63db\u662f\u5426\u986f\u793a\u9802\u90e8\u5feb\u6377\u5de5\u5177\u5217", None))
#endif // QT_CONFIG(tooltip)
        self.action_toggle_advanced.setText(QCoreApplication.translate("MainWindow", u"\u5207\u63db\u81f3\u9032\u968e\u8a2d\u5b9a\u5206\u9801", None))
#if QT_CONFIG(tooltip)
        self.action_toggle_advanced.setToolTip(QCoreApplication.translate("MainWindow", u"\u5207\u63db\u81f3\u9032\u968e\u53c3\u6578\u8a2d\u5b9a\u5206\u9801 (\u5305\u542b\u81ea\u8a02\u89e3\u6790\u5ea6\u3001FPS\u3001\u78bc\u7387\u7b49) [Ctrl+Shift+A]", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.action_toggle_advanced.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+Shift+A", None))
#endif // QT_CONFIG(shortcut)
        self.action_toggle_summary.setText(QCoreApplication.translate("MainWindow", u"\u986f\u793a\u8a2d\u5b9a\u6458\u8981\u9762\u677f", None))
#if QT_CONFIG(tooltip)
        self.action_toggle_summary.setToolTip(QCoreApplication.translate("MainWindow", u"\u5207\u63db\u986f\u793a\u6216\u96b1\u85cf\u6e32\u67d3\u8a2d\u5b9a\u6458\u8981\u9762\u677f", None))
#endif // QT_CONFIG(tooltip)
        self.action_toggle_workers.setText(QCoreApplication.translate("MainWindow", u"\u986f\u793a Worker \u5b50\u9032\u5ea6\u689d", None))
#if QT_CONFIG(tooltip)
        self.action_toggle_workers.setToolTip(QCoreApplication.translate("MainWindow", u"\u5207\u63db\u986f\u793a\u6216\u96b1\u85cf\u5404 Worker \u5b50\u9032\u5ea6\u689d\uff0c\u7bc0\u7701\u8996\u7a97\u7248\u9762\u5782\u76f4\u9ad8\u5ea6", None))
#endif // QT_CONFIG(tooltip)
        self.action_profile_fast.setText(QCoreApplication.translate("MainWindow", u"\u5feb\u901f\u6a21\u5f0f (720p / p3 / 12M)", None))
        self.action_profile_balanced.setText(QCoreApplication.translate("MainWindow", u"\u5e73\u8861\u6a21\u5f0f (1080p / p4 / 20M)", None))
        self.action_profile_quality.setText(QCoreApplication.translate("MainWindow", u"\u9ad8\u756b\u8cea\u6a21\u5f0f (1440p / p5 / 30M)", None))
        self.action_show_speed.setText(QCoreApplication.translate("MainWindow", u"\u901f\u5ea6\u9762\u677f (Speed HUD)", None))
        self.action_show_minimap.setText(QCoreApplication.translate("MainWindow", u"\u8def\u7dda\u7e2e\u5716 (Minimap)", None))
        self.action_show_elevation.setText(QCoreApplication.translate("MainWindow", u"\u6d77\u62d4\u5716 (Elevation)", None))
        self.action_dynamic_speed_zoom.setText(QCoreApplication.translate("MainWindow", u"\u901f\u5ea6\u52d5\u614b\u93e1\u982d", None))
        self.action_real_speed.setText(QCoreApplication.translate("MainWindow", u"\u8ddf\u96a8 GPX \u5be6\u969b\u901f\u5ea6", None))
        self.action_basemap.setText(QCoreApplication.translate("MainWindow", u"\u5730\u5716\u5e95\u5716", None))
        self.action_parallel.setText(QCoreApplication.translate("MainWindow", u"\u591a\u7a0b\u5e8f\u6e32\u67d3", None))
        self.action_enable_media.setText(QCoreApplication.translate("MainWindow", u"\u8def\u7dda\u5a92\u9ad4\u5361\u7247", None))
        self.action_preview.setText(QCoreApplication.translate("MainWindow", u"Preview \u9810\u89bd\u6a21\u5f0f", None))
        self.action_cache_session.setText(QCoreApplication.translate("MainWindow", u"\u81ea\u52d5\u66ab\u5b58 (\u95dc\u9589\u6e05\u9664)", None))
        self.action_cache_persistent.setText(QCoreApplication.translate("MainWindow", u"\u6c38\u4e45\u4fdd\u7559 (\u52a0\u901f\u6e32\u67d3)", None))
        self.action_start_render.setText(QCoreApplication.translate("MainWindow", u"\u958b\u59cb\u6e32\u67d3", None))
#if QT_CONFIG(tooltip)
        self.action_start_render.setToolTip(QCoreApplication.translate("MainWindow", u"\u6839\u64da\u76ee\u524d\u8a2d\u5b9a\u555f\u52d5 GPX \u52d5\u756b\u6e32\u67d3\u7a0b\u5e8f [Ctrl+R / F5]", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.action_start_render.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+R", None))
#endif // QT_CONFIG(shortcut)
        self.action_stop_render.setText(QCoreApplication.translate("MainWindow", u"\u505c\u6b62\u6e32\u67d3", None))
#if QT_CONFIG(tooltip)
        self.action_stop_render.setToolTip(QCoreApplication.translate("MainWindow", u"\u7d42\u6b62\u7576\u524d\u6b63\u5728\u57f7\u884c\u7684\u6e32\u67d3\u6216\u6e2c\u8a66\u7a0b\u5e8f [Esc]", None))
#endif // QT_CONFIG(tooltip)
        self.action_help_shortcuts.setText(QCoreApplication.translate("MainWindow", u"\u5feb\u6377\u9375\u8207\u4f7f\u7528\u624b\u518a...", None))
#if QT_CONFIG(shortcut)
        self.action_help_shortcuts.setShortcut(QCoreApplication.translate("MainWindow", u"F1", None))
#endif // QT_CONFIG(shortcut)
        self.action_about.setText(QCoreApplication.translate("MainWindow", u"\u95dc\u65bc GPX Ride Renderer...", None))
        self.groupBox_files.setTitle(QCoreApplication.translate("MainWindow", u"\u6a94\u6848", None))
        self.lbl_gpx.setText(QCoreApplication.translate("MainWindow", u"GPX \u6a94\u6848", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_gpx.setToolTip(QCoreApplication.translate("MainWindow", u"\u9078\u64c7\u6b32\u6e32\u67d3\u7684 GPX \u8ecc\u8de1\u8def\u5f91\u6a94\u6848 (.gpx)", None))
#endif // QT_CONFIG(tooltip)
        self.btn_browse_gpx.setText(QCoreApplication.translate("MainWindow", u"\u700f\u89bd\u2026", None))
        self.lbl_output.setText(QCoreApplication.translate("MainWindow", u"\u8f38\u51fa\u5f71\u7247", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_output.setToolTip(QCoreApplication.translate("MainWindow", u"\u6307\u5b9a\u8f38\u51fa\u7684 MP4 \u5f71\u7247\u6a94\u540d\u8207\u8cc7\u6599\u593e\u8def\u5f91", None))
#endif // QT_CONFIG(tooltip)
        self.btn_browse_output.setText(QCoreApplication.translate("MainWindow", u"\u700f\u89bd\u2026", None))
#if QT_CONFIG(tooltip)
        self.lbl_media.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u9078\u64c7\u5305\u542b\u7167\u7247\u6216\u5f71\u7247\u7684\u8cc7\u6599\u593e\u6216\u6a94\u6848\u3002\u7a0b\u5f0f\u6703\u81ea\u52d5\u8b80\u53d6 EXIF \u6642\u9593\u8207 GPS \u5ea7\u6a19\u9ede\u63d2\u5165\u6642\u9593\u8ef8\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_media.setText(QCoreApplication.translate("MainWindow", u"\u8def\u7dda\u5a92\u9ad4", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_media.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u9078\u64c7\u5305\u542b\u7167\u7247\u6216\u5f71\u7247\u7684\u8cc7\u6599\u593e\u6216\u6a94\u6848\u3002\u7a0b\u5f0f\u6703\u81ea\u52d5\u8b80\u53d6 EXIF \u6642\u9593\u8207 GPS \u5ea7\u6a19\u9ede\u63d2\u5165\u6642\u9593\u8ef8\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.btn_browse_media.setText(QCoreApplication.translate("MainWindow", u"\u700f\u89bd\u2026", None))
        self.btn_media_dialog.setText(QCoreApplication.translate("MainWindow", u"\u5a92\u9ad4\u7ba1\u7406", None))
        self.groupBox_settings_2.setTitle(QCoreApplication.translate("MainWindow", u"\u6e32\u67d3\u8a2d\u5b9a", None))
#if QT_CONFIG(tooltip)
        self.chk_parallel_2.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u5141\u8a31\u540c\u6642\u555f\u52d5\u591a\u500b worker \u5e73\u884c\u6e32\u67d3\u4e3b\u52d5\u756b\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.chk_parallel_2.setText(QCoreApplication.translate("MainWindow", u"\u591a\u7a0b\u5e8f", None))
#if QT_CONFIG(tooltip)
        self.chk_real_speed_2.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u63a7\u5236\u9a0e\u4e58\u52d5\u756b\u5728\u8def\u7dda\u4e0a\u7684\u79fb\u52d5\u901f\u5ea6\u6a21\u5f0f\uff08\u7b49\u901f vs \u5be6\u969b GPS \u901f\u5ea6\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.chk_real_speed_2.setText(QCoreApplication.translate("MainWindow", u"\u8ddf\u96a8 GPX \u5be6\u969b\u901f\u5ea6", None))
#if QT_CONFIG(tooltip)
        self.chk_enable_media_2.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u662f\u5426\u5728\u8def\u7dda\u52d5\u756b\u4e2d\u986f\u793a\u76f8\u7247/\u5f71\u7247\u61f8\u6d6e\u5361\u7247\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.chk_enable_media_2.setText(QCoreApplication.translate("MainWindow", u"\u8def\u7dda\u5a92\u9ad4\u5361\u7247", None))
#if QT_CONFIG(tooltip)
        self.lbl_map_style_2.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u6c7a\u5b9a\u5f71\u7247\u4e3b\u756b\u9762\u8207\u7d50\u5c3e overview \u4f7f\u7528\u7684\u5e95\u5716\u6a23\u5f0f\u3002\n"
"\u5efa\u8b70\uff1a\u6df1\u8272\u8def\u7dda\u53ef\u7528 DarkMatter\uff0c\u9053\u8def\u7d30\u7bc0\u53ef\u7528 Voyager\uff0c\u885b\u661f\u5716\u8cc7\u8a0a\u91cf\u6700\u9ad8\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_map_style_2.setText(QCoreApplication.translate("MainWindow", u"\u5730\u5716\u98a8\u683c", None))
#if QT_CONFIG(tooltip)
        self.combo_map_style_2.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u6c7a\u5b9a\u5f71\u7247\u4e3b\u756b\u9762\u8207\u7d50\u5c3e overview \u4f7f\u7528\u7684\u5e95\u5716\u6a23\u5f0f\u3002\n"
"\u5efa\u8b70\uff1a\u6df1\u8272\u8def\u7dda\u53ef\u7528 DarkMatter\uff0c\u9053\u8def\u7d30\u7bc0\u53ef\u7528 Voyager\uff0c\u885b\u661f\u5716\u8cc7\u8a0a\u91cf\u6700\u9ad8\u3002", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.lbl_panels.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u63a7\u5236\u662f\u5426\u5728\u52d5\u756b\u4e3b\u756b\u9762\u4e2d\u986f\u793a\u901f\u5ea6\u5100\u8868\u3001\u8def\u7dda\u7e2e\u5716\u6216\u6d77\u62d4\u9ad8\u5ea6\u5256\u9762\u5716\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_panels.setText(QCoreApplication.translate("MainWindow", u"\u8cc7\u8a0a\u9762\u677f", None))
#if QT_CONFIG(tooltip)
        self.chk_show_speed.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u63a7\u5236\u662f\u5426\u5728\u756b\u9762\u5de6\u4e0a\u89d2\u986f\u793a\u5373\u6642\u901f\u5ea6\u8207\u6578\u64da\u9762\u677f\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.chk_show_speed.setText(QCoreApplication.translate("MainWindow", u"\u901f\u5ea6\u9762\u677f", None))
#if QT_CONFIG(tooltip)
        self.chk_show_minimap.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u63a7\u5236\u662f\u5426\u5728\u756b\u9762\u53f3\u4e0a\u89d2\u986f\u793a\u8def\u7dda\u7e2e\u5716\u8207\u9032\u5ea6\u9762\u677f\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.chk_show_minimap.setText(QCoreApplication.translate("MainWindow", u"\u8def\u7dda\u7e2e\u5716", None))
#if QT_CONFIG(tooltip)
        self.chk_show_elevation.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u63a7\u5236\u662f\u5426\u5728\u756b\u9762\u4e0b\u65b9\u986f\u793a\u5168\u666f\u9ad8\u5ea6\u5256\u9762\u5716\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.chk_show_elevation.setText(QCoreApplication.translate("MainWindow", u"\u6d77\u62d4\u5716", None))
#if QT_CONFIG(tooltip)
        self.lbl_camera_mode_2.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u6c7a\u5b9a\u8def\u7dda\u52d5\u756b\u7684\u93e1\u982d\u8996\u89d2\u671d\u5411\u8207 3D \u5730\u5f62\u900f\u8996\u3002\n"
"\u2022 \u6b63\u5317\u671d\u4e0a (North-Up)\n"
"\u2022 \u8ddf\u96a8\u884c\u9032\u65b9\u5411 (Heading-Up)\n"
"\u2022 3D \u771f\u5730\u5f62 (3D-Terrain)", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_camera_mode_2.setText(QCoreApplication.translate("MainWindow", u"\u8996\u89d2\u6a21\u5f0f", None))
#if QT_CONFIG(tooltip)
        self.combo_camera_mode_2.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u6c7a\u5b9a\u8def\u7dda\u52d5\u756b\u7684\u93e1\u982d\u8996\u89d2\u671d\u5411\u8207 3D \u5730\u5f62\u900f\u8996\u3002\n"
"\u2022 \u6b63\u5317\u671d\u4e0a (North-Up)\n"
"\u2022 \u8ddf\u96a8\u884c\u9032\u65b9\u5411 (Heading-Up)\n"
"\u2022 3D \u771f\u5730\u5f62 (3D-Terrain)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.chk_dynamic_speed_zoom.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u6839\u64da\u7576\u524d GPX \u9a0e\u4e58\u901f\u5ea6\u52d5\u614b\u7e2e\u653e\u93e1\u982d\uff08\u9ad8\u901f\u62c9\u9060\u3001\u4f4e\u901f\u62c9\u8fd1\uff09\uff0c\u5982\u540c\u8eca\u7528\u5c0e\u822a\u8996\u89ba\u6548\u679c\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.chk_dynamic_speed_zoom.setText(QCoreApplication.translate("MainWindow", u"\u901f\u5ea6\u52d5\u614b\u93e1\u982d", None))
#if QT_CONFIG(tooltip)
        self.lbl_resolution_2.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u9078\u64c7\u8f38\u51fa\u5f71\u7247\u7684\u89e3\u6790\u5ea6\u5c3a\u5bf8\u8207\u756b\u9762\u6bd4\u4f8b\uff089:16, 16:9, 1:1 \u7b49\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_resolution_2.setText(QCoreApplication.translate("MainWindow", u"\u89e3\u6790\u5ea6\u9810\u8a2d", None))
#if QT_CONFIG(tooltip)
        self.combo_resolution_2.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u9078\u64c7\u8f38\u51fa\u5f71\u7247\u7684\u89e3\u6790\u5ea6\u5c3a\u5bf8\u8207\u756b\u9762\u6bd4\u4f8b\uff089:16, 16:9, 1:1 \u7b49\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.chk_basemap_2.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u662f\u5426\u4e0b\u8f09\u4e26\u986f\u793a\u9053\u8def\u6216\u885b\u661f\u7b49\u5730\u5716\u5e95\u5716\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.chk_basemap_2.setText(QCoreApplication.translate("MainWindow", u"\u5e95\u5716", None))
#if QT_CONFIG(tooltip)
        self.lbl_profile_2.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u4e00\u6b21\u5957\u7528\u4e00\u7d44\u89e3\u6790\u5ea6\u3001Local Zoom\u3001bitrate\u3001NVENC preset\u3001Workers \u8207 Chunks/Worker\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_profile_2.setText(QCoreApplication.translate("MainWindow", u"\u9810\u8a2d\u6a21\u5f0f", None))
#if QT_CONFIG(tooltip)
        self.combo_profile_2.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u4e00\u6b21\u5957\u7528\u4e00\u7d44\u89e3\u6790\u5ea6\u3001Local Zoom\u3001bitrate\u3001NVENC preset\u3001Workers \u8207 Chunks/Worker\u3002", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.lbl_track_color_2.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u63a7\u5236\u4e3b\u756b\u9762\u8ecc\u8de1\u7dda\u689d\u8207\u5347\u964d\u5f69\u5e36\u7684\u914d\u8272\u98a8\u683c\u3002\n"
"\u2022 \u6d77\u62d4\u52d5\u614b\u6f38\u5c64\n"
"\u2022 \u4eae\u7da0\u3001\u9ec3\u3001\u7d05\u55ae\u8272\n"
"\u2022 \u9a0e\u4e58\u901f\u5ea6\u6f38\u5c64", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_track_color_2.setText(QCoreApplication.translate("MainWindow", u"\u8ecc\u8de1\u984f\u8272", None))
#if QT_CONFIG(tooltip)
        self.combo_track_color_2.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u63a7\u5236\u4e3b\u756b\u9762\u8ecc\u8de1\u7dda\u689d\u8207\u5347\u964d\u5f69\u5e36\u7684\u914d\u8272\u98a8\u683c\u3002\n"
"\u2022 \u6d77\u62d4\u52d5\u614b\u6f38\u5c64\n"
"\u2022 \u4eae\u7da0\u3001\u9ec3\u3001\u7d05\u55ae\u8272\n"
"\u2022 \u9a0e\u4e58\u901f\u5ea6\u6f38\u5c64", None))
#endif // QT_CONFIG(tooltip)
        self.groupBox_summary.setTitle(QCoreApplication.translate("MainWindow", u"\u6e32\u67d3\u8a2d\u5b9a\u6458\u8981", None))
        self.label_cfg_map.setText(QCoreApplication.translate("MainWindow", u"\u5730\u5716\u8996\u89d2: \u98a8\u683c [1] | North-Up | Zoom: 17", None))
        self.label_cfg_enc.setText(QCoreApplication.translate("MainWindow", u"\u7de8\u78bc\u8a2d\u5b9a: NVENC 30M (preset: p5) | \u7121\u5a92\u9ad4 Overlay", None))
        self.label_cfg_res.setText(QCoreApplication.translate("MainWindow", u"\u756b\u9762\u898f\u683c: 1440x1440 @ 60 FPS (\u81ea\u52d5\u6642\u9577 20.0s)", None))
        self.label_cfg_perf.setText(QCoreApplication.translate("MainWindow", u"\u6548\u80fd\u6a21\u5f0f: \u591a\u7a0b\u5e8f (6 Workers \u00d7 4 chunks) | \u505c\u7528 Cache", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_general), QCoreApplication.translate("MainWindow", u"\u4e00\u822c\u8a2d\u5b9a", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"\u9032\u968e\u8a2d\u5b9a", None))
#if QT_CONFIG(tooltip)
        self.lbl_custom_res.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u9078\u64c7\u8f38\u51fa\u5f71\u7247\u7684\u89e3\u6790\u5ea6\u5c3a\u5bf8\u8207\u756b\u9762\u6bd4\u4f8b\uff089:16, 16:9, 1:1 \u7b49\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_custom_res.setText(QCoreApplication.translate("MainWindow", u"\u81ea\u8a02\u89e3\u6790\u5ea6", None))
        self.lbl_x.setText(QCoreApplication.translate("MainWindow", u"\u00d7", None))
#if QT_CONFIG(tooltip)
        self.lbl_view_margin.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u63a7\u5236\u4e3b\u52d5\u756b\u93e1\u982d\u5728\u6469\u6258\u8eca\u4f4d\u7f6e\u5468\u570d\u4e00\u6b21\u770b\u591a\u5927\u7684\u5be6\u969b\u5730\u7406\u7bc4\u570d\uff08\u516c\u5c3a\uff0c\u9810\u8a2d 1600\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_view_margin.setText(QCoreApplication.translate("MainWindow", u"View Margin", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_view_margin.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u63a7\u5236\u4e3b\u52d5\u756b\u93e1\u982d\u5728\u6469\u6258\u8eca\u4f4d\u7f6e\u5468\u570d\u4e00\u6b21\u770b\u591a\u5927\u7684\u5be6\u969b\u5730\u7406\u7bc4\u570d\uff08\u516c\u5c3a\uff0c\u9810\u8a2d 1600\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_view_margin.setText(QCoreApplication.translate("MainWindow", u"1600", None))
#if QT_CONFIG(tooltip)
        self.lbl_local_zoom.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u6c7a\u5b9a\u4e3b\u52d5\u756b\u5c40\u90e8\u5e95\u5716\u4e0b\u8f09\u7684\u5730\u5716\u7e2e\u653e\u5c64\u7d1a\uff08\u9810\u8a2d 17 \u6216 auto\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_local_zoom.setText(QCoreApplication.translate("MainWindow", u"Local Zoom", None))
#if QT_CONFIG(tooltip)
        self.combo_local_zoom.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u6c7a\u5b9a\u4e3b\u52d5\u756b\u5c40\u90e8\u5e95\u5716\u4e0b\u8f09\u7684\u5730\u5716\u7e2e\u653e\u5c64\u7d1a\uff08\u9810\u8a2d 17 \u6216 auto\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.lbl_preset.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u63a7\u5236 NVIDIA NVENC \u901f\u5ea6\u8207\u54c1\u8cea\u53d6\u6368\uff08\u9810\u8a2d p5\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_preset.setText(QCoreApplication.translate("MainWindow", u"NVENC Preset", None))
#if QT_CONFIG(tooltip)
        self.combo_preset.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u63a7\u5236 NVIDIA NVENC \u901f\u5ea6\u8207\u54c1\u8cea\u53d6\u6368\uff08\u9810\u8a2d p5\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.lbl_fps.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u8a2d\u5b9a\u8f38\u51fa\u5f71\u7247\u6bcf\u79d2\u5305\u542b\u591a\u5c11\u5e40\uff08\u9810\u8a2d 60 FPS\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_fps.setText(QCoreApplication.translate("MainWindow", u"FPS (\u5e40\u7387)", None))
#if QT_CONFIG(tooltip)
        self.spin_fps.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u8a2d\u5b9a\u8f38\u51fa\u5f71\u7247\u6bcf\u79d2\u5305\u542b\u591a\u5c11\u5e40\uff08\u9810\u8a2d 60 FPS\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.lbl_zoomout.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u4e3b\u52d5\u756b\u8dd1\u5b8c\u5f8c\uff0c\u93e1\u982d\u5f9e\u5c40\u90e8\u8996\u89d2\u62c9\u9060\u5230\u5b8c\u6574\u8def\u7dda overview \u6240\u82b1\u7684\u6642\u9593\uff08\u79d2\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_zoomout.setText(QCoreApplication.translate("MainWindow", u"Zoom-out \u79d2", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_zoomout.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u4e3b\u52d5\u756b\u8dd1\u5b8c\u5f8c\uff0c\u93e1\u982d\u5f9e\u5c40\u90e8\u8996\u89d2\u62c9\u9060\u5230\u5b8c\u6574\u8def\u7dda overview \u6240\u82b1\u7684\u6642\u9593\uff08\u79d2\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_zoomout.setText(QCoreApplication.translate("MainWindow", u"2.5", None))
#if QT_CONFIG(tooltip)
        self.lbl_end_hold.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u5b8c\u6574\u8def\u5f91\u8207 RIDE STATS \u51fa\u73fe\u5f8c\uff0c\u756b\u9762\u7dad\u6301\u591a\u4e45\u518d\u7d50\u675f\u5f71\u7247\uff08\u79d2\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_end_hold.setText(QCoreApplication.translate("MainWindow", u"\u7d50\u5c3e\u505c\u7559\u79d2", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_end_hold.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u5b8c\u6574\u8def\u5f91\u8207 RIDE STATS \u51fa\u73fe\u5f8c\uff0c\u756b\u9762\u7dad\u6301\u591a\u4e45\u518d\u7d50\u675f\u5f71\u7247\uff08\u79d2\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_end_hold.setText(QCoreApplication.translate("MainWindow", u"4.0", None))
#if QT_CONFIG(tooltip)
        self.lbl_bitrate.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u8a2d\u5b9a H.264 NVENC \u8f38\u51fa\u78bc\u7387\uff08\u9810\u8a2d 30M\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_bitrate.setText(QCoreApplication.translate("MainWindow", u"NVENC \u6bd4\u7279\u7387", None))
#if QT_CONFIG(tooltip)
        self.combo_bitrate.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u8a2d\u5b9a H.264 NVENC \u8f38\u51fa\u78bc\u7387\uff08\u9810\u8a2d 30M\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.chk_auto_duration.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u4f9d GPX \u7e3d\u8ddd\u96e2\u81ea\u52d5\u8a08\u7b97\u4e3b\u52d5\u756b\u9577\u5ea6\uff0c\u8b93\u4e0d\u540c\u9577\u5ea6\u7684\u9a0e\u4e58\u8def\u7dda\u4fdd\u6301\u76f8\u8fd1\u7bc0\u594f\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.chk_auto_duration.setText(QCoreApplication.translate("MainWindow", u"\u4f9d GPX \u8ddd\u96e2\u81ea\u52d5\u6642\u9577", None))
#if QT_CONFIG(tooltip)
        self.lbl_rate.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u81ea\u52d5\u6642\u9577\u7684\u7bc0\u594f\u500d\u7387\u3002\u516c\u5f0f\u7d04\u70ba\uff1a\u8ddd\u96e2 km \u00f7 100 \u00d7 \u6b64\u6578\u503c\uff08\u9810\u8a2d 60 \u79d2/100km\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_rate.setText(QCoreApplication.translate("MainWindow", u"\u81ea\u52d5\u6642\u9577\u500d\u7387", None))
        self.lbl_rate_unit.setText(QCoreApplication.translate("MainWindow", u"\u79d2 / 100km", None))
#if QT_CONFIG(tooltip)
        self.lbl_duration.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u63a7\u5236\u6469\u6258\u8eca\u6cbf GPX \u8def\u5f91\u64ad\u653e\u7684\u4e3b\u52d5\u756b\u9577\u5ea6\uff08\u79d2\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_duration.setText(QCoreApplication.translate("MainWindow", u"\u4e3b\u52d5\u756b\u79d2\u6578", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_duration.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u63a7\u5236\u6469\u6258\u8eca\u6cbf GPX \u8def\u5f91\u64ad\u653e\u7684\u4e3b\u52d5\u756b\u9577\u5ea6\uff08\u79d2\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.label_distance_info.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u4f9d GPX \u7e3d\u8ddd\u96e2\u81ea\u52d5\u8a08\u7b97\u4e3b\u52d5\u756b\u9577\u5ea6\uff0c\u8b93\u4e0d\u540c\u9577\u5ea6\u7684\u9a0e\u4e58\u8def\u7dda\u4fdd\u6301\u76f8\u8fd1\u7bc0\u594f\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.label_distance_info.setText(QCoreApplication.translate("MainWindow", u"GPX \u8ddd\u96e2\uff1a-- km (\u81ea\u52d5\u6642\u9577 --s)", None))
#if QT_CONFIG(tooltip)
        self.chk_preview.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u53ea\u6e32\u67d3\u4e00\u5c0f\u6bb5\u4e3b\u52d5\u756b\uff0c\u5feb\u901f\u6aa2\u67e5 HUD\u3001\u8def\u5f91\u3001\u5730\u5716\u8207\u756b\u8cea\u8a2d\u5b9a\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.chk_preview.setText(QCoreApplication.translate("MainWindow", u"Preview \u9810\u89bd\u6a21\u5f0f", None))
#if QT_CONFIG(tooltip)
        self.combo_cache_mode.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u5207\u63db\u5e95\u5716\u78c1\u789f\u5feb\u53d6\u6a21\u5f0f\u3002\u81ea\u52d5\u66ab\u5b58\u6a21\u5f0f\u65bc\u95dc\u9589\u7a0b\u5f0f\u6642\u6e05\u9664\uff1b\u6c38\u4e45\u4fdd\u7559\u6a21\u5f0f\u5247\u4fdd\u7559\u4ee5\u52a0\u901f\u65e5\u5f8c\u6e32\u67d3\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_cache_size.setText(QCoreApplication.translate("MainWindow", u"\u5feb\u53d6: 0.0 MB", None))
        self.btn_clear_cache.setText(QCoreApplication.translate("MainWindow", u"\u6e05\u9664\u5feb\u53d6", None))
#if QT_CONFIG(tooltip)
        self.lbl_hide_privacy.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u63a7\u5236\u4e3b\u52d5\u756b\u524d\u6bb5\u96b1\u85cf\u7684 GPX \u8ecc\u8de1\u8ddd\u96e2 (0~50 km)\uff0c\u4fdd\u8b77\u8d77\u9ede\u96b1\u79c1\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_hide_privacy.setText(QCoreApplication.translate("MainWindow", u"\u96b1\u85cf", None))
        self.lbl_hide_start.setText(QCoreApplication.translate("MainWindow", u"\u8d77\u9ede", None))
        self.lbl_hide_end.setText(QCoreApplication.translate("MainWindow", u"k | \u7d42 ", None))
        self.lbl_hide_unit.setText(QCoreApplication.translate("MainWindow", u"k", None))
#if QT_CONFIG(tooltip)
        self.lbl_workers_chunks.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u540c\u6642\u4f7f\u7528\u591a\u5c11\u500b\u7368\u7acb\u6e32\u67d3\u7a0b\u5e8f\u8655\u7406\u4e0d\u540c chunks\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_workers_chunks.setText(QCoreApplication.translate("MainWindow", u"Workers / Chunks", None))
        self.lbl_wc_x.setText(QCoreApplication.translate("MainWindow", u" W \u00d7 ", None))
        self.lbl_wc_unit.setText(QCoreApplication.translate("MainWindow", u" C", None))
#if QT_CONFIG(tooltip)
        self.lbl_tile_connections.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1acontextily \u4e0b\u8f09\u5730\u5716 tile \u6642\u53ef\u540c\u6642\u4f7f\u7528\u7684\u9023\u7dda\u6578\uff08\u9810\u8a2d 4\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_tile_connections.setText(QCoreApplication.translate("MainWindow", u"Tile \u9023\u7dda\u6578", None))
#if QT_CONFIG(tooltip)
        self.spin_tile_connections.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1acontextily \u4e0b\u8f09\u5730\u5716 tile \u6642\u53ef\u540c\u6642\u4f7f\u7528\u7684\u9023\u7dda\u6578\uff08\u9810\u8a2d 4\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.btn_autotune.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u7528\u77ed benchmark \u5be6\u6e2c\u4e0d\u540c Workers \u6578\u91cf\u7684\u7b49\u6548 FPS\uff0c\u518d\u63a8\u85a6\u63a5\u8fd1\u5cf0\u503c\u6548\u80fd\u7684\u6700\u4f4e worker \u6578\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.btn_autotune.setText(QCoreApplication.translate("MainWindow", u"\u6548\u80fd\u6e2c\u8a66 / Auto Tune", None))
#if QT_CONFIG(tooltip)
        self.label_autotune_result.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u7528\u77ed benchmark \u5be6\u6e2c\u4e0d\u540c Workers \u6578\u91cf\u7684\u7b49\u6548 FPS\uff0c\u518d\u63a8\u85a6\u63a5\u8fd1\u5cf0\u503c\u6548\u80fd\u7684\u6700\u4f4e worker \u6578\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.label_autotune_result.setText(QCoreApplication.translate("MainWindow", u"\u5c1a\u672a\u6e2c\u8a66", None))
        self.btn_apply_benchmark.setText(QCoreApplication.translate("MainWindow", u"\u5957\u7528\u5efa\u8b70", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_advanced), QCoreApplication.translate("MainWindow", u"\u9032\u968e\u8a2d\u5b9a", None))
        self.groupBox_workers.setTitle(QCoreApplication.translate("MainWindow", u"\u6e32\u67d3\u9032\u5ea6", None))
        self.label_eta_elapsed.setText(QCoreApplication.translate("MainWindow", u"\u6e32\u67d3\u8a08\u6642: 00:00:00", None))
        self.label_eta_time.setText(QCoreApplication.translate("MainWindow", u"\u9810\u4f30\u5269\u9918\u6642\u9593: --", None))
        self.label_eta_clock.setText(QCoreApplication.translate("MainWindow", u"\u9810\u8a08\u5b8c\u6210\u6642\u523b: --:--:--", None))
        self.label_eta_frames.setText(QCoreApplication.translate("MainWindow", u"\u5df2\u5b8c\u6210\u5e40\u6578: 0 / 0", None))
        self.label_eta_speed.setText(QCoreApplication.translate("MainWindow", u"\u6e32\u67d3\u901f\u5ea6: -- frame/s", None))
        self.lbl_worker_1.setText(QCoreApplication.translate("MainWindow", u"Worker 1:", None))
        self.lbl_worker_status_1.setText(QCoreApplication.translate("MainWindow", u"\u5f85\u547d", None))
        self.lbl_worker_4.setText(QCoreApplication.translate("MainWindow", u"Worker 4:", None))
        self.lbl_worker_status_4.setText(QCoreApplication.translate("MainWindow", u"\u5f85\u547d", None))
        self.lbl_worker_2.setText(QCoreApplication.translate("MainWindow", u"Worker 2:", None))
        self.lbl_worker_status_2.setText(QCoreApplication.translate("MainWindow", u"\u5f85\u547d", None))
        self.lbl_worker_5.setText(QCoreApplication.translate("MainWindow", u"Worker 5:", None))
        self.lbl_worker_status_5.setText(QCoreApplication.translate("MainWindow", u"\u5f85\u547d", None))
        self.lbl_worker_3.setText(QCoreApplication.translate("MainWindow", u"Worker 3:", None))
        self.lbl_worker_status_3.setText(QCoreApplication.translate("MainWindow", u"\u5f85\u547d", None))
        self.lbl_worker_6.setText(QCoreApplication.translate("MainWindow", u"Worker 6:", None))
        self.lbl_worker_status_6.setText(QCoreApplication.translate("MainWindow", u"\u5f85\u547d", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_workers), QCoreApplication.translate("MainWindow", u"\u6e32\u67d3\u9032\u5ea6", None))
        self.btn_start_render.setText(QCoreApplication.translate("MainWindow", u"\u958b\u59cb\u6e32\u67d3", None))
        self.btn_stop_render.setText(QCoreApplication.translate("MainWindow", u"\u505c\u6b62", None))
        self.menu_file.setTitle(QCoreApplication.translate("MainWindow", u"\u6a94\u6848(&F)", None))
        self.menu_edit.setTitle(QCoreApplication.translate("MainWindow", u"\u7de8\u8f2f\u8207\u5de5\u5177(&E)", None))
        self.menu_view.setTitle(QCoreApplication.translate("MainWindow", u"\u6aa2\u8996(&V)", None))
        self.menu_settings.setTitle(QCoreApplication.translate("MainWindow", u"\u8a2d\u5b9a(&S)", None))
        self.menu_profile.setTitle(QCoreApplication.translate("MainWindow", u"\u9810\u8a2d\u756b\u8cea\u98a8\u683c", None))
        self.menu_hud_panels.setTitle(QCoreApplication.translate("MainWindow", u"\u8cc7\u8a0a\u9762\u677f", None))
        self.menu_cache_mode.setTitle(QCoreApplication.translate("MainWindow", u"\u5730\u5716\u5feb\u53d6\u6a21\u5f0f", None))
        self.menu_help.setTitle(QCoreApplication.translate("MainWindow", u"\u8aaa\u660e(&H)", None))
        self.toolBar.setWindowTitle(QCoreApplication.translate("MainWindow", u"\u5feb\u6377\u5de5\u5177\u5217", None))
    # retranslateUi

