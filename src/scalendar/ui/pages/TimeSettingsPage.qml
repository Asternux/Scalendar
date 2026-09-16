import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Scalendar.Theme 1.0

Page {
    background: Rectangle { color: "transparent" }
    Flickable { anchors.fill: parent; contentWidth: width; contentHeight: body.implicitHeight + 48; clip: true; ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
 ColumnLayout { id: body; width: Math.min(parent.width - 60, 1000); anchors.horizontalCenter: parent.horizontalCenter; spacing: 16; Text { text: "学期与节次"; color: Theme.ink; font.pixelSize: 25; font.bold: true }
 Text { text: "手动确认第一周周一、教学周范围，以及每节课真实的开始和结束时间。"; color: Theme.inkSoft; font.pixelSize: 13 }
 Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 100; radius: Theme.radius; color: Theme.surface; border.color: Theme.border; RowLayout { anchors.fill: parent; anchors.margins: 18; spacing: 20; ColumnLayout { Layout.fillWidth: true; Text { text: "第一教学周周一"; color: Theme.muted; font.pixelSize: 11 }
 Text { text: "2026-09-07"; color: Theme.ink; font.pixelSize: 16; font.bold: true } }
 ColumnLayout { Layout.fillWidth: true; Text { text: "教学周数"; color: Theme.muted; font.pixelSize: 11 }
 Text { text: "20 周"; color: Theme.ink; font.pixelSize: 16; font.bold: true } }
 Button { text: "编辑学期"; flat: true; onClicked: appController.notify("学期编辑器将在 M3 开放"); contentItem: Text { text: parent.text; color: Theme.accent; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter } } } }
 Text { text: "每日节次"; color: Theme.ink; font.pixelSize: 16; font.bold: true; topPadding: 8 }
 Repeater { model: 12; delegate: Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 58; radius: Theme.radiusSmall; color: Theme.surface; border.color: Theme.border; RowLayout { anchors.fill: parent; anchors.leftMargin: 18; anchors.rightMargin: 18; spacing: 16; Text { text: "第 " + (index + 1) + " 节"; color: Theme.ink; font.pixelSize: 13; font.bold: true; Layout.preferredWidth: 80 }
 TextField { Layout.preferredWidth: 115; text: ["08:00","08:55","10:00","10:55","14:00","14:55","16:00","16:55","19:00","19:55","20:50","21:45"][index]; placeholderText: "开始"; selectByMouse: true }
 Text { text: "至"; color: Theme.muted; font.pixelSize: 12 }
 TextField { Layout.preferredWidth: 115; text: ["08:45","09:40","10:45","11:40","14:45","15:40","16:45","17:40","19:45","20:40","21:35","22:30"][index]; placeholderText: "结束"; selectByMouse: true }
 Item { Layout.fillWidth: true }
 Text { text: "可编辑"; color: Theme.success; font.pixelSize: 11 } } } } } }
}

