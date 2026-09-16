import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Scalendar.Theme 1.0

Item {
    id: root
    property string courseId: ""
    property string courseName: "未命名课程"
    property string scheduleLabel: ""
    property string teacher: ""
    property string locationText: ""
    property string courseColor: Theme.accent
    signal editRequested(string courseId)

    Rectangle {
        anchors.fill: parent
        radius: Theme.radiusSmall
        color: Theme.surface
        border.color: Theme.border
        border.width: 1

        Rectangle {
            width: 5
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            radius: 3
            color: root.courseColor
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.leftMargin: 18
            anchors.rightMargin: 14
            anchors.topMargin: 12
            anchors.bottomMargin: 10
            spacing: 4

            Text {
                Layout.fillWidth: true
                text: root.courseName
                color: Theme.ink
                font.pixelSize: 14
                font.bold: true
                elide: Text.ElideRight
            }

            Text {
                Layout.fillWidth: true
                text: root.scheduleLabel
                color: Theme.accent
                font.pixelSize: 11
                elide: Text.ElideRight
            }

            Item { Layout.fillHeight: true }

            Text {
                Layout.fillWidth: true
                text: root.teacher || "未填写教师"
                color: Theme.inkSoft
                font.pixelSize: 11
                elide: Text.ElideRight
            }

            RowLayout {
                Layout.fillWidth: true
                Text {
                    Layout.fillWidth: true
                    text: root.locationText || "未填写地点"
                    color: Theme.muted
                    font.pixelSize: 10
                    elide: Text.ElideRight
                }
                Button {
                    text: "编辑"
                    flat: true
                    implicitWidth: 48
                    implicitHeight: 26
                    onClicked: root.editRequested(root.courseId)
                    contentItem: Text {
                        text: parent.text
                        color: Theme.accent
                        font.pixelSize: 11
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        radius: 8
                        color: parent.hovered ? Theme.accentSoft : "transparent"
                    }
                }
            }
        }
    }
}
