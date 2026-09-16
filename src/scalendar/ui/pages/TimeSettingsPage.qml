import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Dialogs 6.5
import QtQuick.Layouts 1.15
import Scalendar.Theme 1.0

Page {
    id: page
    objectName: "timeSettingsPage"
    property bool formDirty: false
    property int pendingDeleteIndex: -1

    background: Rectangle { color: "transparent" }

    function loadSemesterFields() {
        semesterNameField.text = appController.semesterName
        firstMondayField.text = appController.firstWeekMonday
        totalWeeksField.text = String(appController.totalWeeks)
        formDirty = false
    }

    Component.onCompleted: loadSemesterFields()
    onVisibleChanged: if (visible && !formDirty) loadSemesterFields()

    Connections {
        target: appController
        function onProjectChanged() {
            if (!page.formDirty) page.loadSemesterFields()
        }
    }

    Flickable {
        anchors.fill: parent
        contentWidth: width
        contentHeight: body.implicitHeight + 52
        clip: true
        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

        ColumnLayout {
            id: body
            width: Math.min(page.width - 60, 1000)
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 16

            Text { text: "学期与节次"; color: Theme.ink; font.pixelSize: 25; font.bold: true }
            Text {
                text: "这里的设置会直接影响课表时间轴和课程周次。第一教学周指第 1 教学周的星期一。"
                color: Theme.inkSoft
                font.pixelSize: 13
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 176
                radius: Theme.radius
                color: Theme.surface
                border.color: Theme.border
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 18
                    spacing: 10
                    RowLayout {
                        Layout.fillWidth: true
                        Text { Layout.fillWidth: true; text: "学期设置"; color: Theme.ink; font.pixelSize: 15; font.bold: true }
                        Button {
                            text: "保存学期设置"
                            enabled: page.formDirty
                            onClicked: {
                                if (appController.updateSemester(semesterNameField.text, firstMondayField.text, Number(totalWeeksField.text))) page.formDirty = false
                            }
                            contentItem: Text { text: parent.text; color: parent.enabled ? "white" : Theme.muted; font.pixelSize: 11; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                            background: Rectangle { radius: 9; color: parent.enabled ? Theme.accent : Theme.surfaceSoft; border.color: Theme.border }
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12
                        ColumnLayout {
                            Layout.fillWidth: true
                            Text { text: "学期名称"; color: Theme.inkSoft; font.pixelSize: 11 }
                            TextField { id: semesterNameField; Layout.fillWidth: true; selectByMouse: true; onTextEdited: page.formDirty = true }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            Text { text: "第 1 教学周的星期一"; color: Theme.inkSoft; font.pixelSize: 11 }
                            TextField { id: firstMondayField; Layout.fillWidth: true; placeholderText: "YYYY-MM-DD（必须是周一）"; selectByMouse: true; onTextEdited: page.formDirty = true }
                        }
                        ColumnLayout {
                            Layout.preferredWidth: 130
                            Text { text: "总周数（1–60）"; color: Theme.inkSoft; font.pixelSize: 11 }
                            TextField { id: totalWeeksField; Layout.fillWidth: true; inputMethodHints: Qt.ImhDigitsOnly; selectByMouse: true; onTextEdited: page.formDirty = true }
                        }
                    }
                    Text { text: "如果缩短周数会影响现有课程，系统会阻止保存，避免静默截断。"; color: Theme.muted; font.pixelSize: 11 }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Text { Layout.fillWidth: true; text: "每日节次"; color: Theme.ink; font.pixelSize: 16; font.bold: true }
                Text { text: "允许时间重叠，但会显示警告"; color: Theme.warning; font.pixelSize: 11 }
                Button {
                    text: "＋ 添加节次"
                    onClicked: appController.addSection()
                    contentItem: Text { text: parent.text; color: Theme.accent; font.pixelSize: 11; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                }
            }

            Rectangle {
                visible: appController.sectionModel.count === 0
                Layout.fillWidth: true
                Layout.preferredHeight: 150
                radius: Theme.radius
                color: Theme.surfaceGlass
                border.color: Theme.border
                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 8
                    Text { Layout.alignment: Qt.AlignHCenter; text: "还没有设置上课时间。"; color: Theme.ink; font.pixelSize: 15; font.bold: true }
                    RowLayout {
                        Layout.alignment: Qt.AlignHCenter
                        Button { text: "使用默认模板"; onClicked: appController.restoreDefaultSections() }
                        Button { text: "添加第一节"; onClicked: appController.addSection() }
                    }
                }
            }

            ListView {
                id: sections
                objectName: "sectionList"
                visible: appController.sectionModel.count > 0
                Layout.fillWidth: true
                Layout.preferredHeight: Math.min(470, Math.max(90, appController.sectionModel.count * 76))
                model: appController.sectionModel
                spacing: 8
                clip: true
                ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                delegate: Rectangle {
                    required property int sectionIndex
                    required property string startTime
                    required property string endTime
                    required property string warningText
                    width: sections.width
                    height: warningText.length > 0 ? 86 : 62
                    radius: Theme.radiusSmall
                    color: Theme.surface
                    border.color: warningText.length > 0 ? Theme.warning : Theme.border

                    RowLayout {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.topMargin: 8
                        anchors.leftMargin: 16
                        anchors.rightMargin: 12
                        spacing: 12
                        Text { text: "第 " + sectionIndex + " 节"; color: Theme.ink; font.pixelSize: 13; font.bold: true; Layout.preferredWidth: 66 }
                        TextField {
                            id: startField
                            Layout.preferredWidth: 112
                            text: startTime
                            placeholderText: "开始 HH:MM"
                            selectByMouse: true
                            onEditingFinished: {
                                if (!appController.updateSection(sectionIndex, text, endField.text)) text = startTime
                            }
                        }
                        Text { text: "—"; color: Theme.muted; font.pixelSize: 12 }
                        TextField {
                            id: endField
                            Layout.preferredWidth: 112
                            text: endTime
                            placeholderText: "结束 HH:MM"
                            selectByMouse: true
                            onEditingFinished: {
                                if (!appController.updateSection(sectionIndex, startField.text, text)) text = endTime
                            }
                        }
                        Item { Layout.fillWidth: true }
                        Button {
                            text: "删除"
                            flat: true
                            onClicked: { page.pendingDeleteIndex = sectionIndex; deleteSectionDialog.open() }
                            contentItem: Text { text: parent.text; color: Theme.danger; font.pixelSize: 11; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                        }
                    }
                    Text {
                        visible: warningText.length > 0
                        anchors.left: parent.left
                        anchors.leftMargin: 94
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 8
                        text: "⚠ " + warningText
                        color: Theme.warning
                        font.pixelSize: 10
                    }
                }
            }

            RowLayout {
                visible: appController.sectionModel.count > 0
                Layout.fillWidth: true
                Text { Layout.fillWidth: true; text: "默认模板只是可编辑起点，不代表所有学校的实际作息。"; color: Theme.muted; font.pixelSize: 11 }
                Button {
                    text: "恢复默认模板"
                    onClicked: restoreTemplateDialog.open()
                    contentItem: Text { text: parent.text; color: Theme.accent; font.pixelSize: 11; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                }
            }
        }
    }

    MessageDialog {
        id: deleteSectionDialog
        title: "删除节次"
        text: "确定删除第 " + page.pendingDeleteIndex + " 节吗？如果有课程使用它，系统会阻止删除。"
        buttons: MessageDialog.Ok | MessageDialog.Cancel
        onAccepted: {
            appController.deleteSection(page.pendingDeleteIndex)
            page.pendingDeleteIndex = -1
        }
    }

    MessageDialog {
        id: restoreTemplateDialog
        title: "恢复默认模板"
        text: "恢复默认模板会替换当前所有节次时间。确定继续吗？"
        buttons: MessageDialog.Ok | MessageDialog.Cancel
        onAccepted: appController.restoreDefaultSections()
    }
}
