import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Scalendar.Theme 1.0

Page {
    id: page
    signal editCourse(var course)
    background: Rectangle { color: "transparent" }
    Flickable { anchors.fill: parent; contentWidth: width; contentHeight: body.implicitHeight + 48; clip: true; ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
 ColumnLayout { id: body; width: Math.min(page.width - 60, 1080); anchors.horizontalCenter: parent.horizontalCenter; spacing: 16; RowLayout { Layout.fillWidth: true; Text { Layout.fillWidth: true; text: "课程列表"; color: Theme.ink; font.pixelSize: 25; font.bold: true }
 Button { text: "＋ 添加课程"; onClicked: appController.notify("课程编辑器将在 M3 开放"); contentItem: Text { text: parent.text; color: "white"; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
 background: Rectangle { radius: 10; color: Theme.accent } } }
 Text { text: "共 " + appController.demoCourses.length + " 门课程 · 当前为 M2 演示数据"; color: Theme.muted; font.pixelSize: 12 }
 Repeater { model: appController.demoCourses; delegate: Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 72; radius: Theme.radiusSmall; color: Theme.surface; border.color: Theme.border; RowLayout { anchors.fill: parent; anchors.leftMargin: 18; anchors.rightMargin: 12; spacing: 14; Rectangle { Layout.preferredWidth: 8; Layout.preferredHeight: 34; radius: 4; color: modelData.color }
 ColumnLayout { Layout.fillWidth: true; Text { text: modelData.name; color: Theme.ink; font.pixelSize: 14; font.bold: true }
 Text { text: modelData.meta + "  ·  " + modelData.location; color: Theme.muted; font.pixelSize: 11 } }
 Button { text: "编辑"; flat: true; onClicked: page.editCourse(modelData); contentItem: Text { text: parent.text; color: Theme.accent; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter } } } } } } }
}

