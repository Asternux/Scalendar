import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Scalendar.Theme 1.0

Page {
    id: page
    signal startRequested()
    background: Rectangle { color: "transparent" }
    Flickable {
        anchors.fill: parent
        contentWidth: width
        contentHeight: contentColumn.implicitHeight + 48
        clip: true
        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
        ColumnLayout {
            id: contentColumn
            width: Math.min(page.width - 60, 1080)
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.topMargin: 12
            spacing: 22
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 290
                radius: Theme.radiusLarge
                color: Theme.accent
                clip: true
                ColumnLayout { anchors.left: parent.left; anchors.leftMargin: 42; anchors.verticalCenter: parent.verticalCenter; width: Math.min(parent.width * 0.62, 600); spacing: 12; Text { text: "把一张课表图片，\n变成真正好用的日历"; color: "white"; font.pixelSize: 31; font.bold: true; lineHeight: 1.08 }
 Text { text: "Scalendar 用清晰的步骤帮助你识别、校对、编辑，并导出属于自己的课程安排。"; color: "#EAF1FF"; font.pixelSize: 14; wrapMode: Text.WordWrap; Layout.fillWidth: true }
 Button { text: "开始整理课表  →"; implicitWidth: 162; implicitHeight: 44; onClicked: page.startRequested(); contentItem: Text { text: parent.text; color: Theme.accent; font.pixelSize: 14; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
 background: Rectangle { radius: 12; color: "white" } } }
                Text { anchors.right: parent.right; anchors.rightMargin: 58; anchors.verticalCenter: parent.verticalCenter; text: "✦"; color: "#9AB9FF"; font.pixelSize: 118; opacity: 0.55 }
                Text { anchors.right: parent.right; anchors.rightMargin: 34; anchors.bottom: parent.bottom; anchors.bottomMargin: 32; text: "·  ·  ·"; color: "#BFD1FF"; font.pixelSize: 18; opacity: 0.8 }
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 16
                Repeater {
                    model: [{ title: "识别", body: "从图片提取课程信息", glyph: "⌁", color: "#E8F0FF" }, { title: "校对", body: "在可视化界面里确认", glyph: "✓", color: "#E9F7F2" }, { title: "导出", body: "生成适合日历的文件", glyph: "↗", color: "#FFF4E5" }]
                    delegate: Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 124; radius: Theme.radius; color: modelData.color; ColumnLayout { anchors.fill: parent; anchors.margins: 18; spacing: 7; Text { text: modelData.glyph; color: Theme.accent; font.pixelSize: 22; font.bold: true }
 Text { text: modelData.title; color: Theme.ink; font.pixelSize: 15; font.bold: true }
 Text { text: modelData.body; color: Theme.inkSoft; font.pixelSize: 12 } } }
                }
            }
            Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 100; radius: Theme.radius; color: Theme.surfaceGlass; border.color: Theme.border; ColumnLayout { anchors.fill: parent; anchors.margins: 20; spacing: 4; Text { text: "从简单开始"; color: Theme.ink; font.pixelSize: 14; font.bold: true }
 Text { text: "导入图片后，你可以逐项修改学期、节次、时间和地点。每一步都能回到上一步。"; color: Theme.inkSoft; font.pixelSize: 12; wrapMode: Text.WordWrap; Layout.fillWidth: true } } }
        }
    }
}

