import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Dialogs 6.5
import QtQuick.Layouts 1.15
import Scalendar.Theme 1.0

Page {
    id: page
    objectName: "courseListPage"
    signal editCourse(string courseId)
    signal addCourse()
    property var selectedIds: []

    background: Rectangle { color: "transparent" }

    function isSelected(courseId) {
        return selectedIds.indexOf(courseId) >= 0
    }

    function toggleSelected(courseId) {
        var next = selectedIds.slice()
        var position = next.indexOf(courseId)
        if (position >= 0) next.splice(position, 1)
        else next.push(courseId)
        selectedIds = next
    }

    function clearSelection() {
        selectedIds = []
    }

    function patternLabel(pattern) {
        if (pattern === "odd") return "单周"
        if (pattern === "even") return "双周"
        if (pattern === "custom") return "自定义"
        return "每周"
    }

    function weekLabel(startWeek, endWeek, pattern, customWeeks) {
        if (pattern === "custom") return customWeeks.join("、") + "周"
        return startWeek + "–" + endWeek + "周（" + patternLabel(pattern) + "）"
    }

    function weekdayLabel(weekday) {
        return ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][weekday - 1] || "未知星期"
    }

    function locationLabel(locationText, building, room) {
        if (locationText && locationText.length > 0) return locationText
        return ((building || "") + " " + (room || "")).trim() || "未填写地点"
    }

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
            ComboBox {
                id: sortBox
                model: ["星期 → 开始节次", "课程名称", "开始节次"]
                implicitWidth: 150
                onActivated: appController.setCourseSort(currentIndex)
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
                background: Rectangle { radius: 10; color: Theme.accent }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Text {
                Layout.fillWidth: true
                text: "共 " + appController.courseModel.count + " 门课程 · " + appController.projectName
                color: Theme.muted
                font.pixelSize: 12
            }
            Button {
                visible: page.selectedIds.length > 0
                text: "清除选择"
                flat: true
                onClicked: page.clearSelection()
                contentItem: Text { text: parent.text; color: Theme.accent; font.pixelSize: 11; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            }
        }

        Rectangle {
            visible: page.selectedIds.length > 0
            Layout.fillWidth: true
            Layout.preferredHeight: 58
            radius: Theme.radiusSmall
            color: Theme.accentSoft
            border.color: Theme.accent
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 16
                anchors.rightMargin: 12
                spacing: 8
                Text { text: "已选择 " + page.selectedIds.length + " 门课程"; color: Theme.ink; font.pixelSize: 12; font.bold: true; Layout.fillWidth: true }
                Button {
                    text: "修改周次"
                    onClicked: weekDialog.open()
                    contentItem: Text { text: parent.text; color: Theme.accent; font.pixelSize: 11; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                }
                Button {
                    text: "修改地点"
                    onClicked: locationDialog.open()
                    contentItem: Text { text: parent.text; color: Theme.accent; font.pixelSize: 11; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                }
                Button {
                    text: "删除"
                    onClicked: deleteSelectedDialog.open()
                    contentItem: Text { text: parent.text; color: Theme.danger; font.pixelSize: 11; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                }
            }
        }

        ListView {
            id: list
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: appController.courseSortModel
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
                required property string weekPattern
                required property var customWeeks
                required property string teacher
                required property string building
                required property string room
                required property string locationText
                required property string courseColor
                required property var needsReviewFields
                property bool selected: page.isSelected(courseId)
                width: list.width
                height: 84
                radius: Theme.radiusSmall
                color: selected ? Theme.accentSoft : Theme.surface
                border.color: selected ? Theme.accent : Theme.border

                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.LeftButton
                    onDoubleClicked: page.editCourse(courseId)
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 14
                    anchors.rightMargin: 12
                    spacing: 12
                    CheckBox {
                        z: 2
                        checked: selected
                        onClicked: page.toggleSelected(courseId)
                    }
                    Rectangle {
                        z: 2
                        Layout.preferredWidth: 8
                        Layout.preferredHeight: 42
                        radius: 4
                        color: courseColor
                    }
                    ColumnLayout {
                        z: 2
                        Layout.fillWidth: true
                        Text { text: name; color: Theme.ink; font.pixelSize: 14; font.bold: true; elide: Text.ElideRight; Layout.fillWidth: true }
                        Text {
                            text: (needsReviewFields.length > 0 ? "⚠ 待确认 · " : "") + weekdayLabel(weekday) + " · 第" + startSection + "–" + endSection + "节 · " + weekLabel(startWeek, endWeek, weekPattern, customWeeks)
                            color: needsReviewFields.length > 0 ? Theme.warning : Theme.muted
                            font.pixelSize: 11
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                        Text {
                            text: locationLabel(locationText, building, room) + (teacher ? " · " + teacher : "")
                            color: Theme.inkSoft
                            font.pixelSize: 11
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                    }
                    Button {
                        z: 2
                        text: "编辑"
                        flat: true
                        onClicked: page.editCourse(courseId)
                        contentItem: Text { text: parent.text; color: Theme.accent; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                    }
                }
            }
        }

        Rectangle {
            visible: list.count === 0
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: Theme.radius
            color: Theme.surfaceGlass
            border.color: Theme.border
            ColumnLayout {
                anchors.centerIn: parent
                spacing: 8
                Text { Layout.alignment: Qt.AlignHCenter; text: "还没有课程"; color: Theme.ink; font.pixelSize: 17; font.bold: true }
                Text { Layout.alignment: Qt.AlignHCenter; text: "添加课程，或者稍后从图片 / Excel 导入。"; color: Theme.muted; font.pixelSize: 12 }
                Button {
                    Layout.alignment: Qt.AlignHCenter
                    text: "添加课程"
                    onClicked: page.addCourse()
                    contentItem: Text { text: parent.text; color: "white"; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                    background: Rectangle { radius: 9; color: Theme.accent }
                }
            }
        }
    }

    Dialog {
        id: weekDialog
        modal: true
        title: "批量修改周次"
        width: 390
        contentItem: ColumnLayout {
            spacing: 10
            Text { Layout.fillWidth: true; text: "将修改 " + page.selectedIds.length + " 门课程的周次设置。"; color: Theme.inkSoft; font.pixelSize: 12; wrapMode: Text.WordWrap }
            RowLayout {
                Layout.fillWidth: true
                Text { text: "范围"; color: Theme.inkSoft; font.pixelSize: 11 }
                SpinBox { id: batchStartWeek; from: 1; to: Math.max(1, appController.totalWeeks); value: 1; editable: true; Layout.fillWidth: true }
                Text { text: "–"; color: Theme.muted }
                SpinBox { id: batchEndWeek; from: 1; to: Math.max(1, appController.totalWeeks); value: Math.max(1, appController.totalWeeks); editable: true; Layout.fillWidth: true }
            }
            ComboBox { id: batchPattern; Layout.fillWidth: true; model: ["每周", "单周", "双周", "自定义"] }
            TextField { id: batchCustomWeeks; Layout.fillWidth: true; visible: batchPattern.currentIndex === 3; placeholderText: "自定义周次，例如：1,3,5"; selectByMouse: true }
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                Button { text: "取消"; onClicked: weekDialog.close() }
                Button {
                    text: "确认修改"
                    onClicked: {
                        var ok = appController.batchUpdateWeeks(page.selectedIds, batchStartWeek.value, batchEndWeek.value, ["all", "odd", "even", "custom"][batchPattern.currentIndex], batchCustomWeeks.text)
                        if (ok) { page.clearSelection(); weekDialog.close() }
                    }
                    contentItem: Text { text: parent.text; color: "white"; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                    background: Rectangle { radius: 9; color: Theme.accent }
                }
            }
        }
    }

    Dialog {
        id: locationDialog
        modal: true
        title: "批量修改地点"
        width: 390
        contentItem: ColumnLayout {
            spacing: 10
            Text { Layout.fillWidth: true; text: "为选中的 " + page.selectedIds.length + " 门课程设置地点。留空表示清除对应字段。"; color: Theme.inkSoft; font.pixelSize: 12; wrapMode: Text.WordWrap }
            TextField { id: batchBuilding; Layout.fillWidth: true; placeholderText: "教学楼"; selectByMouse: true }
            TextField { id: batchRoom; Layout.fillWidth: true; placeholderText: "教室"; selectByMouse: true }
            TextField { id: batchLocation; Layout.fillWidth: true; placeholderText: "地点显示文本（可选）"; selectByMouse: true }
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                Button { text: "取消"; onClicked: locationDialog.close() }
                Button {
                    text: "保存地点"
                    onClicked: {
                        var ok = appController.batchUpdateLocation(page.selectedIds, batchBuilding.text, batchRoom.text, batchLocation.text)
                        if (ok) { page.clearSelection(); locationDialog.close() }
                    }
                    contentItem: Text { text: parent.text; color: "white"; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                    background: Rectangle { radius: 9; color: Theme.accent }
                }
            }
        }
    }

    MessageDialog {
        id: deleteSelectedDialog
        title: "批量删除课程"
        text: "确定删除选中的 " + page.selectedIds.length + " 门课程吗？"
        buttons: MessageDialog.Ok | MessageDialog.Cancel
        onAccepted: {
            if (appController.batchDeleteCourses(page.selectedIds)) page.clearSelection()
        }
    }
}
