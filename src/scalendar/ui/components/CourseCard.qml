import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Scalendar.Theme 1.0

Item {
    id: root
    property var course: ({})
    signal editRequested(var course)
    implicitWidth: 270
    implicitHeight: 148
    Rectangle {
        anchors.fill: parent
        radius: Theme.radius
        color: Theme.surface
        border.color: Theme.border
        border.width: 1
        Rectangle { width: 5; anchors.top: parent.top; anchors.bottom: parent.bottom; anchors.left: parent.left; radius: 3; color: root.course.color || Theme.accent }
        ColumnLayout {
            anchors.fill: parent
            anchors.leftMargin: 20
            anchors.rightMargin: 16
            anchors.topMargin: 16
            anchors.bottomMargin: 14
            spacing: 6
            Text { Layout.fillWidth: true; text: root.course.name || "未命名课程"; color: Theme.ink; font.pixelSize: 16; font.bold: true; elide: Text.ElideRight }
            Text { Layout.fillWidth: true; text: root.course.meta || ""; color: Theme.accent; font.pixelSize: 12; elide: Text.ElideRight }
            Item { Layout.fillHeight: true }
            Text { Layout.fillWidth: true; text: root.course.teacher || "待补充教师"; color: Theme.inkSoft; font.pixelSize: 12; elide: Text.ElideRight }
            RowLayout { Layout.fillWidth: true; Text { Layout.fillWidth: true; text: root.course.location || "待补充地点"; color: Theme.muted; font.pixelSize: 11; elide: Text.ElideRight }
 Button { text: "编辑"; flat: true; implicitWidth: 48; implicitHeight: 28; onClicked: root.editRequested(root.course); contentItem: Text { text: parent.text; color: Theme.accent; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
 background: Rectangle { radius: 8; color: parent.hovered ? Theme.accentSoft : "transparent" } } }
        }
    }
}

