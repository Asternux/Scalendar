import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs 6.5
import Scalendar.Theme 1.0

Page {
    id: page
    background: Rectangle { color: "transparent" }

    FileDialog {
        id: projectPicker
        title: "打开 Scalendar 项目"
        fileMode: FileDialog.OpenFile
        nameFilters: ["Scalendar 项目 (*.scalendar)", "所有文件 (*)"]
        onAccepted: appController.openProject(selectedFile.toString())
    }

    Flickable {
        anchors.fill: parent
        contentWidth: width
        contentHeight: body.implicitHeight + 48
        clip: true
        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

        ColumnLayout {
            id: body
            width: Math.min(page.width - 60, 1000)
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 18

            Text { text: "创建或打开课表"; color: Theme.ink; font.pixelSize: 25; font.bold: true }
            Text {
                text: "M3 · 先建立一个真实的本地项目，再手动编辑课程。图片识别会在 M5 接入。"
                color: Theme.inkSoft
                font.pixelSize: 13
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            Rectangle {
                Layout.fillWidth: true
                radius: Theme.radiusLarge
                color: Theme.surface
                border.color: Theme.border
                Layout.preferredHeight: 330

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 26
                    spacing: 12
                    Text { text: "新建空白课表"; color: Theme.ink; font.pixelSize: 17; font.bold: true }
                    Text { text: "请先设置项目和学期的基本信息。节次会使用默认模板，之后可以继续修改。"; color: Theme.muted; font.pixelSize: 12; wrapMode: Text.WordWrap; Layout.fillWidth: true }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 14
                        ColumnLayout {
                            Layout.fillWidth: true
                            Text { text: "项目名称"; color: Theme.inkSoft; font.pixelSize: 11 }
                            TextField { id: projectNameField; Layout.fillWidth: true; text: "我的课表"; placeholderText: "例如：我的 2026 课表"; selectByMouse: true }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            Text { text: "学期名称"; color: Theme.inkSoft; font.pixelSize: 11 }
                            TextField { id: semesterNameField; Layout.fillWidth: true; text: "2026 秋季学期"; placeholderText: "例如：2026 秋季学期"; selectByMouse: true }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 14
                        ColumnLayout {
                            Layout.fillWidth: true
                            Text { text: "第一教学周周一"; color: Theme.inkSoft; font.pixelSize: 11 }
                            TextField { id: firstMondayField; Layout.fillWidth: true; text: "2026-09-07"; placeholderText: "YYYY-MM-DD"; selectByMouse: true }
                        }
                        ColumnLayout {
                            Layout.preferredWidth: 180
                            Text { text: "总周数"; color: Theme.inkSoft; font.pixelSize: 11 }
                            SpinBox { id: totalWeeksField; Layout.fillWidth: true; from: 1; to: 60; value: 20; editable: true }
                        }
                    }

                    Button {
                        text: "创建并进入课表"
                        Layout.alignment: Qt.AlignRight
                        implicitWidth: 156
                        implicitHeight: 40
                        onClicked: appController.createProject(projectNameField.text, semesterNameField.text, firstMondayField.text, totalWeeksField.value)
                        contentItem: Text { text: parent.text; color: "white"; font.pixelSize: 13; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                        background: Rectangle { radius: 11; color: Theme.accent }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 90
                radius: Theme.radius
                color: Theme.surfaceGlass
                border.color: Theme.border
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 14
                    ColumnLayout {
                        Layout.fillWidth: true
                        Text { text: "打开已有项目"; color: Theme.ink; font.pixelSize: 14; font.bold: true }
                        Text { text: "继续编辑一个 .scalendar 文件，打开前会自动进行数据校验。"; color: Theme.inkSoft; font.pixelSize: 12 }
                    }
                    Button {
                        text: "打开 .scalendar"
                        onClicked: projectPicker.open()
                        contentItem: Text { text: parent.text; color: Theme.accent; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                        background: Rectangle { radius: 10; color: Theme.surface; border.color: Theme.borderStrong }
                    }
                }
            }
        }
    }
}
