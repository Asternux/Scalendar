import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Scalendar.Theme 1.0

Page {
    id: page
    signal editCourse(string courseId)
    signal addCourse()
    background: Rectangle { color: "transparent" }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 30
        spacing: 14

        RowLayout {
            Layout.fillWidth: true
            Text {
                Layout.fillWidth: true
                text: "课程列表"
                color: Theme.ink
                font.pixelSize: 25
                font.bold: true
            }
            Button {
                text: "＋ 添加课程"
                onClicked: page.addCourse()
                contentItem: Text {
                    text: parent.text
                    color: "white"
                    font.pixelSize: 12
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    radius: 10
                    color: Theme.accent
                }
            }
        }

        Text {
            text: "共 " + appController.courseModel.count + " 门课程 · " + appController.projectName
            color: Theme.muted
            font.pixelSize: 12
        }

        ListView {
            id: list
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: appController.courseModel
            spacing: 10
            clip: true
            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
            delegate: Rectangle {
                required property string courseId
                required property string name
                required property int weekday
                required property int startSection
                required property int endSection
                required property int startWeek
                required property int endWeek
                required property string teacher
                required property string locationText
                required property string courseColor
                width: list.width
                height: 78
                radius: Theme.radiusSmall
                color: Theme.surface
                border.color: Theme.border

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 18
                    anchors.rightMargin: 12
                    spacing: 14

                    Rectangle {
                        Layout.preferredWidth: 8
                        Layout.preferredHeight: 36
                        radius: 4
                        color: courseColor
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        Text {
                            text: name
                            color: Theme.ink
                            font.pixelSize: 14
                            font.bold: true
                        }
                        Text {
                            text: "周" + weekday + " · 第" + startSection + "–" + endSection + "节 · " + startWeek + "–" + endWeek + "周 · " + (locationText || "未填写地点")
                            color: Theme.muted
                            font.pixelSize: 11
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                        Text {
                            text: teacher || "未填写教师"
                            color: Theme.inkSoft
                            font.pixelSize: 11
                        }
                    }

                    Button {
                        text: "编辑"
                        flat: true
                        onClicked: page.editCourse(courseId)
                        contentItem: Text {
                            text: parent.text
                            color: Theme.accent
                            font.pixelSize: 12
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                }
            }
        }
    }
}
