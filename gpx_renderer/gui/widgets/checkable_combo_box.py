# -*- coding: utf-8 -*-
"""
CheckableComboBox
支援多選/複選 CheckBox 的 Qt 下拉選單元件。
針對 Modal 對話框、自訂樣式表與點擊事件做了完整防護與自適應支援。
"""

from PySide6.QtWidgets import QComboBox, QLineEdit, QListView
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt, Signal, QEvent


class CheckableComboBox(QComboBox):
    """支援複選 CheckBox 的自訂 QComboBox 元件。"""
    selection_changed = Signal(list)

    def __init__(self, parent=None, placeholder_text="請勾選面板..."):
        super().__init__(parent)
        self.placeholder_text = placeholder_text
        self.setEditable(True)
        
        le = self.lineEdit()
        if le:
            le.setReadOnly(True)
            le.setCursor(Qt.PointingHandCursor)
            le.installEventFilter(self)

        model = QStandardItemModel(self)
        self.setModel(model)
        
        # 確保 view 為標準 QListView 並監聽點擊與關閉行為
        view = self.view()
        view.viewport().installEventFilter(self)
        view.pressed.connect(self._handle_item_pressed)
        model.dataChanged.connect(self._on_data_changed)
        self._is_updating = False

    def eventFilter(self, obj, event):
        # 1. 點擊輸入框任何區域直接展開下拉選單
        if obj == self.lineEdit():
            if event.type() == QEvent.MouseButtonPress:
                self.showPopup()
                return True

        # 2. 攔截下拉清單視窗上的點擊，切換勾選狀態並避免選單立即關閉
        if self.view() and obj == self.view().viewport():
            if event.type() == QEvent.MouseButtonRelease:
                idx = self.view().indexAt(event.pos())
                if idx.isValid():
                    self._handle_item_pressed(idx)
                    return True

        return super().eventFilter(obj, event)

    def _handle_item_pressed(self, index):
        item = self.model().itemFromIndex(index)
        if item and item.isCheckable():
            new_state = Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked
            item.setCheckState(new_state)

    def _on_data_changed(self, top_left, bottom_right, roles):
        if Qt.CheckStateRole in roles and not self._is_updating:
            self._update_display_text()
            self.selection_changed.emit(self.checked_items())

    def add_checkable_item(self, text: str, data=None, checked: bool = True):
        """新增一個帶 CheckBox 的選項。"""
        self._is_updating = True
        item = QStandardItem(text)
        item.setCheckable(True)
        item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
        if data is not None:
            item.setData(data, Qt.UserRole)
        self.model().appendRow(item)
        self._is_updating = False
        self._update_display_text()

    def set_item_checked(self, index: int, checked: bool):
        """設定指定索引項目的勾選狀態。"""
        if 0 <= index < self.model().rowCount():
            item = self.model().item(index)
            target_state = Qt.Checked if checked else Qt.Unchecked
            if item.checkState() == target_state:
                return
            self._is_updating = True
            item.setCheckState(target_state)
            self._is_updating = False
            self._update_display_text()
            self.selection_changed.emit(self.checked_items())

    def set_item_checked_by_text(self, text: str, checked: bool):
        """以項目文字比對並設定勾選狀態。"""
        for row in range(self.model().rowCount()):
            item = self.model().item(row)
            if item and item.text() == text:
                self.set_item_checked(row, checked)
                break

    def set_item_checked_by_data(self, data, checked: bool):
        """以項目 UserData 比對並設定勾選狀態。"""
        for row in range(self.model().rowCount()):
            item = self.model().item(row)
            if item and item.data(Qt.UserRole) == data:
                self.set_item_checked(row, checked)
                break

    def is_item_checked(self, index: int) -> bool:
        """檢查指定索引項目是否已被勾選。"""
        if 0 <= index < self.model().rowCount():
            return self.model().item(index).checkState() == Qt.Checked
        return False

    def checked_items(self) -> list:
        """傳回所有已勾選項目的文字清單。"""
        res = []
        for row in range(self.model().rowCount()):
            item = self.model().item(row)
            if item.checkState() == Qt.Checked:
                res.append(item.text())
        return res

    def checked_data(self) -> list:
        """傳回所有已勾選項目的 UserData 清單。"""
        res = []
        for row in range(self.model().rowCount()):
            item = self.model().item(row)
            if item.checkState() == Qt.Checked:
                res.append(item.data(Qt.UserRole))
        return res

    def _update_display_text(self):
        """更新頂部主顯示文字。"""
        checked = self.checked_items()
        total = self.model().rowCount()
        if len(checked) == 0:
            txt = "全部隱藏 (乾淨畫面)"
        elif len(checked) == total:
            txt = "全部顯示 (HUD+地圖+高程)"
        else:
            txt = " + ".join(checked)
        if self.lineEdit():
            self.lineEdit().setText(txt)

    def showPopup(self):
        super().showPopup()
        self._update_display_text()

    def hidePopup(self):
        super().hidePopup()
        self._update_display_text()


__all__ = ["CheckableComboBox"]
