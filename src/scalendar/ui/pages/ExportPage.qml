import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Scalendar.Theme 1.0

Page {
    background: Rectangle { color: "transparent" }
    Flickable { anchors.fill: parent; contentWidth: width; contentHeight: body.implicitHeight + 48; clip: true; ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
 ColumnLayout { id: body; width: Math.min(parent.width - 60, 1000); anchors.horizontalCenter: parent.horizontalCenter; spacing: 18; Text { text: "导出结果"; color: Theme.ink; font.pixelSize: 25; font.bold: true }
 Text { text: "确认课程和时间后，在这里选择你需要的日历文件格式。"; color: Theme.inkSoft; font.pixelSize: 13 }
 RowLayout { Layout.fillWidth: true; spacing: 16; Repeater { model: [{ name: "Excel", detail: "便于继续整理和备份", glyph: "▤", enabled: false }, { name: "Apple 日历", detail: "生成可导入的 .ics 文件", glyph: "◫", enabled: false }]; delegate: Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 180; radius: Theme.radius; color: Theme.surface; border.color: Theme.border; ColumnLayout { anchors.fill: parent; anchors.margins: 20; spacing: 9; Text { text: modelData.glyph; color: Theme.accent; font.pixelSize: 27 }
 Text { text: modelData.name; color: Theme.ink; font.pixelSize: 16; font.bold: true }
 Text { Layout.fillWidth: true; text: modelData.detail; color: Theme.muted; font.pixelSize: 12; wrapMode: Text.WordWrap }
 Item { Layout.fillHeight: true }
 Button { text: "M3 开放"; enabled: false; Layout.preferredWidth: 100; Layout.preferredHeight: 32 } } } } }
 Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 88; radius: Theme.radius; color: Theme.surfaceGlass; border.color: Theme.border; Text { anchors.fill: parent; anchors.margins: 18; text: "导出前会检查学期日期、节次时间和课程周次。位置字段将在 V1 中支持可选的名称与坐标，不会因地址解析失败而阻止导出。"; color: Theme.inkSoft; font.pixelSize: 12; wrapMode: Text.WordWrap; verticalAlignment: Text.AlignVCenter } } } }
}

