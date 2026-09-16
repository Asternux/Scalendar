import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Scalendar.Theme 1.0

Page {
    background: Rectangle { color: "transparent" }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 30
        spacing: 14

        Text {
            text: "学期与节次"
            color: Theme.ink
            font.pixelSize: 25
            font.bold: true
        }

        Text {
            text: "当前项目的学期日期和每节课时间。修改节次后，课表时间轴会同步刷新。"
            color: Theme.inkSoft
            font.pixelSize: 13
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 94
            radius: Theme.radius
            color: Theme.surface
            border.color: Theme.border

            RowLayout {
                anchors.fill: parent
                anchors.margins: 18
                spacing: 22
                ColumnLayout {
                    Layout.fillWidth: true
                    Text { text: "项目"; color: Theme.muted; font.pixelSize: 11 }
                    Text { text: appController.projectName; color: Theme.ink; font.pixelSize: 15; font.bold: true; elide: Text.ElideRight }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    Text { text: "学期"; color: Theme.muted; font.pixelSize: 11 }
                    Text { text: appController.semesterName; color: Theme.ink; font.pixelSize: 15; font.bold: true; elide: Text.ElideRight }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    Text { text: "第一教学周周一"; color: Theme.muted; font.pixelSize: 11 }
                    Text { text: appController.firstWeekMonday; color: Theme.ink; font.pixelSize: 15; font.bold: true }
                }
                ColumnLayout {
                    Text { text: "教学周数"; color: Theme.muted; font.pixelSize: 11 }
                    Text { text: appController.totalWeeks + " 周"; color: Theme.ink; font.pixelSize: 15; font.bold: true }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Text { Layout.fillWidth: true; text: "每日节次"; color: Theme.ink; font.pixelSize: 16; font.bold: true }
            Text { text: "保存项目后会自动记录修改"; color: Theme.muted; font.pixelSize: 11 }
        }

        ListView {
            id: sections
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: appController.sectionModel
            spacing: 8
            clip: true
            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
            delegate: Rectangle {
                required property int sectionIndex
                required property string startTime
                required property string endTime
                width: sections.width
                height: 58
                radius: Theme.radiusSmall
                color: Theme.surface
                border.color: Theme.border

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 18
                    anchors.rightMargin: 18
                    spacing: 16
                    Text {
                        text: "第 " + sectionIndex + " 节"
                        color: Theme.ink
                        font.pixelSize: 13
                        font.bold: true
                        Layout.preferredWidth: 72
                    }
                    TextField {
                        id: startField
                        Layout.preferredWidth: 116
                        text: startTime
                        placeholderText: "开始"
                        selectByMouse: true
                        onEditingFinished: appController.updateSection(sectionIndex, text, endField.text)
                    }
                    Text { text: "至"; color: Theme.muted; font.pixelSize: 12 }
                    TextField {
                        id: endField
                        Layout.preferredWidth: 116
                        text: endTime
                        placeholderText: "结束"
                        selectByMouse: true
                        onEditingFinished: appController.updateSection(sectionIndex, startField.text, text)
                    }
                    Item { Layout.fillWidth: true }
                    Text { text: "可编辑"; color: Theme.success; font.pixelSize: 11 }
                }
            }
        }
    }
}
