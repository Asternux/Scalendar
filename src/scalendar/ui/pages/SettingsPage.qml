import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Scalendar.Theme 1.0

Page {
    background: Rectangle { color: "transparent" }
    Flickable { anchors.fill: parent; contentWidth: width; contentHeight: body.implicitHeight + 48; clip: true; ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
 ColumnLayout { id: body; width: Math.min(parent.width - 60, 820); anchors.horizontalCenter: parent.horizontalCenter; spacing: 16; Text { text: "设置"; color: Theme.ink; font.pixelSize: 25; font.bold: true }
 Text { text: "保持简洁：M2 只展示视觉设置入口，持久化和系统材质将在后续阶段接入。"; color: Theme.inkSoft; font.pixelSize: 13; wrapMode: Text.WordWrap; Layout.fillWidth: true }
 Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 210; radius: Theme.radius; color: Theme.surface; border.color: Theme.border; ColumnLayout { anchors.fill: parent; anchors.margins: 22; spacing: 12; Text { text: "窗口外观"; color: Theme.ink; font.pixelSize: 16; font.bold: true }
 RowLayout { Layout.fillWidth: true; Text { Layout.fillWidth: true; text: "透明磨砂效果"; color: Theme.inkSoft; font.pixelSize: 13 }
 Switch { checked: true } }
 RowLayout { Layout.fillWidth: true; Text { Layout.fillWidth: true; text: "透明度"; color: Theme.inkSoft; font.pixelSize: 13 }
 Slider { Layout.preferredWidth: 220; from: 0.8; to: 1.0; value: 0.96 } }
 RowLayout { Layout.fillWidth: true; Text { Layout.fillWidth: true; text: "磨砂程度"; color: Theme.inkSoft; font.pixelSize: 13 }
 Slider { Layout.preferredWidth: 220; from: 0; to: 1; value: 0.55 } } } }
 Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 116; radius: Theme.radius; color: Theme.surfaceSoft; border.color: Theme.border; ColumnLayout { anchors.fill: parent; anchors.margins: 20; spacing: 5; Text { text: "目录策略"; color: Theme.ink; font.pixelSize: 14; font.bold: true }
 Text { text: "项目与设置默认放在用户可写目录，不写入 Program Files。具体路径选择将在 M3/M4 接入。"; color: Theme.muted; font.pixelSize: 12; wrapMode: Text.WordWrap; Layout.fillWidth: true } } } } }
}

