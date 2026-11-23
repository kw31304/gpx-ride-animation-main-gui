# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_windowMWMByF.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox,
    QDoubleSpinBox, QFrame, QGridLayout, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMainWindow, QMenu, QMenuBar, QPushButton,
    QSizePolicy, QSpacerItem, QSpinBox, QSplitter,
    QTabWidget, QTableWidget, QTableWidgetItem, QToolBar,
    QVBoxLayout, QWidget)

from gpx_renderer.gui.media_dialog.widgets.clickable_preview import ClickablePreviewLabel
from gpx_renderer.gui.media_dialog.widgets.route_preview_widget import QtRoutePreviewWidget
from gpx_renderer.gui.widgets.checkable_combo_box import CheckableComboBox
from gpx_renderer.gui.widgets.py_circular_progress import PyCircularProgress

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1150, 819)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setMinimumSize(QSize(0, 0))
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
        self.action_preset_p1 = QAction(MainWindow)
        self.action_preset_p1.setObjectName(u"action_preset_p1")
        self.action_preset_p1.setCheckable(True)
        self.action_preset_p2 = QAction(MainWindow)
        self.action_preset_p2.setObjectName(u"action_preset_p2")
        self.action_preset_p2.setCheckable(True)
        self.action_preset_p3 = QAction(MainWindow)
        self.action_preset_p3.setObjectName(u"action_preset_p3")
        self.action_preset_p3.setCheckable(True)
        self.action_preset_p4 = QAction(MainWindow)
        self.action_preset_p4.setObjectName(u"action_preset_p4")
        self.action_preset_p4.setCheckable(True)
        self.action_preset_p4.setChecked(True)
        self.action_preset_p5 = QAction(MainWindow)
        self.action_preset_p5.setObjectName(u"action_preset_p5")
        self.action_preset_p5.setCheckable(True)
        self.action_preset_p6 = QAction(MainWindow)
        self.action_preset_p6.setObjectName(u"action_preset_p6")
        self.action_preset_p6.setCheckable(True)
        self.action_preset_p7 = QAction(MainWindow)
        self.action_preset_p7.setObjectName(u"action_preset_p7")
        self.action_preset_p7.setCheckable(True)
        self.action_bitrate_8M = QAction(MainWindow)
        self.action_bitrate_8M.setObjectName(u"action_bitrate_8M")
        self.action_bitrate_8M.setCheckable(True)
        self.action_bitrate_12M = QAction(MainWindow)
        self.action_bitrate_12M.setObjectName(u"action_bitrate_12M")
        self.action_bitrate_12M.setCheckable(True)
        self.action_bitrate_20M = QAction(MainWindow)
        self.action_bitrate_20M.setObjectName(u"action_bitrate_20M")
        self.action_bitrate_20M.setCheckable(True)
        self.action_bitrate_20M.setChecked(True)
        self.action_bitrate_24M = QAction(MainWindow)
        self.action_bitrate_24M.setObjectName(u"action_bitrate_24M")
        self.action_bitrate_24M.setCheckable(True)
        self.action_bitrate_30M = QAction(MainWindow)
        self.action_bitrate_30M.setObjectName(u"action_bitrate_30M")
        self.action_bitrate_30M.setCheckable(True)
        self.action_bitrate_40M = QAction(MainWindow)
        self.action_bitrate_40M.setObjectName(u"action_bitrate_40M")
        self.action_bitrate_40M.setCheckable(True)
        self.action_bitrate_60M = QAction(MainWindow)
        self.action_bitrate_60M.setObjectName(u"action_bitrate_60M")
        self.action_bitrate_60M.setCheckable(True)
        self.action_workers_2 = QAction(MainWindow)
        self.action_workers_2.setObjectName(u"action_workers_2")
        self.action_workers_2.setCheckable(True)
        self.action_workers_4 = QAction(MainWindow)
        self.action_workers_4.setObjectName(u"action_workers_4")
        self.action_workers_4.setCheckable(True)
        self.action_workers_6 = QAction(MainWindow)
        self.action_workers_6.setObjectName(u"action_workers_6")
        self.action_workers_6.setCheckable(True)
        self.action_workers_6.setChecked(True)
        self.action_workers_8 = QAction(MainWindow)
        self.action_workers_8.setObjectName(u"action_workers_8")
        self.action_workers_8.setCheckable(True)
        self.action_workers_12 = QAction(MainWindow)
        self.action_workers_12.setObjectName(u"action_workers_12")
        self.action_workers_12.setCheckable(True)
        self.action_workers_16 = QAction(MainWindow)
        self.action_workers_16.setObjectName(u"action_workers_16")
        self.action_workers_16.setCheckable(True)
        self.action_tile_conn_4 = QAction(MainWindow)
        self.action_tile_conn_4.setObjectName(u"action_tile_conn_4")
        self.action_tile_conn_4.setCheckable(True)
        self.action_tile_conn_8 = QAction(MainWindow)
        self.action_tile_conn_8.setObjectName(u"action_tile_conn_8")
        self.action_tile_conn_8.setCheckable(True)
        self.action_tile_conn_16 = QAction(MainWindow)
        self.action_tile_conn_16.setObjectName(u"action_tile_conn_16")
        self.action_tile_conn_16.setCheckable(True)
        self.action_tile_conn_16.setChecked(True)
        self.action_tile_conn_24 = QAction(MainWindow)
        self.action_tile_conn_24.setObjectName(u"action_tile_conn_24")
        self.action_tile_conn_24.setCheckable(True)
        self.action_tile_conn_32 = QAction(MainWindow)
        self.action_tile_conn_32.setObjectName(u"action_tile_conn_32")
        self.action_tile_conn_32.setCheckable(True)
        self.action_custom_resolution = QAction(MainWindow)
        self.action_custom_resolution.setObjectName(u"action_custom_resolution")
        self.action_advanced_settings = QAction(MainWindow)
        self.action_advanced_settings.setObjectName(u"action_advanced_settings")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout_8 = QGridLayout(self.centralwidget)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setMinimumSize(QSize(0, 0))
        self.tab_general = QWidget()
        self.tab_general.setObjectName(u"tab_general")
        self.gridLayout_7 = QGridLayout(self.tab_general)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.splitter_2 = QSplitter(self.tab_general)
        self.splitter_2.setObjectName(u"splitter_2")
        self.splitter_2.setOrientation(Qt.Orientation.Horizontal)
        self.layoutWidget = QWidget(self.splitter_2)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.verticalLayout_27 = QVBoxLayout(self.layoutWidget)
        self.verticalLayout_27.setObjectName(u"verticalLayout_27")
        self.verticalLayout_27.setContentsMargins(0, 0, 0, 0)
        self.groupBox_files = QGroupBox(self.layoutWidget)
        self.groupBox_files.setObjectName(u"groupBox_files")
        sizePolicy.setHeightForWidth(self.groupBox_files.sizePolicy().hasHeightForWidth())
        self.groupBox_files.setSizePolicy(sizePolicy)
        self.groupBox_files.setMinimumSize(QSize(0, 0))
        self.verticalLayout_22 = QVBoxLayout(self.groupBox_files)
        self.verticalLayout_22.setObjectName(u"verticalLayout_22")
        self.horizontalLayout_17 = QHBoxLayout()
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.lbl_gpx = QLabel(self.groupBox_files)
        self.lbl_gpx.setObjectName(u"lbl_gpx")
        sizePolicy.setHeightForWidth(self.lbl_gpx.sizePolicy().hasHeightForWidth())
        self.lbl_gpx.setSizePolicy(sizePolicy)
        self.lbl_gpx.setMinimumSize(QSize(63, 0))
        self.lbl_gpx.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_17.addWidget(self.lbl_gpx)

        self.lineEdit_gpx = QLineEdit(self.groupBox_files)
        self.lineEdit_gpx.setObjectName(u"lineEdit_gpx")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.lineEdit_gpx.sizePolicy().hasHeightForWidth())
        self.lineEdit_gpx.setSizePolicy(sizePolicy1)
        self.lineEdit_gpx.setMinimumSize(QSize(150, 0))

        self.horizontalLayout_17.addWidget(self.lineEdit_gpx)

        self.btn_browse_gpx = QPushButton(self.groupBox_files)
        self.btn_browse_gpx.setObjectName(u"btn_browse_gpx")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.btn_browse_gpx.sizePolicy().hasHeightForWidth())
        self.btn_browse_gpx.setSizePolicy(sizePolicy2)

        self.horizontalLayout_17.addWidget(self.btn_browse_gpx)


        self.verticalLayout_22.addLayout(self.horizontalLayout_17)

        self.horizontalLayout_18 = QHBoxLayout()
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.lbl_output = QLabel(self.groupBox_files)
        self.lbl_output.setObjectName(u"lbl_output")
        sizePolicy.setHeightForWidth(self.lbl_output.sizePolicy().hasHeightForWidth())
        self.lbl_output.setSizePolicy(sizePolicy)
        self.lbl_output.setMinimumSize(QSize(63, 0))
        self.lbl_output.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_18.addWidget(self.lbl_output)

        self.lineEdit_output = QLineEdit(self.groupBox_files)
        self.lineEdit_output.setObjectName(u"lineEdit_output")
        sizePolicy1.setHeightForWidth(self.lineEdit_output.sizePolicy().hasHeightForWidth())
        self.lineEdit_output.setSizePolicy(sizePolicy1)
        self.lineEdit_output.setMinimumSize(QSize(150, 0))

        self.horizontalLayout_18.addWidget(self.lineEdit_output)

        self.btn_browse_output = QPushButton(self.groupBox_files)
        self.btn_browse_output.setObjectName(u"btn_browse_output")
        sizePolicy2.setHeightForWidth(self.btn_browse_output.sizePolicy().hasHeightForWidth())
        self.btn_browse_output.setSizePolicy(sizePolicy2)

        self.horizontalLayout_18.addWidget(self.btn_browse_output)


        self.verticalLayout_22.addLayout(self.horizontalLayout_18)

        self.horizontalLayout_21 = QHBoxLayout()
        self.horizontalLayout_21.setObjectName(u"horizontalLayout_21")
        self.lbl_media = QLabel(self.groupBox_files)
        self.lbl_media.setObjectName(u"lbl_media")
        sizePolicy.setHeightForWidth(self.lbl_media.sizePolicy().hasHeightForWidth())
        self.lbl_media.setSizePolicy(sizePolicy)
        self.lbl_media.setMinimumSize(QSize(63, 0))
        self.lbl_media.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_21.addWidget(self.lbl_media)

        self.lineEdit_media = QLineEdit(self.groupBox_files)
        self.lineEdit_media.setObjectName(u"lineEdit_media")
        sizePolicy1.setHeightForWidth(self.lineEdit_media.sizePolicy().hasHeightForWidth())
        self.lineEdit_media.setSizePolicy(sizePolicy1)
        self.lineEdit_media.setMinimumSize(QSize(150, 0))

        self.horizontalLayout_21.addWidget(self.lineEdit_media)

        self.horizontalLayout_media = QHBoxLayout()
        self.horizontalLayout_media.setObjectName(u"horizontalLayout_media")
        self.btn_browse_media = QPushButton(self.groupBox_files)
        self.btn_browse_media.setObjectName(u"btn_browse_media")
        sizePolicy2.setHeightForWidth(self.btn_browse_media.sizePolicy().hasHeightForWidth())
        self.btn_browse_media.setSizePolicy(sizePolicy2)

        self.horizontalLayout_media.addWidget(self.btn_browse_media)

        self.btn_media_dialog = QPushButton(self.groupBox_files)
        self.btn_media_dialog.setObjectName(u"btn_media_dialog")
        sizePolicy2.setHeightForWidth(self.btn_media_dialog.sizePolicy().hasHeightForWidth())
        self.btn_media_dialog.setSizePolicy(sizePolicy2)

        self.horizontalLayout_media.addWidget(self.btn_media_dialog)


        self.horizontalLayout_21.addLayout(self.horizontalLayout_media)


        self.verticalLayout_22.addLayout(self.horizontalLayout_21)


        self.verticalLayout_27.addWidget(self.groupBox_files)

        self.groupBox_summary = QGroupBox(self.layoutWidget)
        self.groupBox_summary.setObjectName(u"groupBox_summary")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.groupBox_summary.sizePolicy().hasHeightForWidth())
        self.groupBox_summary.setSizePolicy(sizePolicy3)
        self.verticalLayout_18 = QVBoxLayout(self.groupBox_summary)
        self.verticalLayout_18.setObjectName(u"verticalLayout_18")
        self.verticalLayout_17 = QVBoxLayout()
        self.verticalLayout_17.setObjectName(u"verticalLayout_17")
        self.label_cfg_res = QLabel(self.groupBox_summary)
        self.label_cfg_res.setObjectName(u"label_cfg_res")

        self.verticalLayout_17.addWidget(self.label_cfg_res)

        self.label_cfg_map = QLabel(self.groupBox_summary)
        self.label_cfg_map.setObjectName(u"label_cfg_map")

        self.verticalLayout_17.addWidget(self.label_cfg_map)

        self.label_cfg_enc = QLabel(self.groupBox_summary)
        self.label_cfg_enc.setObjectName(u"label_cfg_enc")

        self.verticalLayout_17.addWidget(self.label_cfg_enc)

        self.label_cfg_perf = QLabel(self.groupBox_summary)
        self.label_cfg_perf.setObjectName(u"label_cfg_perf")

        self.verticalLayout_17.addWidget(self.label_cfg_perf)


        self.verticalLayout_18.addLayout(self.verticalLayout_17)


        self.verticalLayout_27.addWidget(self.groupBox_summary)

        self.splitter_2.addWidget(self.layoutWidget)
        self.groupBox_settings_2 = QGroupBox(self.splitter_2)
        self.groupBox_settings_2.setObjectName(u"groupBox_settings_2")
        sizePolicy.setHeightForWidth(self.groupBox_settings_2.sizePolicy().hasHeightForWidth())
        self.groupBox_settings_2.setSizePolicy(sizePolicy)
        self.groupBox_settings_2.setMinimumSize(QSize(0, 0))
        self.groupBox_settings_2.setMaximumSize(QSize(16777215, 16777215))
        self.verticalLayout_4 = QVBoxLayout(self.groupBox_settings_2)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.lbl_resolution_2 = QLabel(self.groupBox_settings_2)
        self.lbl_resolution_2.setObjectName(u"lbl_resolution_2")
        sizePolicy2.setHeightForWidth(self.lbl_resolution_2.sizePolicy().hasHeightForWidth())
        self.lbl_resolution_2.setSizePolicy(sizePolicy2)
        self.lbl_resolution_2.setMinimumSize(QSize(60, 0))
        self.lbl_resolution_2.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_2.addWidget(self.lbl_resolution_2)

        self.combo_resolution_2 = QComboBox(self.groupBox_settings_2)
        self.combo_resolution_2.setObjectName(u"combo_resolution_2")
        sizePolicy1.setHeightForWidth(self.combo_resolution_2.sizePolicy().hasHeightForWidth())
        self.combo_resolution_2.setSizePolicy(sizePolicy1)
        self.combo_resolution_2.setMinimumSize(QSize(200, 0))

        self.horizontalLayout_2.addWidget(self.combo_resolution_2)

        self.label = QLabel(self.groupBox_settings_2)
        self.label.setObjectName(u"label")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy4)

        self.horizontalLayout_2.addWidget(self.label)

        self.spin_fps = QSpinBox(self.groupBox_settings_2)
        self.spin_fps.setObjectName(u"spin_fps")
        sizePolicy2.setHeightForWidth(self.spin_fps.sizePolicy().hasHeightForWidth())
        self.spin_fps.setSizePolicy(sizePolicy2)
        self.spin_fps.setMinimumSize(QSize(120, 0))
        self.spin_fps.setMaximumSize(QSize(16777215, 16777215))
        self.spin_fps.setValue(60)

        self.horizontalLayout_2.addWidget(self.spin_fps)


        self.verticalLayout_4.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.lbl_profile_2 = QLabel(self.groupBox_settings_2)
        self.lbl_profile_2.setObjectName(u"lbl_profile_2")
        self.lbl_profile_2.setMinimumSize(QSize(60, 0))
        self.lbl_profile_2.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_9.addWidget(self.lbl_profile_2)

        self.combo_profile_2 = QComboBox(self.groupBox_settings_2)
        self.combo_profile_2.setObjectName(u"combo_profile_2")
        sizePolicy1.setHeightForWidth(self.combo_profile_2.sizePolicy().hasHeightForWidth())
        self.combo_profile_2.setSizePolicy(sizePolicy1)
        self.combo_profile_2.setMinimumSize(QSize(180, 0))

        self.horizontalLayout_9.addWidget(self.combo_profile_2)


        self.verticalLayout_4.addLayout(self.horizontalLayout_9)

        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.lbl_map_style_2 = QLabel(self.groupBox_settings_2)
        self.lbl_map_style_2.setObjectName(u"lbl_map_style_2")
        self.lbl_map_style_2.setMinimumSize(QSize(60, 0))
        self.lbl_map_style_2.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_11.addWidget(self.lbl_map_style_2)

        self.combo_map_style_2 = QComboBox(self.groupBox_settings_2)
        self.combo_map_style_2.addItem("")
        self.combo_map_style_2.setObjectName(u"combo_map_style_2")
        sizePolicy1.setHeightForWidth(self.combo_map_style_2.sizePolicy().hasHeightForWidth())
        self.combo_map_style_2.setSizePolicy(sizePolicy1)
        self.combo_map_style_2.setMinimumSize(QSize(180, 0))

        self.horizontalLayout_11.addWidget(self.combo_map_style_2)


        self.verticalLayout_4.addLayout(self.horizontalLayout_11)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.lbl_camera_mode_2 = QLabel(self.groupBox_settings_2)
        self.lbl_camera_mode_2.setObjectName(u"lbl_camera_mode_2")
        self.lbl_camera_mode_2.setMinimumSize(QSize(60, 0))
        self.lbl_camera_mode_2.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_10.addWidget(self.lbl_camera_mode_2)

        self.combo_camera_mode_2 = QComboBox(self.groupBox_settings_2)
        self.combo_camera_mode_2.setObjectName(u"combo_camera_mode_2")
        sizePolicy1.setHeightForWidth(self.combo_camera_mode_2.sizePolicy().hasHeightForWidth())
        self.combo_camera_mode_2.setSizePolicy(sizePolicy1)
        self.combo_camera_mode_2.setMinimumSize(QSize(180, 0))

        self.horizontalLayout_10.addWidget(self.combo_camera_mode_2)


        self.verticalLayout_4.addLayout(self.horizontalLayout_10)

        self.verticalLayout_23 = QVBoxLayout()
        self.verticalLayout_23.setObjectName(u"verticalLayout_23")
        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.lbl_track_color_2 = QLabel(self.groupBox_settings_2)
        self.lbl_track_color_2.setObjectName(u"lbl_track_color_2")
        self.lbl_track_color_2.setMinimumSize(QSize(60, 0))
        self.lbl_track_color_2.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_8.addWidget(self.lbl_track_color_2)

        self.combo_track_color_2 = QComboBox(self.groupBox_settings_2)
        self.combo_track_color_2.setObjectName(u"combo_track_color_2")
        sizePolicy1.setHeightForWidth(self.combo_track_color_2.sizePolicy().hasHeightForWidth())
        self.combo_track_color_2.setSizePolicy(sizePolicy1)
        self.combo_track_color_2.setMinimumSize(QSize(110, 0))

        self.horizontalLayout_8.addWidget(self.combo_track_color_2)


        self.verticalLayout_23.addLayout(self.horizontalLayout_8)

        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.lbl_local_zoom = QLabel(self.groupBox_settings_2)
        self.lbl_local_zoom.setObjectName(u"lbl_local_zoom")
        self.lbl_local_zoom.setMinimumSize(QSize(60, 0))
        self.lbl_local_zoom.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_14.addWidget(self.lbl_local_zoom)

        self.combo_local_zoom = QComboBox(self.groupBox_settings_2)
        self.combo_local_zoom.setObjectName(u"combo_local_zoom")
        sizePolicy1.setHeightForWidth(self.combo_local_zoom.sizePolicy().hasHeightForWidth())
        self.combo_local_zoom.setSizePolicy(sizePolicy1)
        self.combo_local_zoom.setMinimumSize(QSize(110, 0))
        self.combo_local_zoom.setMaximumSize(QSize(16777215, 16777215))

        self.horizontalLayout_14.addWidget(self.combo_local_zoom)


        self.verticalLayout_23.addLayout(self.horizontalLayout_14)

        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.lbl_view_margin = QLabel(self.groupBox_settings_2)
        self.lbl_view_margin.setObjectName(u"lbl_view_margin")
        self.lbl_view_margin.setMinimumSize(QSize(60, 0))
        self.lbl_view_margin.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_13.addWidget(self.lbl_view_margin)

        self.lineEdit_view_margin = QLineEdit(self.groupBox_settings_2)
        self.lineEdit_view_margin.setObjectName(u"lineEdit_view_margin")
        sizePolicy1.setHeightForWidth(self.lineEdit_view_margin.sizePolicy().hasHeightForWidth())
        self.lineEdit_view_margin.setSizePolicy(sizePolicy1)
        self.lineEdit_view_margin.setMinimumSize(QSize(0, 0))
        self.lineEdit_view_margin.setMaximumSize(QSize(16777215, 16777215))

        self.horizontalLayout_13.addWidget(self.lineEdit_view_margin)


        self.verticalLayout_23.addLayout(self.horizontalLayout_13)


        self.verticalLayout_4.addLayout(self.verticalLayout_23)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.lbl_hide_privacy = QLabel(self.groupBox_settings_2)
        self.lbl_hide_privacy.setObjectName(u"lbl_hide_privacy")
        self.lbl_hide_privacy.setMinimumSize(QSize(60, 0))
        self.lbl_hide_privacy.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_5.addWidget(self.lbl_hide_privacy)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.spin_hide_start = QDoubleSpinBox(self.groupBox_settings_2)
        self.spin_hide_start.setObjectName(u"spin_hide_start")
        sizePolicy1.setHeightForWidth(self.spin_hide_start.sizePolicy().hasHeightForWidth())
        self.spin_hide_start.setSizePolicy(sizePolicy1)
        self.spin_hide_start.setMinimumSize(QSize(0, 0))
        self.spin_hide_start.setDecimals(2)
        self.spin_hide_start.setSingleStep(0.000000000000000)

        self.horizontalLayout_3.addWidget(self.spin_hide_start)


        self.horizontalLayout_5.addLayout(self.horizontalLayout_3)

        self.lbl_hide_end_3 = QLabel(self.groupBox_settings_2)
        self.lbl_hide_end_3.setObjectName(u"lbl_hide_end_3")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.lbl_hide_end_3.sizePolicy().hasHeightForWidth())
        self.lbl_hide_end_3.setSizePolicy(sizePolicy5)
        self.lbl_hide_end_3.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_5.addWidget(self.lbl_hide_end_3)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.spin_hide_end = QDoubleSpinBox(self.groupBox_settings_2)
        self.spin_hide_end.setObjectName(u"spin_hide_end")
        sizePolicy1.setHeightForWidth(self.spin_hide_end.sizePolicy().hasHeightForWidth())
        self.spin_hide_end.setSizePolicy(sizePolicy1)
        self.spin_hide_end.setMinimumSize(QSize(0, 0))

        self.horizontalLayout_4.addWidget(self.spin_hide_end)


        self.horizontalLayout_5.addLayout(self.horizontalLayout_4)


        self.verticalLayout_4.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.chk_dynamic_speed_zoom = QCheckBox(self.groupBox_settings_2)
        self.chk_dynamic_speed_zoom.setObjectName(u"chk_dynamic_speed_zoom")
        self.chk_dynamic_speed_zoom.setChecked(True)

        self.horizontalLayout_6.addWidget(self.chk_dynamic_speed_zoom)

        self.chk_real_speed_2 = QCheckBox(self.groupBox_settings_2)
        self.chk_real_speed_2.setObjectName(u"chk_real_speed_2")

        self.horizontalLayout_6.addWidget(self.chk_real_speed_2)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_2)


        self.verticalLayout_4.addLayout(self.horizontalLayout_6)

        self.splitter_2.addWidget(self.groupBox_settings_2)

        self.gridLayout_7.addWidget(self.splitter_2, 0, 0, 1, 1)

        self.groupBox_workers = QGroupBox(self.tab_general)
        self.groupBox_workers.setObjectName(u"groupBox_workers")
        sizePolicy.setHeightForWidth(self.groupBox_workers.sizePolicy().hasHeightForWidth())
        self.groupBox_workers.setSizePolicy(sizePolicy)
        self.gridLayout_5 = QGridLayout(self.groupBox_workers)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.verticalLayout_16 = QVBoxLayout()
        self.verticalLayout_16.setObjectName(u"verticalLayout_16")
        self.progressBar_main = PyCircularProgress(self.groupBox_workers)
        self.progressBar_main.setObjectName(u"progressBar_main")
        self.progressBar_main.setMinimumSize(QSize(110, 110))
        self.progressBar_main.setProperty(u"value", 0)

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
        self.progressBar_worker_1.setProperty(u"value", 0)

        self.verticalLayout_10.addWidget(self.progressBar_worker_1)

        self.horizontalLayout_worker_1 = QHBoxLayout()
        self.horizontalLayout_worker_1.setObjectName(u"horizontalLayout_worker_1")
        self.lbl_worker_1 = QLabel(self.groupBox_workers)
        self.lbl_worker_1.setObjectName(u"lbl_worker_1")
        self.lbl_worker_1.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

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
        self.progressBar_worker_4.setProperty(u"value", 0)

        self.verticalLayout_13.addWidget(self.progressBar_worker_4)

        self.horizontalLayout_worker_4 = QHBoxLayout()
        self.horizontalLayout_worker_4.setObjectName(u"horizontalLayout_worker_4")
        self.lbl_worker_4 = QLabel(self.groupBox_workers)
        self.lbl_worker_4.setObjectName(u"lbl_worker_4")
        self.lbl_worker_4.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

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
        self.progressBar_worker_2.setProperty(u"value", 0)

        self.verticalLayout_11.addWidget(self.progressBar_worker_2)

        self.horizontalLayout_worker_2 = QHBoxLayout()
        self.horizontalLayout_worker_2.setObjectName(u"horizontalLayout_worker_2")
        self.lbl_worker_2 = QLabel(self.groupBox_workers)
        self.lbl_worker_2.setObjectName(u"lbl_worker_2")
        self.lbl_worker_2.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

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
        self.progressBar_worker_5.setProperty(u"value", 0)

        self.verticalLayout_14.addWidget(self.progressBar_worker_5)

        self.horizontalLayout_worker_5 = QHBoxLayout()
        self.horizontalLayout_worker_5.setObjectName(u"horizontalLayout_worker_5")
        self.lbl_worker_5 = QLabel(self.groupBox_workers)
        self.lbl_worker_5.setObjectName(u"lbl_worker_5")
        self.lbl_worker_5.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

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
        self.progressBar_worker_3.setProperty(u"value", 0)

        self.verticalLayout_12.addWidget(self.progressBar_worker_3)

        self.horizontalLayout_worker_3 = QHBoxLayout()
        self.horizontalLayout_worker_3.setObjectName(u"horizontalLayout_worker_3")
        self.lbl_worker_3 = QLabel(self.groupBox_workers)
        self.lbl_worker_3.setObjectName(u"lbl_worker_3")
        self.lbl_worker_3.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

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
        self.progressBar_worker_6.setProperty(u"value", 0)

        self.verticalLayout_15.addWidget(self.progressBar_worker_6)

        self.horizontalLayout_worker_6 = QHBoxLayout()
        self.horizontalLayout_worker_6.setObjectName(u"horizontalLayout_worker_6")
        self.lbl_worker_6 = QLabel(self.groupBox_workers)
        self.lbl_worker_6.setObjectName(u"lbl_worker_6")
        self.lbl_worker_6.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_worker_6.addWidget(self.lbl_worker_6)

        self.lbl_worker_status_6 = QLabel(self.groupBox_workers)
        self.lbl_worker_status_6.setObjectName(u"lbl_worker_status_6")

        self.horizontalLayout_worker_6.addWidget(self.lbl_worker_status_6)


        self.verticalLayout_15.addLayout(self.horizontalLayout_worker_6)


        self.gridLayout_4.addLayout(self.verticalLayout_15, 2, 1, 1, 1)


        self.gridLayout_5.addLayout(self.gridLayout_4, 0, 1, 1, 1)


        self.gridLayout_7.addWidget(self.groupBox_workers, 1, 0, 1, 1)

        self.tabWidget.addTab(self.tab_general, "")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.gridLayout_2 = QGridLayout(self.tab)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.top_group = QGroupBox(self.tab)
        self.top_group.setObjectName(u"top_group")
        sizePolicy.setHeightForWidth(self.top_group.sizePolicy().hasHeightForWidth())
        self.top_group.setSizePolicy(sizePolicy)
        self.top_group.setMinimumSize(QSize(0, 0))
        self.gridLayout_6 = QGridLayout(self.top_group)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.verticalLayout_25 = QVBoxLayout()
        self.verticalLayout_25.setObjectName(u"verticalLayout_25")
        self.horizontalLayout_preview_res = QHBoxLayout()
        self.horizontalLayout_preview_res.setObjectName(u"horizontalLayout_preview_res")
        self.lbl_preview_resolution = QLabel(self.top_group)
        self.lbl_preview_resolution.setObjectName(u"lbl_preview_resolution")
        self.lbl_preview_resolution.setMinimumSize(QSize(85, 0))
        self.lbl_preview_resolution.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_preview_res.addWidget(self.lbl_preview_resolution)

        self.combo_preview_resolution = QComboBox(self.top_group)
        self.combo_preview_resolution.setObjectName(u"combo_preview_resolution")
        sizePolicy1.setHeightForWidth(self.combo_preview_resolution.sizePolicy().hasHeightForWidth())
        self.combo_preview_resolution.setSizePolicy(sizePolicy1)
        self.combo_preview_resolution.setMinimumSize(QSize(220, 0))
        self.combo_preview_resolution.setMaximumSize(QSize(16777215, 16777215))

        self.horizontalLayout_preview_res.addWidget(self.combo_preview_resolution)


        self.verticalLayout_25.addLayout(self.horizontalLayout_preview_res)

        self.horizontalLayout_preview_map_style = QHBoxLayout()
        self.horizontalLayout_preview_map_style.setObjectName(u"horizontalLayout_preview_map_style")
        self.lbl_preview_map_style = QLabel(self.top_group)
        self.lbl_preview_map_style.setObjectName(u"lbl_preview_map_style")
        self.lbl_preview_map_style.setMinimumSize(QSize(85, 0))
        self.lbl_preview_map_style.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_preview_map_style.addWidget(self.lbl_preview_map_style)

        self.combo_preview_map_style = QComboBox(self.top_group)
        self.combo_preview_map_style.setObjectName(u"combo_preview_map_style")
        sizePolicy1.setHeightForWidth(self.combo_preview_map_style.sizePolicy().hasHeightForWidth())
        self.combo_preview_map_style.setSizePolicy(sizePolicy1)
        self.combo_preview_map_style.setMinimumSize(QSize(220, 0))
        self.combo_preview_map_style.setMaximumSize(QSize(16777215, 16777215))

        self.horizontalLayout_preview_map_style.addWidget(self.combo_preview_map_style)


        self.verticalLayout_25.addLayout(self.horizontalLayout_preview_map_style)

        self.horizontalLayout_preview_camera = QHBoxLayout()
        self.horizontalLayout_preview_camera.setObjectName(u"horizontalLayout_preview_camera")
        self.lbl_preview_camera_mode = QLabel(self.top_group)
        self.lbl_preview_camera_mode.setObjectName(u"lbl_preview_camera_mode")
        self.lbl_preview_camera_mode.setMinimumSize(QSize(85, 0))
        self.lbl_preview_camera_mode.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_preview_camera.addWidget(self.lbl_preview_camera_mode)

        self.combo_preview_camera_mode = QComboBox(self.top_group)
        self.combo_preview_camera_mode.setObjectName(u"combo_preview_camera_mode")
        sizePolicy1.setHeightForWidth(self.combo_preview_camera_mode.sizePolicy().hasHeightForWidth())
        self.combo_preview_camera_mode.setSizePolicy(sizePolicy1)
        self.combo_preview_camera_mode.setMinimumSize(QSize(220, 0))
        self.combo_preview_camera_mode.setMaximumSize(QSize(16777215, 16777215))

        self.horizontalLayout_preview_camera.addWidget(self.combo_preview_camera_mode)


        self.verticalLayout_25.addLayout(self.horizontalLayout_preview_camera)

        self.horizontalLayout_panels_2 = QHBoxLayout()
        self.horizontalLayout_panels_2.setObjectName(u"horizontalLayout_panels_2")
        self.lbl_panels_2 = QLabel(self.top_group)
        self.lbl_panels_2.setObjectName(u"lbl_panels_2")
        self.lbl_panels_2.setMinimumSize(QSize(85, 0))
        self.lbl_panels_2.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_panels_2.addWidget(self.lbl_panels_2)

        self.combo_hud_panels = CheckableComboBox(self.top_group)
        self.combo_hud_panels.setObjectName(u"combo_hud_panels")
        sizePolicy1.setHeightForWidth(self.combo_hud_panels.sizePolicy().hasHeightForWidth())
        self.combo_hud_panels.setSizePolicy(sizePolicy1)
        self.combo_hud_panels.setMinimumSize(QSize(220, 0))
        self.combo_hud_panels.setMaximumSize(QSize(16777215, 16777215))

        self.horizontalLayout_panels_2.addWidget(self.combo_hud_panels)


        self.verticalLayout_25.addLayout(self.horizontalLayout_panels_2)


        self.gridLayout_6.addLayout(self.verticalLayout_25, 0, 0, 1, 1)

        self.label_distance_info = QLabel(self.top_group)
        self.label_distance_info.setObjectName(u"label_distance_info")

        self.gridLayout_6.addWidget(self.label_distance_info, 2, 0, 1, 1)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_23 = QHBoxLayout()
        self.horizontalLayout_23.setObjectName(u"horizontalLayout_23")
        self.lbl_duration = QLabel(self.top_group)
        self.lbl_duration.setObjectName(u"lbl_duration")
        sizePolicy2.setHeightForWidth(self.lbl_duration.sizePolicy().hasHeightForWidth())
        self.lbl_duration.setSizePolicy(sizePolicy2)
        self.lbl_duration.setMinimumSize(QSize(73, 0))
        self.lbl_duration.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_23.addWidget(self.lbl_duration)

        self.lineEdit_duration = QLineEdit(self.top_group)
        self.lineEdit_duration.setObjectName(u"lineEdit_duration")
        sizePolicy1.setHeightForWidth(self.lineEdit_duration.sizePolicy().hasHeightForWidth())
        self.lineEdit_duration.setSizePolicy(sizePolicy1)
        self.lineEdit_duration.setMinimumSize(QSize(0, 0))

        self.horizontalLayout_23.addWidget(self.lineEdit_duration)


        self.verticalLayout.addLayout(self.horizontalLayout_23)

        self.horizontalLayout_27 = QHBoxLayout()
        self.horizontalLayout_27.setObjectName(u"horizontalLayout_27")
        self.lbl_end_hold = QLabel(self.top_group)
        self.lbl_end_hold.setObjectName(u"lbl_end_hold")
        self.lbl_end_hold.setMinimumSize(QSize(73, 0))
        self.lbl_end_hold.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_27.addWidget(self.lbl_end_hold)

        self.lineEdit_end_hold = QLineEdit(self.top_group)
        self.lineEdit_end_hold.setObjectName(u"lineEdit_end_hold")
        sizePolicy1.setHeightForWidth(self.lineEdit_end_hold.sizePolicy().hasHeightForWidth())
        self.lineEdit_end_hold.setSizePolicy(sizePolicy1)
        self.lineEdit_end_hold.setMaximumSize(QSize(16777215, 16777215))

        self.horizontalLayout_27.addWidget(self.lineEdit_end_hold)


        self.verticalLayout.addLayout(self.horizontalLayout_27)

        self.horizontalLayout_28 = QHBoxLayout()
        self.horizontalLayout_28.setObjectName(u"horizontalLayout_28")
        self.lbl_zoomout = QLabel(self.top_group)
        self.lbl_zoomout.setObjectName(u"lbl_zoomout")
        self.lbl_zoomout.setMinimumSize(QSize(73, 0))
        self.lbl_zoomout.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_28.addWidget(self.lbl_zoomout)

        self.lineEdit_zoomout = QLineEdit(self.top_group)
        self.lineEdit_zoomout.setObjectName(u"lineEdit_zoomout")
        sizePolicy1.setHeightForWidth(self.lineEdit_zoomout.sizePolicy().hasHeightForWidth())
        self.lineEdit_zoomout.setSizePolicy(sizePolicy1)
        self.lineEdit_zoomout.setMaximumSize(QSize(16777215, 16777215))

        self.horizontalLayout_28.addWidget(self.lineEdit_zoomout)


        self.verticalLayout.addLayout(self.horizontalLayout_28)

        self.line = QFrame(self.top_group)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.horizontalLayout_25 = QHBoxLayout()
        self.horizontalLayout_25.setObjectName(u"horizontalLayout_25")
        self.lbl_photo_dur_title = QLabel(self.top_group)
        self.lbl_photo_dur_title.setObjectName(u"lbl_photo_dur_title")
        self.lbl_photo_dur_title.setMinimumSize(QSize(73, 0))
        self.lbl_photo_dur_title.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_25.addWidget(self.lbl_photo_dur_title)

        self.spin_photo_dur = QDoubleSpinBox(self.top_group)
        self.spin_photo_dur.setObjectName(u"spin_photo_dur")
        sizePolicy1.setHeightForWidth(self.spin_photo_dur.sizePolicy().hasHeightForWidth())
        self.spin_photo_dur.setSizePolicy(sizePolicy1)
        self.spin_photo_dur.setMinimumSize(QSize(100, 0))
        self.spin_photo_dur.setMaximumSize(QSize(16777215, 16777215))
        self.spin_photo_dur.setMinimum(1.000000000000000)
        self.spin_photo_dur.setMaximum(30.000000000000000)
        self.spin_photo_dur.setSingleStep(0.500000000000000)
        self.spin_photo_dur.setValue(3.000000000000000)

        self.horizontalLayout_25.addWidget(self.spin_photo_dur)


        self.gridLayout_3.addLayout(self.horizontalLayout_25, 0, 0, 1, 1)

        self.btn_reset_defaults = QPushButton(self.top_group)
        self.btn_reset_defaults.setObjectName(u"btn_reset_defaults")
        sizePolicy.setHeightForWidth(self.btn_reset_defaults.sizePolicy().hasHeightForWidth())
        self.btn_reset_defaults.setSizePolicy(sizePolicy)
        self.btn_reset_defaults.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.gridLayout_3.addWidget(self.btn_reset_defaults, 0, 1, 2, 1)

        self.horizontalLayout_26 = QHBoxLayout()
        self.horizontalLayout_26.setObjectName(u"horizontalLayout_26")
        self.lbl_caption_size_title = QLabel(self.top_group)
        self.lbl_caption_size_title.setObjectName(u"lbl_caption_size_title")
        self.lbl_caption_size_title.setMinimumSize(QSize(73, 0))
        self.lbl_caption_size_title.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_26.addWidget(self.lbl_caption_size_title)

        self.spin_default_caption_size = QSpinBox(self.top_group)
        self.spin_default_caption_size.setObjectName(u"spin_default_caption_size")
        sizePolicy1.setHeightForWidth(self.spin_default_caption_size.sizePolicy().hasHeightForWidth())
        self.spin_default_caption_size.setSizePolicy(sizePolicy1)
        self.spin_default_caption_size.setMinimumSize(QSize(100, 0))
        self.spin_default_caption_size.setMaximumSize(QSize(16777215, 16777215))
        self.spin_default_caption_size.setMinimum(50)
        self.spin_default_caption_size.setMaximum(80)
        self.spin_default_caption_size.setSingleStep(1)
        self.spin_default_caption_size.setValue(50)

        self.horizontalLayout_26.addWidget(self.spin_default_caption_size)


        self.gridLayout_3.addLayout(self.horizontalLayout_26, 1, 0, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout_3)


        self.gridLayout_6.addLayout(self.verticalLayout, 0, 2, 3, 1)

        self.horizontalLayout_22 = QHBoxLayout()
        self.horizontalLayout_22.setObjectName(u"horizontalLayout_22")
        self.horizontalLayout_rate_2 = QHBoxLayout()
        self.horizontalLayout_rate_2.setObjectName(u"horizontalLayout_rate_2")
        self.lbl_rate = QLabel(self.top_group)
        self.lbl_rate.setObjectName(u"lbl_rate")
        sizePolicy.setHeightForWidth(self.lbl_rate.sizePolicy().hasHeightForWidth())
        self.lbl_rate.setSizePolicy(sizePolicy)
        self.lbl_rate.setMinimumSize(QSize(85, 0))
        self.lbl_rate.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_rate_2.addWidget(self.lbl_rate)

        self.spin_seconds_per_100km = QSpinBox(self.top_group)
        self.spin_seconds_per_100km.setObjectName(u"spin_seconds_per_100km")
        sizePolicy1.setHeightForWidth(self.spin_seconds_per_100km.sizePolicy().hasHeightForWidth())
        self.spin_seconds_per_100km.setSizePolicy(sizePolicy1)
        self.spin_seconds_per_100km.setMinimumSize(QSize(0, 0))
        self.spin_seconds_per_100km.setMinimum(1)
        self.spin_seconds_per_100km.setMaximum(9999)
        self.spin_seconds_per_100km.setValue(60)

        self.horizontalLayout_rate_2.addWidget(self.spin_seconds_per_100km)

        self.chk_auto_duration = QCheckBox(self.top_group)
        self.chk_auto_duration.setObjectName(u"chk_auto_duration")
        sizePolicy4.setHeightForWidth(self.chk_auto_duration.sizePolicy().hasHeightForWidth())
        self.chk_auto_duration.setSizePolicy(sizePolicy4)

        self.horizontalLayout_rate_2.addWidget(self.chk_auto_duration)


        self.horizontalLayout_22.addLayout(self.horizontalLayout_rate_2)


        self.gridLayout_6.addLayout(self.horizontalLayout_22, 1, 0, 1, 1)

        self.line_3 = QFrame(self.top_group)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.Shape.VLine)
        self.line_3.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout_6.addWidget(self.line_3, 0, 1, 3, 1)


        self.gridLayout_2.addWidget(self.top_group, 0, 0, 1, 2)

        self.group_media_list = QGroupBox(self.tab)
        self.group_media_list.setObjectName(u"group_media_list")
        sizePolicy.setHeightForWidth(self.group_media_list.sizePolicy().hasHeightForWidth())
        self.group_media_list.setSizePolicy(sizePolicy)
        self.group_media_list.setMinimumSize(QSize(0, 0))
        self.group_media_list.setMaximumSize(QSize(16777215, 300))
        self.verticalLayout_20 = QVBoxLayout(self.group_media_list)
        self.verticalLayout_20.setObjectName(u"verticalLayout_20")
        self.table = QTableWidget(self.group_media_list)
        if (self.table.columnCount() < 8):
            self.table.setColumnCount(8)
        __qtablewidgetitem = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(4, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(5, __qtablewidgetitem5)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(6, __qtablewidgetitem6)
        __qtablewidgetitem7 = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(7, __qtablewidgetitem7)
        self.table.setObjectName(u"table")
        self.table.setMinimumSize(QSize(0, 0))
        self.table.setMaximumSize(QSize(16777215, 16777215))
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setColumnCount(8)

        self.verticalLayout_20.addWidget(self.table)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalSpacer_table_hdr = QSpacerItem(163, 18, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_table_hdr)

        self.btn_add_files = QPushButton(self.group_media_list)
        self.btn_add_files.setObjectName(u"btn_add_files")
        self.btn_add_files.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.horizontalLayout_7.addWidget(self.btn_add_files)

        self.btn_add_folder = QPushButton(self.group_media_list)
        self.btn_add_folder.setObjectName(u"btn_add_folder")
        self.btn_add_folder.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.horizontalLayout_7.addWidget(self.btn_add_folder)


        self.verticalLayout_20.addLayout(self.horizontalLayout_7)


        self.gridLayout_2.addWidget(self.group_media_list, 1, 0, 1, 2)

        self.info_group = QGroupBox(self.tab)
        self.info_group.setObjectName(u"info_group")
        sizePolicy.setHeightForWidth(self.info_group.sizePolicy().hasHeightForWidth())
        self.info_group.setSizePolicy(sizePolicy)
        self.info_group.setMinimumSize(QSize(0, 0))
        self.verticalLayout_21 = QVBoxLayout(self.info_group)
        self.verticalLayout_21.setObjectName(u"verticalLayout_21")
        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.lbl_fn_title = QLabel(self.info_group)
        self.lbl_fn_title.setObjectName(u"lbl_fn_title")

        self.horizontalLayout_12.addWidget(self.lbl_fn_title)

        self.lbl_info_filename = QLabel(self.info_group)
        self.lbl_info_filename.setObjectName(u"lbl_info_filename")
        self.lbl_info_filename.setStyleSheet(u"font-weight: bold; color: #e2e8f0;")
        self.lbl_info_filename.setWordWrap(True)

        self.horizontalLayout_12.addWidget(self.lbl_info_filename)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_12.addItem(self.horizontalSpacer_5)


        self.verticalLayout_21.addLayout(self.horizontalLayout_12)

        self.horizontalLayout_15 = QHBoxLayout()
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.lbl_time_title = QLabel(self.info_group)
        self.lbl_time_title.setObjectName(u"lbl_time_title")

        self.horizontalLayout_15.addWidget(self.lbl_time_title)

        self.lbl_info_time = QLabel(self.info_group)
        self.lbl_info_time.setObjectName(u"lbl_info_time")
        self.lbl_info_time.setStyleSheet(u"color: #cbd5e0;")

        self.horizontalLayout_15.addWidget(self.lbl_info_time)

        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_15.addItem(self.horizontalSpacer_7)


        self.verticalLayout_21.addLayout(self.horizontalLayout_15)

        self.horizontalLayout_16 = QHBoxLayout()
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.lbl_gps_title = QLabel(self.info_group)
        self.lbl_gps_title.setObjectName(u"lbl_gps_title")

        self.horizontalLayout_16.addWidget(self.lbl_gps_title)

        self.lbl_info_gps = QLabel(self.info_group)
        self.lbl_info_gps.setObjectName(u"lbl_info_gps")
        self.lbl_info_gps.setStyleSheet(u"color: #cbd5e0;")

        self.horizontalLayout_16.addWidget(self.lbl_info_gps)

        self.horizontalSpacer_8 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_16.addItem(self.horizontalSpacer_8)


        self.verticalLayout_21.addLayout(self.horizontalLayout_16)

        self.horizontalLayout_19 = QHBoxLayout()
        self.horizontalLayout_19.setObjectName(u"horizontalLayout_19")
        self.lbl_res_title = QLabel(self.info_group)
        self.lbl_res_title.setObjectName(u"lbl_res_title")

        self.horizontalLayout_19.addWidget(self.lbl_res_title)

        self.lbl_info_res = QLabel(self.info_group)
        self.lbl_info_res.setObjectName(u"lbl_info_res")
        self.lbl_info_res.setStyleSheet(u"color: #cbd5e0;")

        self.horizontalLayout_19.addWidget(self.lbl_info_res)

        self.horizontalSpacer_9 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_19.addItem(self.horizontalSpacer_9)


        self.verticalLayout_21.addLayout(self.horizontalLayout_19)

        self.horizontalLayout_20 = QHBoxLayout()
        self.horizontalLayout_20.setObjectName(u"horizontalLayout_20")
        self.lbl_match_title = QLabel(self.info_group)
        self.lbl_match_title.setObjectName(u"lbl_match_title")

        self.horizontalLayout_20.addWidget(self.lbl_match_title)

        self.lbl_info_match = QLabel(self.info_group)
        self.lbl_info_match.setObjectName(u"lbl_info_match")
        self.lbl_info_match.setStyleSheet(u"color: #63b3ed; font-weight: bold;")

        self.horizontalLayout_20.addWidget(self.lbl_info_match)

        self.horizontalSpacer_10 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_20.addItem(self.horizontalSpacer_10)


        self.verticalLayout_21.addLayout(self.horizontalLayout_20)


        self.gridLayout_2.addWidget(self.info_group, 2, 2, 1, 1)

        self.preview_group = QGroupBox(self.tab)
        self.preview_group.setObjectName(u"preview_group")
        sizePolicy.setHeightForWidth(self.preview_group.sizePolicy().hasHeightForWidth())
        self.preview_group.setSizePolicy(sizePolicy)
        self.gridLayout_9 = QGridLayout(self.preview_group)
        self.gridLayout_9.setObjectName(u"gridLayout_9")
        self.lbl_preview_image = ClickablePreviewLabel(self.preview_group)
        self.lbl_preview_image.setObjectName(u"lbl_preview_image")
        sizePolicy.setHeightForWidth(self.lbl_preview_image.sizePolicy().hasHeightForWidth())
        self.lbl_preview_image.setSizePolicy(sizePolicy)
        self.lbl_preview_image.setMinimumSize(QSize(450, 160))
        self.lbl_preview_image.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.lbl_preview_image.setStyleSheet(u"background-color: #0b0f14; border: 1px solid #2d3748; border-radius: 8px; color: #a0aec0;")
        self.lbl_preview_image.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_9.addWidget(self.lbl_preview_image, 0, 0, 1, 2)


        self.gridLayout_2.addWidget(self.preview_group, 0, 2, 2, 1)

        self.groupBox_2 = QGroupBox(self.tab)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.groupBox_2.setMinimumSize(QSize(0, 0))
        self.gridLayout = QGridLayout(self.groupBox_2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.preview_widget = QtRoutePreviewWidget(self.groupBox_2)
        self.preview_widget.setObjectName(u"preview_widget")

        self.verticalLayout_2.addWidget(self.preview_widget)


        self.gridLayout.addLayout(self.verticalLayout_2, 0, 0, 1, 1)

        self.map_toolbar = QHBoxLayout()
        self.map_toolbar.setObjectName(u"map_toolbar")
        self.lbl_map_hint = QLabel(self.groupBox_2)
        self.lbl_map_hint.setObjectName(u"lbl_map_hint")
        self.lbl_map_hint.setStyleSheet(u"color: #718096; font-size: 11px;")

        self.map_toolbar.addWidget(self.lbl_map_hint)

        self.horizontalSpacer_map_hdr = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.map_toolbar.addItem(self.horizontalSpacer_map_hdr)

        self.btn_zoom_in = QPushButton(self.groupBox_2)
        self.btn_zoom_in.setObjectName(u"btn_zoom_in")
        sizePolicy2.setHeightForWidth(self.btn_zoom_in.sizePolicy().hasHeightForWidth())
        self.btn_zoom_in.setSizePolicy(sizePolicy2)

        self.map_toolbar.addWidget(self.btn_zoom_in)

        self.btn_zoom_out = QPushButton(self.groupBox_2)
        self.btn_zoom_out.setObjectName(u"btn_zoom_out")
        sizePolicy2.setHeightForWidth(self.btn_zoom_out.sizePolicy().hasHeightForWidth())
        self.btn_zoom_out.setSizePolicy(sizePolicy2)

        self.map_toolbar.addWidget(self.btn_zoom_out)

        self.btn_reset_view = QPushButton(self.groupBox_2)
        self.btn_reset_view.setObjectName(u"btn_reset_view")
        sizePolicy2.setHeightForWidth(self.btn_reset_view.sizePolicy().hasHeightForWidth())
        self.btn_reset_view.setSizePolicy(sizePolicy2)

        self.map_toolbar.addWidget(self.btn_reset_view)


        self.gridLayout.addLayout(self.map_toolbar, 1, 0, 1, 1)


        self.gridLayout_2.addWidget(self.groupBox_2, 2, 0, 1, 2)

        self.tabWidget.addTab(self.tab, "")

        self.gridLayout_8.addWidget(self.tabWidget, 0, 0, 2, 1)

        self.horizontalLayout_actions = QHBoxLayout()
        self.horizontalLayout_actions.setObjectName(u"horizontalLayout_actions")
        self.btn_start_render = QPushButton(self.centralwidget)
        self.btn_start_render.setObjectName(u"btn_start_render")
        sizePolicy2.setHeightForWidth(self.btn_start_render.sizePolicy().hasHeightForWidth())
        self.btn_start_render.setSizePolicy(sizePolicy2)
        self.btn_start_render.setMinimumSize(QSize(0, 0))
        font = QFont()
        font.setPointSize(12)
        self.btn_start_render.setFont(font)

        self.horizontalLayout_actions.addWidget(self.btn_start_render)

        self.btn_stop_render = QPushButton(self.centralwidget)
        self.btn_stop_render.setObjectName(u"btn_stop_render")
        self.btn_stop_render.setEnabled(False)
        sizePolicy2.setHeightForWidth(self.btn_stop_render.sizePolicy().hasHeightForWidth())
        self.btn_stop_render.setSizePolicy(sizePolicy2)
        self.btn_stop_render.setMinimumSize(QSize(0, 0))
        self.btn_stop_render.setFont(font)

        self.horizontalLayout_actions.addWidget(self.btn_stop_render)


        self.gridLayout_8.addLayout(self.horizontalLayout_actions, 2, 0, 1, 2)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1150, 33))
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
        self.menu_nvenc_preset = QMenu(self.menu_settings)
        self.menu_nvenc_preset.setObjectName(u"menu_nvenc_preset")
        self.menu_bitrate = QMenu(self.menu_settings)
        self.menu_bitrate.setObjectName(u"menu_bitrate")
        self.menu_workers = QMenu(self.menu_settings)
        self.menu_workers.setObjectName(u"menu_workers")
        self.menu_tile_connections = QMenu(self.menu_settings)
        self.menu_tile_connections.setObjectName(u"menu_tile_connections")
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
        self.menu_settings.addAction(self.menu_nvenc_preset.menuAction())
        self.menu_settings.addAction(self.menu_bitrate.menuAction())
        self.menu_settings.addSeparator()
        self.menu_settings.addAction(self.menu_hud_panels.menuAction())
        self.menu_settings.addAction(self.action_dynamic_speed_zoom)
        self.menu_settings.addAction(self.action_real_speed)
        self.menu_settings.addAction(self.action_basemap)
        self.menu_settings.addAction(self.action_parallel)
        self.menu_settings.addAction(self.action_enable_media)
        self.menu_settings.addAction(self.action_preview)
        self.menu_settings.addSeparator()
        self.menu_settings.addAction(self.menu_workers.menuAction())
        self.menu_settings.addAction(self.menu_tile_connections.menuAction())
        self.menu_settings.addAction(self.menu_cache_mode.menuAction())
        self.menu_settings.addSeparator()
        self.menu_settings.addAction(self.action_custom_resolution)
        self.menu_settings.addAction(self.action_advanced_settings)
        self.menu_profile.addAction(self.action_profile_fast)
        self.menu_profile.addAction(self.action_profile_balanced)
        self.menu_profile.addAction(self.action_profile_quality)
        self.menu_hud_panels.addAction(self.action_show_speed)
        self.menu_hud_panels.addAction(self.action_show_minimap)
        self.menu_hud_panels.addAction(self.action_show_elevation)
        self.menu_cache_mode.addAction(self.action_cache_session)
        self.menu_cache_mode.addAction(self.action_cache_persistent)
        self.menu_nvenc_preset.addAction(self.action_preset_p1)
        self.menu_nvenc_preset.addAction(self.action_preset_p2)
        self.menu_nvenc_preset.addAction(self.action_preset_p3)
        self.menu_nvenc_preset.addAction(self.action_preset_p4)
        self.menu_nvenc_preset.addAction(self.action_preset_p5)
        self.menu_nvenc_preset.addAction(self.action_preset_p6)
        self.menu_nvenc_preset.addAction(self.action_preset_p7)
        self.menu_bitrate.addAction(self.action_bitrate_8M)
        self.menu_bitrate.addAction(self.action_bitrate_12M)
        self.menu_bitrate.addAction(self.action_bitrate_20M)
        self.menu_bitrate.addAction(self.action_bitrate_24M)
        self.menu_bitrate.addAction(self.action_bitrate_30M)
        self.menu_bitrate.addAction(self.action_bitrate_40M)
        self.menu_bitrate.addAction(self.action_bitrate_60M)
        self.menu_workers.addAction(self.action_workers_2)
        self.menu_workers.addAction(self.action_workers_4)
        self.menu_workers.addAction(self.action_workers_6)
        self.menu_workers.addAction(self.action_workers_8)
        self.menu_workers.addAction(self.action_workers_12)
        self.menu_workers.addAction(self.action_workers_16)
        self.menu_tile_connections.addAction(self.action_tile_conn_4)
        self.menu_tile_connections.addAction(self.action_tile_conn_8)
        self.menu_tile_connections.addAction(self.action_tile_conn_16)
        self.menu_tile_connections.addAction(self.action_tile_conn_24)
        self.menu_tile_connections.addAction(self.action_tile_conn_32)
        self.menu_help.addAction(self.action_help_shortcuts)
        self.menu_help.addAction(self.action_about)
        self.toolBar.addAction(self.action_open_gpx)
        self.toolBar.addAction(self.action_media_dialog)
        self.toolBar.addAction(self.action_benchmark)
        self.toolBar.addAction(self.action_clear_cache)
        self.toolBar.addAction(self.action_open_log_folder)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.action_toggle_advanced)
        self.toolBar.addAction(self.action_advanced_settings)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.action_start_render)
        self.toolBar.addAction(self.action_stop_render)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"GPX Ride Renderer V1.4.0", None))
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
        self.action_preset_p1.setText(QCoreApplication.translate("MainWindow", u"p1 (\u6700\u5feb / \u6e2c\u8a66)", None))
        self.action_preset_p2.setText(QCoreApplication.translate("MainWindow", u"p2", None))
        self.action_preset_p3.setText(QCoreApplication.translate("MainWindow", u"p3 (\u5feb\u901f)", None))
        self.action_preset_p4.setText(QCoreApplication.translate("MainWindow", u"p4 (\u9810\u8a2d / \u5e73\u8861)", None))
        self.action_preset_p5.setText(QCoreApplication.translate("MainWindow", u"p5 (\u9ad8\u756b\u8cea)", None))
        self.action_preset_p6.setText(QCoreApplication.translate("MainWindow", u"p6", None))
        self.action_preset_p7.setText(QCoreApplication.translate("MainWindow", u"p7 (\u6700\u9ad8\u54c1\u8cea)", None))
        self.action_bitrate_8M.setText(QCoreApplication.translate("MainWindow", u"8 Mbps", None))
        self.action_bitrate_12M.setText(QCoreApplication.translate("MainWindow", u"12 Mbps", None))
        self.action_bitrate_20M.setText(QCoreApplication.translate("MainWindow", u"20 Mbps (\u9810\u8a2d)", None))
        self.action_bitrate_24M.setText(QCoreApplication.translate("MainWindow", u"24 Mbps", None))
        self.action_bitrate_30M.setText(QCoreApplication.translate("MainWindow", u"30 Mbps (\u9ad8\u756b\u8cea)", None))
        self.action_bitrate_40M.setText(QCoreApplication.translate("MainWindow", u"40 Mbps", None))
        self.action_bitrate_60M.setText(QCoreApplication.translate("MainWindow", u"60 Mbps (\u6975\u81f4)", None))
        self.action_workers_2.setText(QCoreApplication.translate("MainWindow", u"2 Workers", None))
        self.action_workers_4.setText(QCoreApplication.translate("MainWindow", u"4 Workers", None))
        self.action_workers_6.setText(QCoreApplication.translate("MainWindow", u"6 Workers (\u9810\u8a2d)", None))
        self.action_workers_8.setText(QCoreApplication.translate("MainWindow", u"8 Workers", None))
        self.action_workers_12.setText(QCoreApplication.translate("MainWindow", u"12 Workers", None))
        self.action_workers_16.setText(QCoreApplication.translate("MainWindow", u"16 Workers", None))
        self.action_tile_conn_4.setText(QCoreApplication.translate("MainWindow", u"4 Connections", None))
        self.action_tile_conn_8.setText(QCoreApplication.translate("MainWindow", u"8 Connections", None))
        self.action_tile_conn_16.setText(QCoreApplication.translate("MainWindow", u"16 Connections (\u9810\u8a2d)", None))
        self.action_tile_conn_24.setText(QCoreApplication.translate("MainWindow", u"24 Connections", None))
        self.action_tile_conn_32.setText(QCoreApplication.translate("MainWindow", u"32 Connections", None))
        self.action_custom_resolution.setText(QCoreApplication.translate("MainWindow", u"\u81ea\u8a02\u756b\u9762\u89e3\u6790\u5ea6 (\u5bec \u00d7 \u9ad8)...", None))
        self.action_advanced_settings.setText(QCoreApplication.translate("MainWindow", u"\u9032\u968e\u6e32\u67d3\u53c3\u6578\u8a73\u7d30\u8a2d\u5b9a...", None))
        self.groupBox_files.setTitle(QCoreApplication.translate("MainWindow", u"\u6a94\u6848", None))
        self.lbl_gpx.setText(QCoreApplication.translate("MainWindow", u"GPX \u6a94\u6848\uff1a", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_gpx.setToolTip(QCoreApplication.translate("MainWindow", u"\u9078\u64c7\u6b32\u6e32\u67d3\u7684 GPX \u8ecc\u8de1\u8def\u5f91\u6a94\u6848 (.gpx)", None))
#endif // QT_CONFIG(tooltip)
        self.btn_browse_gpx.setText(QCoreApplication.translate("MainWindow", u"\u700f\u89bd\u2026", None))
        self.lbl_output.setText(QCoreApplication.translate("MainWindow", u"\u8f38\u51fa\u5f71\u7247\uff1a", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_output.setToolTip(QCoreApplication.translate("MainWindow", u"\u6307\u5b9a\u8f38\u51fa\u7684 MP4 \u5f71\u7247\u6a94\u540d\u8207\u8cc7\u6599\u593e\u8def\u5f91", None))
#endif // QT_CONFIG(tooltip)
        self.btn_browse_output.setText(QCoreApplication.translate("MainWindow", u"\u700f\u89bd\u2026", None))
#if QT_CONFIG(tooltip)
        self.lbl_media.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u9078\u64c7\u5305\u542b\u7167\u7247\u6216\u5f71\u7247\u7684\u8cc7\u6599\u593e\u6216\u6a94\u6848\u3002\u7a0b\u5f0f\u6703\u81ea\u52d5\u8b80\u53d6 EXIF \u6642\u9593\u8207 GPS \u5ea7\u6a19\u9ede\u63d2\u5165\u6642\u9593\u8ef8\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_media.setText(QCoreApplication.translate("MainWindow", u"\u8def\u7dda\u5a92\u9ad4\uff1a", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_media.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u9078\u64c7\u5305\u542b\u7167\u7247\u6216\u5f71\u7247\u7684\u8cc7\u6599\u593e\u6216\u6a94\u6848\u3002\u7a0b\u5f0f\u6703\u81ea\u52d5\u8b80\u53d6 EXIF \u6642\u9593\u8207 GPS \u5ea7\u6a19\u9ede\u63d2\u5165\u6642\u9593\u8ef8\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.btn_browse_media.setText(QCoreApplication.translate("MainWindow", u"\u700f\u89bd\u2026", None))
        self.btn_media_dialog.setText(QCoreApplication.translate("MainWindow", u"\u5a92\u9ad4\u7ba1\u7406", None))
        self.groupBox_summary.setTitle(QCoreApplication.translate("MainWindow", u"\u8a2d\u5b9a\u6458\u8981", None))
        self.label_cfg_res.setText(QCoreApplication.translate("MainWindow", u"\u756b\u9762\u898f\u683c: 1440x1440 @ 60 FPS (\u81ea\u52d5\u6642\u9577 20.0s)", None))
        self.label_cfg_map.setText(QCoreApplication.translate("MainWindow", u"\u5730\u5716\u8996\u89d2: \u98a8\u683c [1] | North-Up | Zoom: 17", None))
        self.label_cfg_enc.setText(QCoreApplication.translate("MainWindow", u"\u7de8\u78bc\u8a2d\u5b9a: NVENC 30M (preset: p5) | \u7121\u5a92\u9ad4 Overlay", None))
        self.label_cfg_perf.setText(QCoreApplication.translate("MainWindow", u"\u6548\u80fd\u6a21\u5f0f: \u591a\u7a0b\u5e8f (6 Workers \u00d7 4 chunks) | \u505c\u7528 Cache", None))
        self.groupBox_settings_2.setTitle(QCoreApplication.translate("MainWindow", u"\u6e32\u67d3\u8a2d\u5b9a", None))
#if QT_CONFIG(tooltip)
        self.lbl_resolution_2.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u9078\u64c7\u8f38\u51fa\u5f71\u7247\u7684\u89e3\u6790\u5ea6\u5c3a\u5bf8\u8207\u756b\u9762\u6bd4\u4f8b\uff089:16, 16:9, 1:1 \u7b49\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_resolution_2.setText(QCoreApplication.translate("MainWindow", u"\u89e3\u6790\u5ea6\uff1a", None))
#if QT_CONFIG(tooltip)
        self.combo_resolution_2.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u9078\u64c7\u8f38\u51fa\u5f71\u7247\u7684\u89e3\u6790\u5ea6\u5c3a\u5bf8\u8207\u756b\u9762\u6bd4\u4f8b\uff089:16, 16:9, 1:1 \u7b49\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.label.setText(QCoreApplication.translate("MainWindow", u"/", None))
#if QT_CONFIG(tooltip)
        self.spin_fps.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u8a2d\u5b9a\u8f38\u51fa\u5f71\u7247\u6bcf\u79d2\u5305\u542b\u591a\u5c11\u5e40\uff08\u9810\u8a2d 60 FPS\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.spin_fps.setSuffix(QCoreApplication.translate("MainWindow", u" FPS", None))
#if QT_CONFIG(tooltip)
        self.lbl_profile_2.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u4e00\u6b21\u5957\u7528\u4e00\u7d44\u89e3\u6790\u5ea6\u3001Local Zoom\u3001bitrate\u3001NVENC preset\u3001Workers \u8207 Chunks/Worker\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_profile_2.setText(QCoreApplication.translate("MainWindow", u"\u9810\u8a2d\u6a21\u5f0f\uff1a", None))
#if QT_CONFIG(tooltip)
        self.combo_profile_2.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u4e00\u6b21\u5957\u7528\u4e00\u7d44\u89e3\u6790\u5ea6\u3001Local Zoom\u3001bitrate\u3001NVENC preset\u3001Workers \u8207 Chunks/Worker\u3002", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.lbl_map_style_2.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u6c7a\u5b9a\u5f71\u7247\u4e3b\u756b\u9762\u8207\u7d50\u5c3e overview \u4f7f\u7528\u7684\u5e95\u5716\u6a23\u5f0f\u3002\n"
"\u5efa\u8b70\uff1a\u6df1\u8272\u8def\u7dda\u53ef\u7528 DarkMatter\uff0c\u9053\u8def\u7d30\u7bc0\u53ef\u7528 Voyager\uff0c\u885b\u661f\u5716\u8cc7\u8a0a\u91cf\u6700\u9ad8\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_map_style_2.setText(QCoreApplication.translate("MainWindow", u"\u5730\u5716\u98a8\u683c\uff1a", None))
        self.combo_map_style_2.setItemText(0, QCoreApplication.translate("MainWindow", u"4. \u885b\u661f\u5f71\u8c61 (\u5be6\u666f\u7a7a\u62cd)", None))

#if QT_CONFIG(tooltip)
        self.combo_map_style_2.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u6c7a\u5b9a\u5f71\u7247\u4e3b\u756b\u9762\u8207\u7d50\u5c3e overview \u4f7f\u7528\u7684\u5e95\u5716\u6a23\u5f0f\u3002\n"
"\u5efa\u8b70\uff1a\u6df1\u8272\u8def\u7dda\u53ef\u7528 DarkMatter\uff0c\u9053\u8def\u7d30\u7bc0\u53ef\u7528 Voyager\uff0c\u885b\u661f\u5716\u8cc7\u8a0a\u91cf\u6700\u9ad8\u3002", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.lbl_camera_mode_2.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u6c7a\u5b9a\u8def\u7dda\u52d5\u756b\u7684\u93e1\u982d\u8996\u89d2\u671d\u5411\u8207 3D \u5730\u5f62\u900f\u8996\u3002\n"
"\u2022 \u6b63\u5317\u671d\u4e0a (North-Up)\n"
"\u2022 \u8ddf\u96a8\u884c\u9032\u65b9\u5411 (Heading-Up)\n"
"\u2022 3D \u771f\u5730\u5f62 (3D-Terrain)", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_camera_mode_2.setText(QCoreApplication.translate("MainWindow", u"\u8996\u89d2\u6a21\u5f0f\uff1a", None))
#if QT_CONFIG(tooltip)
        self.combo_camera_mode_2.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u6c7a\u5b9a\u8def\u7dda\u52d5\u756b\u7684\u93e1\u982d\u8996\u89d2\u671d\u5411\u8207 3D \u5730\u5f62\u900f\u8996\u3002\n"
"\u2022 \u6b63\u5317\u671d\u4e0a (North-Up)\n"
"\u2022 \u8ddf\u96a8\u884c\u9032\u65b9\u5411 (Heading-Up)\n"
"\u2022 3D \u771f\u5730\u5f62 (3D-Terrain)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.lbl_track_color_2.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u63a7\u5236\u4e3b\u756b\u9762\u8ecc\u8de1\u7dda\u689d\u8207\u5347\u964d\u5f69\u5e36\u7684\u914d\u8272\u98a8\u683c\u3002\n"
"\u2022 \u6d77\u62d4\u52d5\u614b\u6f38\u5c64\n"
"\u2022 \u4eae\u7da0\u3001\u9ec3\u3001\u7d05\u55ae\u8272\n"
"\u2022 \u9a0e\u4e58\u901f\u5ea6\u6f38\u5c64", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_track_color_2.setText(QCoreApplication.translate("MainWindow", u"\u8ecc\u8de1\u984f\u8272\uff1a", None))
#if QT_CONFIG(tooltip)
        self.combo_track_color_2.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u63a7\u5236\u4e3b\u756b\u9762\u8ecc\u8de1\u7dda\u689d\u8207\u5347\u964d\u5f69\u5e36\u7684\u914d\u8272\u98a8\u683c\u3002\n"
"\u2022 \u6d77\u62d4\u52d5\u614b\u6f38\u5c64\n"
"\u2022 \u4eae\u7da0\u3001\u9ec3\u3001\u7d05\u55ae\u8272\n"
"\u2022 \u9a0e\u4e58\u901f\u5ea6\u6f38\u5c64", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.lbl_local_zoom.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u6c7a\u5b9a\u4e3b\u52d5\u756b\u5c40\u90e8\u5e95\u5716\u4e0b\u8f09\u7684\u5730\u5716\u7e2e\u653e\u5c64\u7d1a\uff08\u9810\u8a2d 17 \u6216 auto\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_local_zoom.setText(QCoreApplication.translate("MainWindow", u"\u5730\u5716\u5c64\u7d1a\uff1a", None))
#if QT_CONFIG(tooltip)
        self.combo_local_zoom.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u6c7a\u5b9a\u4e3b\u52d5\u756b\u5c40\u90e8\u5e95\u5716\u4e0b\u8f09\u7684\u5730\u5716\u7e2e\u653e\u5c64\u7d1a\uff08\u9810\u8a2d 17 \u6216 auto\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.lbl_view_margin.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u63a7\u5236\u4e3b\u52d5\u756b\u93e1\u982d\u5728\u6469\u6258\u8eca\u4f4d\u7f6e\u5468\u570d\u4e00\u6b21\u770b\u591a\u5927\u7684\u5be6\u969b\u5730\u7406\u7bc4\u570d\uff08\u516c\u5c3a\uff0c\u9810\u8a2d800\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_view_margin.setText(QCoreApplication.translate("MainWindow", u"\u8996\u89d2\u8ddd\u96e2\uff1a", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_view_margin.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u63a7\u5236\u4e3b\u52d5\u756b\u93e1\u982d\u5728\u6469\u6258\u8eca\u4f4d\u7f6e\u5468\u570d\u4e00\u6b21\u770b\u591a\u5927\u7684\u5be6\u969b\u5730\u7406\u7bc4\u570d\uff08\u516c\u5c3a\uff0c\u9810\u8a2d 800\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_view_margin.setText(QCoreApplication.translate("MainWindow", u"800", None))
#if QT_CONFIG(tooltip)
        self.lbl_hide_privacy.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u63a7\u5236\u4e3b\u52d5\u756b\u524d\u6bb5\u96b1\u85cf\u7684 GPX \u8ecc\u8de1\u8ddd\u96e2 (0~50 km)\uff0c\u4fdd\u8b77\u8d77\u9ede\u96b1\u79c1\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_hide_privacy.setText(QCoreApplication.translate("MainWindow", u"\u8def\u7dda\u96b1\u85cf\uff1a", None))
        self.spin_hide_start.setPrefix(QCoreApplication.translate("MainWindow", u"\u8d77\u9ede ", None))
        self.spin_hide_start.setSuffix(QCoreApplication.translate("MainWindow", u" k", None))
        self.lbl_hide_end_3.setText(QCoreApplication.translate("MainWindow", u"/", None))
        self.spin_hide_end.setPrefix(QCoreApplication.translate("MainWindow", u"\u7d42\u9ede ", None))
        self.spin_hide_end.setSuffix(QCoreApplication.translate("MainWindow", u" k", None))
#if QT_CONFIG(tooltip)
        self.chk_dynamic_speed_zoom.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u6839\u64da\u7576\u524d GPX \u9a0e\u4e58\u901f\u5ea6\u52d5\u614b\u7e2e\u653e\u93e1\u982d\uff08\u9ad8\u901f\u62c9\u9060\u3001\u4f4e\u901f\u62c9\u8fd1\uff09\uff0c\u5982\u540c\u8eca\u7528\u5c0e\u822a\u8996\u89ba\u6548\u679c\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.chk_dynamic_speed_zoom.setText(QCoreApplication.translate("MainWindow", u"\u901f\u5ea6\u52d5\u614b\u93e1\u982d", None))
#if QT_CONFIG(tooltip)
        self.chk_real_speed_2.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u63a7\u5236\u9a0e\u4e58\u52d5\u756b\u5728\u8def\u7dda\u4e0a\u7684\u79fb\u52d5\u901f\u5ea6\u6a21\u5f0f\uff08\u7b49\u901f vs \u5be6\u969b GPS \u901f\u5ea6\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.chk_real_speed_2.setText(QCoreApplication.translate("MainWindow", u"\u8ddf\u96a8 GPX \u5be6\u969b\u901f\u5ea6", None))
        self.groupBox_workers.setTitle(QCoreApplication.translate("MainWindow", u"\u6e32\u67d3\u9032\u5ea6", None))
        self.label_eta_elapsed.setText(QCoreApplication.translate("MainWindow", u"\u7d93\u904e\u6642\u9593: 00:00:00", None))
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
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_general), QCoreApplication.translate("MainWindow", u"\u8a2d\u5b9a", None))
        self.top_group.setTitle(QCoreApplication.translate("MainWindow", u" \u5a92\u9ad4\u64ad\u653e\u8207\u8aaa\u660e\u8a2d\u5b9a ", None))
#if QT_CONFIG(tooltip)
        self.lbl_preview_resolution.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u9078\u64c7\u8f38\u51fa\u5f71\u7247\u7684\u89e3\u6790\u5ea6\u5c3a\u5bf8\u8207\u756b\u9762\u6bd4\u4f8b\uff089:16, 16:9, 1:1 \u7b49\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_preview_resolution.setText(QCoreApplication.translate("MainWindow", u"\u89e3\u6790\u5ea6\uff1a", None))
#if QT_CONFIG(tooltip)
        self.combo_preview_resolution.setToolTip(QCoreApplication.translate("MainWindow", u"\u5207\u63db\u9810\u89bd\u7684\u52d5\u756b\u9577\u5bec\u6bd4\u4f8b\u8207\u89e3\u6790\u5ea6\uff0c\u5373\u6642\u6aa2\u8996\u4e0d\u540c\u87a2\u5e55\u5c3a\u5bf8\u4e0b\u7684\u7167\u7247\u8207\u6587\u5b57\u6392\u7248", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.lbl_preview_map_style.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u6c7a\u5b9a\u5f71\u7247\u4e3b\u756b\u9762\u8207\u7d50\u5c3e overview \u4f7f\u7528\u7684\u5e95\u5716\u6a23\u5f0f\u3002\n"
"\u5efa\u8b70\uff1a\u6df1\u8272\u8def\u7dda\u53ef\u7528 DarkMatter\uff0c\u9053\u8def\u7d30\u7bc0\u53ef\u7528 Voyager\uff0c\u885b\u661f\u5716\u8cc7\u8a0a\u91cf\u6700\u9ad8\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_preview_map_style.setText(QCoreApplication.translate("MainWindow", u"\u5730\u5716\u98a8\u683c\uff1a", None))
#if QT_CONFIG(tooltip)
        self.combo_preview_map_style.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u6c7a\u5b9a\u5f71\u7247\u4e3b\u756b\u9762\u8207\u7d50\u5c3e overview \u4f7f\u7528\u7684\u5e95\u5716\u6a23\u5f0f\u3002\n"
"\u5efa\u8b70\uff1a\u6df1\u8272\u8def\u7dda\u53ef\u7528 DarkMatter\uff0c\u9053\u8def\u7d30\u7bc0\u53ef\u7528 Voyager\uff0c\u885b\u661f\u5716\u8cc7\u8a0a\u91cf\u6700\u9ad8\u3002", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.lbl_preview_camera_mode.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u6c7a\u5b9a\u8def\u7dda\u52d5\u756b\u7684\u93e1\u982d\u8996\u89d2\u671d\u5411\u8207 3D \u5730\u5f62\u900f\u8996\u3002\n"
"\u2022 \u6b63\u5317\u671d\u4e0a (North-Up)\n"
"\u2022 \u8ddf\u96a8\u884c\u9032\u65b9\u5411 (Heading-Up)\n"
"\u2022 3D \u771f\u5730\u5f62 (3D-Terrain)", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_preview_camera_mode.setText(QCoreApplication.translate("MainWindow", u"\u8996\u89d2\u6a21\u5f0f\uff1a", None))
#if QT_CONFIG(tooltip)
        self.combo_preview_camera_mode.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u6c7a\u5b9a\u8def\u7dda\u52d5\u756b\u7684\u93e1\u982d\u8996\u89d2\u671d\u5411\u8207 3D \u5730\u5f62\u900f\u8996\u3002\n"
"\u2022 \u6b63\u5317\u671d\u4e0a (North-Up)\n"
"\u2022 \u8ddf\u96a8\u884c\u9032\u65b9\u5411 (Heading-Up)\n"
"\u2022 3D \u771f\u5730\u5f62 (3D-Terrain)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.lbl_panels_2.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u63a7\u5236\u662f\u5426\u5728\u52d5\u756b\u4e3b\u756b\u9762\u4e2d\u986f\u793a\u901f\u5ea6\u5100\u8868\u3001\u8def\u7dda\u7e2e\u5716\u6216\u6d77\u62d4\u9ad8\u5ea6\u5256\u9762\u5716\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_panels_2.setText(QCoreApplication.translate("MainWindow", u"\u8cc7\u8a0a\u9762\u677f\uff1a", None))
#if QT_CONFIG(tooltip)
        self.combo_hud_panels.setToolTip(QCoreApplication.translate("MainWindow", u"\u9ede\u64ca\u53ef\u8907\u9078\u6216\u53d6\u6d88\u8981\u5728\u9810\u89bd\u756b\u9762\u8207\u8f38\u51fa\u5f71\u7247\u4e2d\u986f\u793a\u7684\u8cc7\u8a0a\u9762\u677f", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.label_distance_info.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u4f9d GPX \u7e3d\u8ddd\u96e2\u81ea\u52d5\u8a08\u7b97\u4e3b\u52d5\u756b\u9577\u5ea6\uff0c\u8b93\u4e0d\u540c\u9577\u5ea6\u7684\u9a0e\u4e58\u8def\u7dda\u4fdd\u6301\u76f8\u8fd1\u7bc0\u594f\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.label_distance_info.setText(QCoreApplication.translate("MainWindow", u"GPX \u8ddd\u96e2\uff1a-- km (\u81ea\u52d5\u6642\u9577 --s)", None))
#if QT_CONFIG(tooltip)
        self.lbl_duration.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u63a7\u5236\u6469\u6258\u8eca\u6cbf GPX \u8def\u5f91\u64ad\u653e\u7684\u4e3b\u52d5\u756b\u9577\u5ea6\uff08\u79d2\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_duration.setText(QCoreApplication.translate("MainWindow", u"\u4e3b\u52d5\u756b\uff1a", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_duration.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u63a7\u5236\u6469\u6258\u8eca\u6cbf GPX \u8def\u5f91\u64ad\u653e\u7684\u4e3b\u52d5\u756b\u9577\u5ea6\uff08\u79d2\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_duration.setText("")
#if QT_CONFIG(tooltip)
        self.lbl_end_hold.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u5b8c\u6574\u8def\u5f91\u8207 RIDE STATS \u51fa\u73fe\u5f8c\uff0c\u756b\u9762\u7dad\u6301\u591a\u4e45\u518d\u7d50\u675f\u5f71\u7247\uff08\u79d2\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_end_hold.setText(QCoreApplication.translate("MainWindow", u"\u7d50\u5c3e\u505c\u7559\uff1a", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_end_hold.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u5b8c\u6574\u8def\u5f91\u8207 RIDE STATS \u51fa\u73fe\u5f8c\uff0c\u756b\u9762\u7dad\u6301\u591a\u4e45\u518d\u7d50\u675f\u5f71\u7247\uff08\u79d2\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_end_hold.setInputMask("")
        self.lineEdit_end_hold.setText("")
#if QT_CONFIG(tooltip)
        self.lbl_zoomout.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u4e3b\u52d5\u756b\u8dd1\u5b8c\u5f8c\uff0c\u93e1\u982d\u5f9e\u5c40\u90e8\u8996\u89d2\u62c9\u9060\u5230\u5b8c\u6574\u8def\u7dda overview \u6240\u82b1\u7684\u6642\u9593\uff08\u79d2\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_zoomout.setText(QCoreApplication.translate("MainWindow", u"Zoom-out\uff1a", None))
#if QT_CONFIG(tooltip)
        self.lineEdit_zoomout.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u4e3b\u52d5\u756b\u8dd1\u5b8c\u5f8c\uff0c\u93e1\u982d\u5f9e\u5c40\u90e8\u8996\u89d2\u62c9\u9060\u5230\u5b8c\u6574\u8def\u7dda overview \u6240\u82b1\u7684\u6642\u9593\uff08\u79d2\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lineEdit_zoomout.setText(QCoreApplication.translate("MainWindow", u"2.5", None))
        self.lbl_photo_dur_title.setText(QCoreApplication.translate("MainWindow", u"\u5a92\u9ad4\u505c\u7559\uff1a", None))
        self.spin_photo_dur.setSuffix(QCoreApplication.translate("MainWindow", u" \u79d2", None))
#if QT_CONFIG(tooltip)
        self.btn_reset_defaults.setToolTip(QCoreApplication.translate("MainWindow", u"\u5c07\u6240\u6709\u7167\u7247\u8a2d\u70ba\u9810\u8a2d\u505c\u7559\u79d2\u6578\u8207\u9810\u8a2d\u8aaa\u660e\u5b57\u7d1a\uff0c\u6240\u6709\u5f71\u7247\u9084\u539f\u70ba\u539f\u59cb\u7247\u9577", None))
#endif // QT_CONFIG(tooltip)
        self.btn_reset_defaults.setText(QCoreApplication.translate("MainWindow", u"\u5168\u90e8\u5957\u7528", None))
        self.lbl_caption_size_title.setText(QCoreApplication.translate("MainWindow", u"\u6587\u5b57\u5927\u5c0f\uff1a", None))
#if QT_CONFIG(tooltip)
        self.spin_default_caption_size.setToolTip(QCoreApplication.translate("MainWindow", u"\u8a2d\u5b9a\u8aaa\u660e\u6587\u5b57\u4e4b\u9810\u8a2d\u5b57\u7d1a\u5927\u5c0f (50~80 pt)", None))
#endif // QT_CONFIG(tooltip)
        self.spin_default_caption_size.setSuffix(QCoreApplication.translate("MainWindow", u" pt", None))
#if QT_CONFIG(tooltip)
        self.lbl_rate.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u81ea\u52d5\u6642\u9577\u7684\u7bc0\u594f\u500d\u7387\u3002\u516c\u5f0f\u7d04\u70ba\uff1a\u8ddd\u96e2 km \u00f7 100 \u00d7 \u6b64\u6578\u503c\uff08\u9810\u8a2d 60 \u79d2/100km\uff09\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_rate.setText(QCoreApplication.translate("MainWindow", u"\u81ea\u52d5\u6642\u9577\u500d\u7387\uff1a", None))
        self.spin_seconds_per_100km.setSuffix(QCoreApplication.translate("MainWindow", u"  \u79d2 / 100km", None))
        self.spin_seconds_per_100km.setPrefix("")
#if QT_CONFIG(tooltip)
        self.chk_auto_duration.setToolTip(QCoreApplication.translate("MainWindow", u"\u7528\u9014\uff1a\u4f9d GPX \u7e3d\u8ddd\u96e2\u81ea\u52d5\u8a08\u7b97\u4e3b\u52d5\u756b\u9577\u5ea6\uff0c\u8b93\u4e0d\u540c\u9577\u5ea6\u7684\u9a0e\u4e58\u8def\u7dda\u4fdd\u6301\u76f8\u8fd1\u7bc0\u594f\u3002", None))
#endif // QT_CONFIG(tooltip)
        self.chk_auto_duration.setText("")
        self.group_media_list.setTitle(QCoreApplication.translate("MainWindow", u"\u5a92\u9ad4\u6e05\u55ae (\u5171 0 \u9805)", None))
        ___qtablewidgetitem = self.table.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MainWindow", u"\u6a94\u540d", None))
        ___qtablewidgetitem1 = self.table.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MainWindow", u"\u985e\u578b", None))
        ___qtablewidgetitem2 = self.table.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("MainWindow", u"\u505c\u7559\u79d2\u6578", None))
        ___qtablewidgetitem3 = self.table.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("MainWindow", u"\u62cd\u651d\u6642\u9593", None))
        ___qtablewidgetitem4 = self.table.horizontalHeaderItem(4)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("MainWindow", u"\u5339\u914d\u91cc\u7a0b (km)", None))
        ___qtablewidgetitem5 = self.table.horizontalHeaderItem(5)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("MainWindow", u"\u81ea\u8a02\u8aaa\u660e", None))
        ___qtablewidgetitem6 = self.table.horizontalHeaderItem(6)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("MainWindow", u"\u5b57\u7d1a (pt)", None))
        ___qtablewidgetitem7 = self.table.horizontalHeaderItem(7)
        ___qtablewidgetitem7.setText(QCoreApplication.translate("MainWindow", u"\u64cd\u4f5c", None))
#if QT_CONFIG(tooltip)
        self.btn_add_files.setToolTip(QCoreApplication.translate("MainWindow", u"\u9078\u53d6\u55ae\u5f35\u6216\u591a\u5f35\u7167\u7247/\u5f71\u7247\u6a94\u6848\u52a0\u5165\u6e05\u55ae", None))
#endif // QT_CONFIG(tooltip)
        self.btn_add_files.setText(QCoreApplication.translate("MainWindow", u"\u2795 \u65b0\u589e\u5a92\u9ad4", None))
#if QT_CONFIG(tooltip)
        self.btn_add_folder.setToolTip(QCoreApplication.translate("MainWindow", u"\u9078\u53d6\u5305\u542b\u7167\u7247/\u5f71\u7247\u4e4b\u8cc7\u6599\u593e\u52a0\u5165\u6e05\u55ae", None))
#endif // QT_CONFIG(tooltip)
        self.btn_add_folder.setText(QCoreApplication.translate("MainWindow", u"\U0001f4c1 \U000065b0\U0000589e\U00008cc7\U00006599\U0000593e", None))
        self.info_group.setTitle(QCoreApplication.translate("MainWindow", u" \u62cd\u651d\u8207 EXIF \u8cc7\u8a0a ", None))
        self.lbl_fn_title.setText(QCoreApplication.translate("MainWindow", u"\U0001f4c1 \U00006a94\U00006848\U0000ff1a", None))
        self.lbl_info_filename.setText(QCoreApplication.translate("MainWindow", u"-", None))
        self.lbl_time_title.setText(QCoreApplication.translate("MainWindow", u"\U0001f4c5 \U00006642\U00009593\U0000ff1a", None))
        self.lbl_info_time.setText(QCoreApplication.translate("MainWindow", u"-", None))
        self.lbl_gps_title.setText(QCoreApplication.translate("MainWindow", u"\U0001f4cd GPS\U0000ff1a", None))
        self.lbl_info_gps.setText(QCoreApplication.translate("MainWindow", u"-", None))
        self.lbl_res_title.setText(QCoreApplication.translate("MainWindow", u"\U0001f4d0 \U00005c3a\U00005bf8\U0000ff1a", None))
        self.lbl_info_res.setText(QCoreApplication.translate("MainWindow", u"-", None))
        self.lbl_match_title.setText(QCoreApplication.translate("MainWindow", u"\U0001f4cf \U00005339\U0000914d\U0000ff1a", None))
        self.lbl_info_match.setText(QCoreApplication.translate("MainWindow", u"-", None))
        self.preview_group.setTitle(QCoreApplication.translate("MainWindow", u" \u5a92\u9ad4\u756b\u9762\u9810\u89bd", None))
#if QT_CONFIG(tooltip)
        self.lbl_preview_image.setToolTip(QCoreApplication.translate("MainWindow", u"\U0001f4a1 \U00009ede\U000064ca\U000053ef\U0000958b\U0000555f\U0000539f\U00006a94\U00006aa2\U00008996\U0000ff08\U000076f8\U00007247\U00005168\U000087a2\U00005e55\U0000539f\U00005716 / \U00005f71\U00007247\U000064ad\U0000653e\U0000ff09", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_preview_image.setText(QCoreApplication.translate("MainWindow", u"\U0001f4f7 \U00008acb\U00005f9e\U00006e05\U000055ae\U00006216\U00005730\U00005716\U00009078\U000053d6\U00007167\U00007247", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", u"\u8def\u7dda\u8ecc\u8de1\u9810\u89bd", None))
        self.lbl_map_hint.setText(QCoreApplication.translate("MainWindow", u"\U0001f4a1 \U00006ed1\U00009f20\U00006efe\U00008f2a\U00007e2e\U0000653e / \U000062d6\U000066f3\U00005e73\U000079fb / \U00009ede\U000064ca\U00006a58\U00008272\U00006a19\U00008a18\U00009078\U000053d6\U00007167\U00007247", None))
#if QT_CONFIG(tooltip)
        self.btn_zoom_in.setToolTip(QCoreApplication.translate("MainWindow", u"\u653e\u5927\u8996\u89d2 (Canvas Zoom In)", None))
#endif // QT_CONFIG(tooltip)
        self.btn_zoom_in.setText(QCoreApplication.translate("MainWindow", u"\u2795", None))
#if QT_CONFIG(tooltip)
        self.btn_zoom_out.setToolTip(QCoreApplication.translate("MainWindow", u"\u7e2e\u5c0f\u8996\u89d2 (Canvas Zoom Out)", None))
#endif // QT_CONFIG(tooltip)
        self.btn_zoom_out.setText(QCoreApplication.translate("MainWindow", u"\u2796", None))
#if QT_CONFIG(tooltip)
        self.btn_reset_view.setToolTip(QCoreApplication.translate("MainWindow", u"\u91cd\u8a2d\u8996\u89d2\u81f3\u8def\u7dda\u5168\u666f\u4e2d\u592e", None))
#endif // QT_CONFIG(tooltip)
        self.btn_reset_view.setText(QCoreApplication.translate("MainWindow", u"\U0001f504 ", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("MainWindow", u"\u8def\u7dda\u5a92\u9ad4\u7ba1\u7406", None))
        self.btn_start_render.setText(QCoreApplication.translate("MainWindow", u"\u958b\u59cb\u6e32\u67d3", None))
        self.btn_stop_render.setText(QCoreApplication.translate("MainWindow", u"\u505c\u6b62", None))
        self.menu_file.setTitle(QCoreApplication.translate("MainWindow", u"\u6a94\u6848(&F)", None))
        self.menu_edit.setTitle(QCoreApplication.translate("MainWindow", u"\u7de8\u8f2f\u8207\u5de5\u5177(&E)", None))
        self.menu_view.setTitle(QCoreApplication.translate("MainWindow", u"\u6aa2\u8996(&V)", None))
        self.menu_settings.setTitle(QCoreApplication.translate("MainWindow", u"\u8a2d\u5b9a(&S)", None))
        self.menu_profile.setTitle(QCoreApplication.translate("MainWindow", u"\u9810\u8a2d\u756b\u8cea\u98a8\u683c", None))
        self.menu_hud_panels.setTitle(QCoreApplication.translate("MainWindow", u"\u8cc7\u8a0a\u9762\u677f", None))
        self.menu_cache_mode.setTitle(QCoreApplication.translate("MainWindow", u"\u5730\u5716\u5feb\u53d6\u6a21\u5f0f", None))
        self.menu_nvenc_preset.setTitle(QCoreApplication.translate("MainWindow", u"\u7de8\u78bc\u5668\u9810\u8a2d\u6a94 (NVENC Preset)", None))
        self.menu_bitrate.setTitle(QCoreApplication.translate("MainWindow", u"\u5f71\u7247\u4f4d\u5143\u7387 (Bitrate)", None))
        self.menu_workers.setTitle(QCoreApplication.translate("MainWindow", u"\u591a\u9032\u7a0b\u5de5\u4f5c\u6578\u91cf (Workers)", None))
        self.menu_tile_connections.setTitle(QCoreApplication.translate("MainWindow", u"\u5730\u5716\u5716\u8cc7\u9023\u7dda\u6578 (Connections)", None))
        self.menu_help.setTitle(QCoreApplication.translate("MainWindow", u"\u8aaa\u660e(&H)", None))
        self.toolBar.setWindowTitle(QCoreApplication.translate("MainWindow", u"\u5feb\u6377\u5de5\u5177\u5217", None))
    # retranslateUi

