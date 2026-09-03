# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'media_dialogqGFUsl.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QDialog,
    QDoubleSpinBox, QGridLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QPushButton, QSizePolicy,
    QSpacerItem, QSpinBox, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget)

from gpx_renderer.gui.media_dialog.widgets.clickable_preview import ClickablePreviewLabel
from gpx_renderer.gui.media_dialog.widgets.route_preview_widget import QtRoutePreviewWidget

class Ui_MediaManagerDialog(object):
    def setupUi(self, MediaManagerDialog):
        if not MediaManagerDialog.objectName():
            MediaManagerDialog.setObjectName(u"MediaManagerDialog")
        MediaManagerDialog.resize(1200, 640)
        MediaManagerDialog.setMinimumSize(QSize(1200, 640))
        self.gridLayout_2 = QGridLayout(MediaManagerDialog)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.top_group = QGroupBox(MediaManagerDialog)
        self.top_group.setObjectName(u"top_group")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.top_group.sizePolicy().hasHeightForWidth())
        self.top_group.setSizePolicy(sizePolicy)
        self.top_group.setMinimumSize(QSize(0, 90))
        self.gridLayout_4 = QGridLayout(self.top_group)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.verticalLayout_7 = QVBoxLayout()
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.lbl_offset_title = QLabel(self.top_group)
        self.lbl_offset_title.setObjectName(u"lbl_offset_title")

        self.horizontalLayout_10.addWidget(self.lbl_offset_title)

        self.spin_media_offset = QDoubleSpinBox(self.top_group)
        self.spin_media_offset.setObjectName(u"spin_media_offset")
        sizePolicy.setHeightForWidth(self.spin_media_offset.sizePolicy().hasHeightForWidth())
        self.spin_media_offset.setSizePolicy(sizePolicy)
        self.spin_media_offset.setMinimum(-86400.000000000000000)
        self.spin_media_offset.setMaximum(86400.000000000000000)
        self.spin_media_offset.setSingleStep(1.000000000000000)
        self.spin_media_offset.setValue(0.000000000000000)

        self.horizontalLayout_10.addWidget(self.spin_media_offset)


        self.verticalLayout_7.addLayout(self.horizontalLayout_10)

        self.btn_realign = QPushButton(self.top_group)
        self.btn_realign.setObjectName(u"btn_realign")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.btn_realign.sizePolicy().hasHeightForWidth())
        self.btn_realign.setSizePolicy(sizePolicy1)

        self.verticalLayout_7.addWidget(self.btn_realign)

        self.lbl_hint = QLabel(self.top_group)
        self.lbl_hint.setObjectName(u"lbl_hint")
        self.lbl_hint.setStyleSheet(u"color: #718096; font-size: 11px;")

        self.verticalLayout_7.addWidget(self.lbl_hint)


        self.gridLayout_4.addLayout(self.verticalLayout_7, 0, 2, 1, 1)

        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.lbl_photo_dur_title = QLabel(self.top_group)
        self.lbl_photo_dur_title.setObjectName(u"lbl_photo_dur_title")

        self.horizontalLayout_8.addWidget(self.lbl_photo_dur_title)

        self.spin_photo_dur = QDoubleSpinBox(self.top_group)
        self.spin_photo_dur.setObjectName(u"spin_photo_dur")
        sizePolicy.setHeightForWidth(self.spin_photo_dur.sizePolicy().hasHeightForWidth())
        self.spin_photo_dur.setSizePolicy(sizePolicy)
        self.spin_photo_dur.setMinimum(1.000000000000000)
        self.spin_photo_dur.setMaximum(30.000000000000000)
        self.spin_photo_dur.setSingleStep(0.500000000000000)
        self.spin_photo_dur.setValue(3.000000000000000)

        self.horizontalLayout_8.addWidget(self.spin_photo_dur)


        self.gridLayout_3.addLayout(self.horizontalLayout_8, 0, 0, 1, 1)

        self.btn_reset_defaults = QPushButton(self.top_group)
        self.btn_reset_defaults.setObjectName(u"btn_reset_defaults")
        sizePolicy1.setHeightForWidth(self.btn_reset_defaults.sizePolicy().hasHeightForWidth())
        self.btn_reset_defaults.setSizePolicy(sizePolicy1)
        self.btn_reset_defaults.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.gridLayout_3.addWidget(self.btn_reset_defaults, 0, 1, 2, 1)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.lbl_caption_size_title = QLabel(self.top_group)
        self.lbl_caption_size_title.setObjectName(u"lbl_caption_size_title")

        self.horizontalLayout_9.addWidget(self.lbl_caption_size_title)

        self.spin_default_caption_size = QSpinBox(self.top_group)
        self.spin_default_caption_size.setObjectName(u"spin_default_caption_size")
        sizePolicy.setHeightForWidth(self.spin_default_caption_size.sizePolicy().hasHeightForWidth())
        self.spin_default_caption_size.setSizePolicy(sizePolicy)
        self.spin_default_caption_size.setMinimum(50)
        self.spin_default_caption_size.setMaximum(80)
        self.spin_default_caption_size.setSingleStep(1)
        self.spin_default_caption_size.setValue(50)

        self.horizontalLayout_9.addWidget(self.spin_default_caption_size)


        self.gridLayout_3.addLayout(self.horizontalLayout_9, 1, 0, 1, 1)


        self.gridLayout_4.addLayout(self.gridLayout_3, 0, 0, 1, 1)

        self.horizontalSpacer_top_2 = QSpacerItem(17, 58, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.gridLayout_4.addItem(self.horizontalSpacer_top_2, 0, 1, 1, 1)


        self.verticalLayout_3.addWidget(self.top_group)

        self.group_media_list = QGroupBox(MediaManagerDialog)
        self.group_media_list.setObjectName(u"group_media_list")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.group_media_list.sizePolicy().hasHeightForWidth())
        self.group_media_list.setSizePolicy(sizePolicy2)
        self.group_media_list.setMinimumSize(QSize(0, 0))
        self.group_media_list.setMaximumSize(QSize(16777215, 300))
        self.verticalLayout_2 = QVBoxLayout(self.group_media_list)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
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
        self.table.setMaximumSize(QSize(16777215, 16777215))
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setColumnCount(8)

        self.verticalLayout_2.addWidget(self.table)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer_table_hdr = QSpacerItem(163, 18, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_table_hdr)

        self.btn_add_files = QPushButton(self.group_media_list)
        self.btn_add_files.setObjectName(u"btn_add_files")
        self.btn_add_files.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.horizontalLayout.addWidget(self.btn_add_files)

        self.btn_add_folder = QPushButton(self.group_media_list)
        self.btn_add_folder.setObjectName(u"btn_add_folder")
        self.btn_add_folder.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.horizontalLayout.addWidget(self.btn_add_folder)


        self.verticalLayout_2.addLayout(self.horizontalLayout)


        self.verticalLayout_3.addWidget(self.group_media_list)

        self.groupBox_2 = QGroupBox(MediaManagerDialog)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.groupBox_2.setMinimumSize(QSize(0, 0))
        self.gridLayout = QGridLayout(self.groupBox_2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.preview_widget = QtRoutePreviewWidget(self.groupBox_2)
        self.preview_widget.setObjectName(u"preview_widget")
        self.verticalLayout_5 = QVBoxLayout(self.preview_widget)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.lbl_map_hint = QLabel(self.preview_widget)
        self.lbl_map_hint.setObjectName(u"lbl_map_hint")
        self.lbl_map_hint.setStyleSheet(u"color: #718096; font-size: 11px;")
        self.lbl_map_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_5.addWidget(self.lbl_map_hint)


        self.verticalLayout.addWidget(self.preview_widget)


        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        self.map_toolbar = QHBoxLayout()
        self.map_toolbar.setObjectName(u"map_toolbar")
        self.lbl_map_header = QLabel(self.groupBox_2)
        self.lbl_map_header.setObjectName(u"lbl_map_header")
        font = QFont()
        font.setFamilies([u"Segoe UI"])
        font.setPointSize(9)
        font.setBold(True)
        self.lbl_map_header.setFont(font)

        self.map_toolbar.addWidget(self.lbl_map_header)

        self.horizontalSpacer_map_hdr = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.map_toolbar.addItem(self.horizontalSpacer_map_hdr)

        self.btn_zoom_in = QPushButton(self.groupBox_2)
        self.btn_zoom_in.setObjectName(u"btn_zoom_in")

        self.map_toolbar.addWidget(self.btn_zoom_in)

        self.btn_zoom_out = QPushButton(self.groupBox_2)
        self.btn_zoom_out.setObjectName(u"btn_zoom_out")

        self.map_toolbar.addWidget(self.btn_zoom_out)

        self.btn_reset_view = QPushButton(self.groupBox_2)
        self.btn_reset_view.setObjectName(u"btn_reset_view")

        self.map_toolbar.addWidget(self.btn_reset_view)


        self.gridLayout.addLayout(self.map_toolbar, 1, 0, 1, 1)


        self.verticalLayout_3.addWidget(self.groupBox_2)


        self.horizontalLayout_2.addLayout(self.verticalLayout_3)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.preview_group = QGroupBox(MediaManagerDialog)
        self.preview_group.setObjectName(u"preview_group")
        sizePolicy2.setHeightForWidth(self.preview_group.sizePolicy().hasHeightForWidth())
        self.preview_group.setSizePolicy(sizePolicy2)
        self.preview_vbox = QVBoxLayout(self.preview_group)
        self.preview_vbox.setSpacing(6)
        self.preview_vbox.setObjectName(u"preview_vbox")
        self.preview_vbox.setContentsMargins(8, 8, 8, 8)
        self.res_row = QHBoxLayout()
        self.res_row.setObjectName(u"res_row")
        self.lbl_preview_res_title = QLabel(self.preview_group)
        self.lbl_preview_res_title.setObjectName(u"lbl_preview_res_title")

        self.res_row.addWidget(self.lbl_preview_res_title)

        self.combo_preview_res = QComboBox(self.preview_group)
        self.combo_preview_res.setObjectName(u"combo_preview_res")

        self.res_row.addWidget(self.combo_preview_res)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.res_row.addItem(self.horizontalSpacer_6)


        self.preview_vbox.addLayout(self.res_row)

        self.lbl_preview_image = ClickablePreviewLabel(self.preview_group)
        self.lbl_preview_image.setObjectName(u"lbl_preview_image")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.lbl_preview_image.sizePolicy().hasHeightForWidth())
        self.lbl_preview_image.setSizePolicy(sizePolicy3)
        self.lbl_preview_image.setMinimumSize(QSize(0, 160))
        self.lbl_preview_image.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.lbl_preview_image.setStyleSheet(u"background-color: #0b0f14; border: 1px solid #2d3748; border-radius: 8px; color: #a0aec0;")
        self.lbl_preview_image.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.preview_vbox.addWidget(self.lbl_preview_image)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.preview_vbox.addItem(self.verticalSpacer)

        self.info_group = QGroupBox(self.preview_group)
        self.info_group.setObjectName(u"info_group")
        sizePolicy.setHeightForWidth(self.info_group.sizePolicy().hasHeightForWidth())
        self.info_group.setSizePolicy(sizePolicy)
        self.info_group.setMinimumSize(QSize(0, 0))
        self.verticalLayout_6 = QVBoxLayout(self.info_group)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.lbl_fn_title = QLabel(self.info_group)
        self.lbl_fn_title.setObjectName(u"lbl_fn_title")

        self.horizontalLayout_3.addWidget(self.lbl_fn_title)

        self.lbl_info_filename = QLabel(self.info_group)
        self.lbl_info_filename.setObjectName(u"lbl_info_filename")
        self.lbl_info_filename.setStyleSheet(u"font-weight: bold; color: #e2e8f0;")
        self.lbl_info_filename.setWordWrap(True)

        self.horizontalLayout_3.addWidget(self.lbl_info_filename)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)


        self.verticalLayout_6.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.lbl_time_title = QLabel(self.info_group)
        self.lbl_time_title.setObjectName(u"lbl_time_title")

        self.horizontalLayout_4.addWidget(self.lbl_time_title)

        self.lbl_info_time = QLabel(self.info_group)
        self.lbl_info_time.setObjectName(u"lbl_info_time")
        self.lbl_info_time.setStyleSheet(u"color: #cbd5e0;")

        self.horizontalLayout_4.addWidget(self.lbl_info_time)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_2)


        self.verticalLayout_6.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.lbl_gps_title = QLabel(self.info_group)
        self.lbl_gps_title.setObjectName(u"lbl_gps_title")

        self.horizontalLayout_5.addWidget(self.lbl_gps_title)

        self.lbl_info_gps = QLabel(self.info_group)
        self.lbl_info_gps.setObjectName(u"lbl_info_gps")
        self.lbl_info_gps.setStyleSheet(u"color: #cbd5e0;")

        self.horizontalLayout_5.addWidget(self.lbl_info_gps)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_3)


        self.verticalLayout_6.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.lbl_res_title = QLabel(self.info_group)
        self.lbl_res_title.setObjectName(u"lbl_res_title")

        self.horizontalLayout_6.addWidget(self.lbl_res_title)

        self.lbl_info_res = QLabel(self.info_group)
        self.lbl_info_res.setObjectName(u"lbl_info_res")
        self.lbl_info_res.setStyleSheet(u"color: #cbd5e0;")

        self.horizontalLayout_6.addWidget(self.lbl_info_res)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_4)


        self.verticalLayout_6.addLayout(self.horizontalLayout_6)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.lbl_match_title = QLabel(self.info_group)
        self.lbl_match_title.setObjectName(u"lbl_match_title")

        self.horizontalLayout_7.addWidget(self.lbl_match_title)

        self.lbl_info_match = QLabel(self.info_group)
        self.lbl_info_match.setObjectName(u"lbl_info_match")
        self.lbl_info_match.setStyleSheet(u"color: #63b3ed; font-weight: bold;")

        self.horizontalLayout_7.addWidget(self.lbl_info_match)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_5)


        self.verticalLayout_6.addLayout(self.horizontalLayout_7)


        self.preview_vbox.addWidget(self.info_group)


        self.verticalLayout_4.addWidget(self.preview_group)


        self.horizontalLayout_2.addLayout(self.verticalLayout_4)


        self.gridLayout_2.addLayout(self.horizontalLayout_2, 0, 0, 1, 1)

        self.bottom_bar = QHBoxLayout()
        self.bottom_bar.setObjectName(u"bottom_bar")
        self.btn_reset_all = QPushButton(MediaManagerDialog)
        self.btn_reset_all.setObjectName(u"btn_reset_all")

        self.bottom_bar.addWidget(self.btn_reset_all)

        self.horizontalSpacer_bottom = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.bottom_bar.addItem(self.horizontalSpacer_bottom)

        self.btn_save = QPushButton(MediaManagerDialog)
        self.btn_save.setObjectName(u"btn_save")
        font1 = QFont()
        font1.setFamilies([u"Segoe UI"])
        font1.setPointSize(10)
        font1.setBold(True)
        self.btn_save.setFont(font1)
        self.btn_save.setStyleSheet(u"background-color: #2b6cb0; color: white; padding: 6px 16px; border-radius: 4px;")

        self.bottom_bar.addWidget(self.btn_save)

        self.btn_cancel = QPushButton(MediaManagerDialog)
        self.btn_cancel.setObjectName(u"btn_cancel")

        self.bottom_bar.addWidget(self.btn_cancel)


        self.gridLayout_2.addLayout(self.bottom_bar, 1, 0, 1, 1)


        self.retranslateUi(MediaManagerDialog)

        QMetaObject.connectSlotsByName(MediaManagerDialog)
    # setupUi

    def retranslateUi(self, MediaManagerDialog):
        MediaManagerDialog.setWindowTitle(QCoreApplication.translate("MediaManagerDialog", u"\u8def\u7dda\u5a92\u9ad4\u7ba1\u7406\u5668\u8207\u7167\u7247/\u5f71\u7247\u6a19\u7c64\u7de8\u8f2f\u5668 (PySide6 Native)", None))
        self.top_group.setTitle(QCoreApplication.translate("MediaManagerDialog", u" \u5a92\u9ad4\u64ad\u653e\u8207\u8aaa\u660e\u8a2d\u5b9a ", None))
        self.lbl_offset_title.setText(QCoreApplication.translate("MediaManagerDialog", u"\u76f8\u6a5f\u6642\u9593\u6821\u6b63\u504f\u79fb\uff1a", None))
        self.spin_media_offset.setSuffix(QCoreApplication.translate("MediaManagerDialog", u" \u79d2", None))
#if QT_CONFIG(tooltip)
        self.btn_realign.setToolTip(QCoreApplication.translate("MediaManagerDialog", u"\u4f9d\u64da\u4e0a\u65b9\u6821\u6b63\u79d2\u6578\uff0c\u91cd\u65b0\u8207 GPX \u6642\u9593\u8ef8\u5339\u914d\u9ede\u4f4d", None))
#endif // QT_CONFIG(tooltip)
        self.btn_realign.setText(QCoreApplication.translate("MediaManagerDialog", u"\u23f1\ufe0f \u91cd\u65b0\u5c0d\u9f4a\u6642\u9593", None))
        self.lbl_hint.setText(QCoreApplication.translate("MediaManagerDialog", u"\U0001f4a1 \U00006162 1 \U00005206\U0000586b 60s\U0000ff1b\U00005feb 1 \U00005206\U0000586b -60s", None))
        self.lbl_photo_dur_title.setText(QCoreApplication.translate("MediaManagerDialog", u"\U0001f4f7 \U000076f8\U00007247\U00009810\U00008a2d\U0000505c\U00007559\U0000ff1a", None))
        self.spin_photo_dur.setSuffix(QCoreApplication.translate("MediaManagerDialog", u" \u79d2", None))
#if QT_CONFIG(tooltip)
        self.btn_reset_defaults.setToolTip(QCoreApplication.translate("MediaManagerDialog", u"\u5c07\u6240\u6709\u7167\u7247\u8a2d\u70ba\u9810\u8a2d\u505c\u7559\u79d2\u6578\u8207\u9810\u8a2d\u8aaa\u660e\u5b57\u7d1a\uff0c\u6240\u6709\u5f71\u7247\u9084\u539f\u70ba\u539f\u59cb\u7247\u9577", None))
#endif // QT_CONFIG(tooltip)
        self.btn_reset_defaults.setText(QCoreApplication.translate("MediaManagerDialog", u"\u26a1 \u4e00\u9375\u5957\u7528\u9810\u8a2d\u503c (\u505c\u7559/\u5b57\u7d1a)", None))
        self.lbl_caption_size_title.setText(QCoreApplication.translate("MediaManagerDialog", u"\U0001f524 \U00008aaa\U0000660e\U00009810\U00008a2d\U00005b57\U00007d1a\U0000ff1a", None))
#if QT_CONFIG(tooltip)
        self.spin_default_caption_size.setToolTip(QCoreApplication.translate("MediaManagerDialog", u"\u8a2d\u5b9a\u8aaa\u660e\u6587\u5b57\u4e4b\u9810\u8a2d\u5b57\u7d1a\u5927\u5c0f (50~80 pt)", None))
#endif // QT_CONFIG(tooltip)
        self.spin_default_caption_size.setSuffix(QCoreApplication.translate("MediaManagerDialog", u" pt", None))
        self.group_media_list.setTitle(QCoreApplication.translate("MediaManagerDialog", u"\u5a92\u9ad4\u6e05\u55ae (\u5171 0 \u9805)", None))
        ___qtablewidgetitem = self.table.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MediaManagerDialog", u"\u6a94\u540d", None))
        ___qtablewidgetitem1 = self.table.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MediaManagerDialog", u"\u985e\u578b", None))
        ___qtablewidgetitem2 = self.table.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("MediaManagerDialog", u"\u505c\u7559\u79d2\u6578", None))
        ___qtablewidgetitem3 = self.table.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("MediaManagerDialog", u"\u62cd\u651d\u6642\u9593", None))
        ___qtablewidgetitem4 = self.table.horizontalHeaderItem(4)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("MediaManagerDialog", u"\u5339\u914d\u91cc\u7a0b (km)", None))
        ___qtablewidgetitem5 = self.table.horizontalHeaderItem(5)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("MediaManagerDialog", u"\u81ea\u8a02\u8aaa\u660e", None))
        ___qtablewidgetitem6 = self.table.horizontalHeaderItem(6)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("MediaManagerDialog", u"\u5b57\u7d1a (pt)", None))
        ___qtablewidgetitem7 = self.table.horizontalHeaderItem(7)
        ___qtablewidgetitem7.setText(QCoreApplication.translate("MediaManagerDialog", u"\u64cd\u4f5c", None))
#if QT_CONFIG(tooltip)
        self.btn_add_files.setToolTip(QCoreApplication.translate("MediaManagerDialog", u"\u9078\u53d6\u55ae\u5f35\u6216\u591a\u5f35\u7167\u7247/\u5f71\u7247\u6a94\u6848\u52a0\u5165\u6e05\u55ae", None))
#endif // QT_CONFIG(tooltip)
        self.btn_add_files.setText(QCoreApplication.translate("MediaManagerDialog", u"\u2795 \u65b0\u589e\u7167\u7247/\u5f71\u7247 (\u53ef\u591a\u9078)", None))
#if QT_CONFIG(tooltip)
        self.btn_add_folder.setToolTip(QCoreApplication.translate("MediaManagerDialog", u"\u9078\u53d6\u5305\u542b\u7167\u7247/\u5f71\u7247\u4e4b\u8cc7\u6599\u593e\u52a0\u5165\u6e05\u55ae", None))
#endif // QT_CONFIG(tooltip)
        self.btn_add_folder.setText(QCoreApplication.translate("MediaManagerDialog", u"\U0001f4c1 \U000065b0\U0000589e\U00008cc7\U00006599\U0000593e", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MediaManagerDialog", u"\u8def\u7dda\u8ecc\u8de1\u9810\u89bd", None))
        self.lbl_map_hint.setText(QCoreApplication.translate("MediaManagerDialog", u"\U0001f4a1 \U00006ed1\U00009f20\U00006efe\U00008f2a\U00007e2e\U0000653e / \U000062d6\U000066f3\U00005e73\U000079fb / \U00009ede\U000064ca\U00006a58\U00008272\U00006a19\U00008a18\U00009078\U000053d6\U00007167\U00007247", None))
        self.lbl_map_header.setText("")
#if QT_CONFIG(tooltip)
        self.btn_zoom_in.setToolTip(QCoreApplication.translate("MediaManagerDialog", u"\u653e\u5927\u8996\u89d2 (Canvas Zoom In)", None))
#endif // QT_CONFIG(tooltip)
        self.btn_zoom_in.setText(QCoreApplication.translate("MediaManagerDialog", u"\u2795 \u653e\u5927", None))
#if QT_CONFIG(tooltip)
        self.btn_zoom_out.setToolTip(QCoreApplication.translate("MediaManagerDialog", u"\u7e2e\u5c0f\u8996\u89d2 (Canvas Zoom Out)", None))
#endif // QT_CONFIG(tooltip)
        self.btn_zoom_out.setText(QCoreApplication.translate("MediaManagerDialog", u"\u2796 \u7e2e\u5c0f", None))
#if QT_CONFIG(tooltip)
        self.btn_reset_view.setToolTip(QCoreApplication.translate("MediaManagerDialog", u"\u91cd\u8a2d\u8996\u89d2\u81f3\u8def\u7dda\u5168\u666f\u4e2d\u592e", None))
#endif // QT_CONFIG(tooltip)
        self.btn_reset_view.setText(QCoreApplication.translate("MediaManagerDialog", u"\U0001f504 \U00008996\U000091ce\U00007f6e\U00004e2d", None))
        self.preview_group.setTitle(QCoreApplication.translate("MediaManagerDialog", u" \u5a92\u9ad4\u756b\u9762\u9810\u89bd (\u52d5\u756b\u89e3\u6790\u5ea6\u540c\u6b65\u6a21\u64ec) ", None))
        self.lbl_preview_res_title.setText(QCoreApplication.translate("MediaManagerDialog", u"\U0001f3ac \U00006a21\U000064ec\U000089e3\U00006790\U00005ea6\U0000ff1a", None))
#if QT_CONFIG(tooltip)
        self.combo_preview_res.setToolTip(QCoreApplication.translate("MediaManagerDialog", u"\u5207\u63db\u9810\u89bd\u7684\u52d5\u756b\u9577\u5bec\u6bd4\u4f8b\u8207\u89e3\u6790\u5ea6\uff0c\u5373\u6642\u6aa2\u8996\u4e0d\u540c\u87a2\u5e55\u5c3a\u5bf8\u4e0b\u7684\u7167\u7247\u8207\u6587\u5b57\u6392\u7248", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.lbl_preview_image.setToolTip(QCoreApplication.translate("MediaManagerDialog", u"\U0001f4a1 \U00009ede\U000064ca\U000053ef\U0000958b\U0000555f\U0000539f\U00006a94\U00006aa2\U00008996\U0000ff08\U000076f8\U00007247\U00005168\U000087a2\U00005e55\U0000539f\U00005716 / \U00005f71\U00007247\U000064ad\U0000653e\U0000ff09", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_preview_image.setText(QCoreApplication.translate("MediaManagerDialog", u"\U0001f4f7 \U00008acb\U00005f9e\U00006e05\U000055ae\U00006216\U00005730\U00005716\U00009078\U000053d6\U00007167\U00007247", None))
        self.info_group.setTitle(QCoreApplication.translate("MediaManagerDialog", u" \u62cd\u651d\u8207 EXIF \u8cc7\u8a0a ", None))
        self.lbl_fn_title.setText(QCoreApplication.translate("MediaManagerDialog", u"\U0001f4c1 \U00006a94\U00006848\U0000ff1a", None))
        self.lbl_info_filename.setText(QCoreApplication.translate("MediaManagerDialog", u"-", None))
        self.lbl_time_title.setText(QCoreApplication.translate("MediaManagerDialog", u"\U0001f4c5 \U00006642\U00009593\U0000ff1a", None))
        self.lbl_info_time.setText(QCoreApplication.translate("MediaManagerDialog", u"-", None))
        self.lbl_gps_title.setText(QCoreApplication.translate("MediaManagerDialog", u"\U0001f4cd GPS\U0000ff1a", None))
        self.lbl_info_gps.setText(QCoreApplication.translate("MediaManagerDialog", u"-", None))
        self.lbl_res_title.setText(QCoreApplication.translate("MediaManagerDialog", u"\U0001f4d0 \U00005c3a\U00005bf8\U0000ff1a", None))
        self.lbl_info_res.setText(QCoreApplication.translate("MediaManagerDialog", u"-", None))
        self.lbl_match_title.setText(QCoreApplication.translate("MediaManagerDialog", u"\U0001f4cf \U00005339\U0000914d\U0000ff1a", None))
        self.lbl_info_match.setText(QCoreApplication.translate("MediaManagerDialog", u"-", None))
        self.btn_reset_all.setText(QCoreApplication.translate("MediaManagerDialog", u"\U0001f504 \U000091cd\U00007f6e\U00006240\U00006709\U0000624b\U000052d5\U00008b8a\U000066f4", None))
        self.btn_save.setText(QCoreApplication.translate("MediaManagerDialog", u"\U0001f4be \U00005132\U00005b58\U00004e26\U00005957\U00007528", None))
        self.btn_cancel.setText(QCoreApplication.translate("MediaManagerDialog", u"\u53d6\u6d88", None))
    # retranslateUi

