import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Dialogs 6.5
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15
import Scalendar.Theme 1.0
import "components"
import "pages"

ApplicationWindow {
    id: window
    visible: true
    width: initialWidth
    height: initialHeight
    minimumWidth: 1120
    minimumHeight: 720
    title: "Scalendar — " + appController.semesterName + (appController.dirty ? " *" : "")
    color: Theme.canvas

    property string currentPage: "home"
    property int pageIndex: pageIndexFor(currentPage)
    property string pageTitle: pageTitleFor(currentPage)

    Component.onCompleted: {
        if (initialCourseId.length > 0) {
            drawer.openWith(initialCourseId)
        }
    }

    function pageIndexFor(page) {
        if (page === "import") return 1
        if (page === "timetable") return 2
        if (page === "courses") return 3
        if (page === "time") return 4
        if (page === "export") return 5
        if (page === "settings") return 6
        return 0
    }

    function pageTitleFor(page) {
        if (page === "import") return "创建或打开"
        if (page === "timetable") return "课表视图"
        if (page === "courses") return "课程列表"
        if (page === "time") return "学期与节次"
        if (page === "export") return "导出结果"
        if (page === "settings") return "设置"
        return "首页"
    }

    function navigate(page) {
        currentPage = page
    }

    Shortcut {
        sequence: "Ctrl+S"
        onActivated: appController.save()
    }

    Connections {
        target: appController
        function onPageRequested(page) { window.navigate(page) }
        function onSavePathRequested() { saveDialog.open() }
        function onToastRequested(message) {
            toast.text = message
            toast.error = false
            toast.visible = true
            toastTimer.restart()
        }
        function onErrorRequested(message) {
            toast.text = message
            toast.error = true
            toast.visible = true
            toastTimer.restart()
        }
    }

    Timer {
        id: toastTimer
        interval: 2600
        onTriggered: toast.visible = false
    }

    FileDialog {
        id: saveDialog
        title: "保存 Scalendar 项目"
        fileMode: FileDialog.SaveFile
        nameFilters: ["Scalendar 项目 (*.scalendar)"]
        defaultSuffix: "scalendar"
        onAccepted: appController.saveAs(selectedFile.toString())
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Sidebar {
            Layout.preferredWidth: 224
            Layout.fillHeight: true
            currentPage: window.currentPage
            onNavigate: window.navigate(page)
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            Topbar {
                Layout.fillWidth: true
                title: window.pageTitle
                subtitle: window.currentPage === "home" ? "先建立项目，再逐步编辑你的课程安排" : appController.projectName
                onSettingsClicked: window.navigate("settings")
            }

            StackLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: window.pageIndex
                HomePage { onStartRequested: window.navigate("import") }
                ImportPage {}
                TimetablePage {
                    onEditCourse: drawer.openWith(courseId)
                    onAddCourse: drawer.openNew()
                }
                CourseListPage {
                    onEditCourse: drawer.openWith(courseId)
                    onAddCourse: drawer.openNew()
                }
                TimeSettingsPage {}
                ExportPage {}
                SettingsPage {}
            }
        }
    }

    Drawer {
        id: drawer
        objectName: "courseDrawer"
        edge: Qt.RightEdge
        width: 430
        height: window.height
        modal: true
        interactive: true

        function openWith(courseId) {
            appController.beginEditCourse(courseId)
            Qt.callLater(syncFields)
            open()
        }

        function openNew() {
            appController.beginNewCourse()
            Qt.callLater(syncFields)
            open()
        }

        function syncFields() {
            nameField.text = courseEditor.name
            weekdayBox.currentIndex = courseEditor.weekday - 1
            startSectionField.text = courseEditor.startSection
            endSectionField.text = courseEditor.endSection
            startWeekField.text = courseEditor.startWeek
            endWeekField.text = courseEditor.endWeek
            patternBox.currentIndex = ["all", "odd", "even", "custom"].indexOf(courseEditor.weekPattern)
            customWeeksField.text = courseEditor.customWeeksText
            teacherField.text = courseEditor.teacher
            buildingField.text = courseEditor.building
            roomField.text = courseEditor.room
            locationField.text = courseEditor.locationText
            colorField.text = courseEditor.color
            notesField.text = courseEditor.notes
        }

        background: Rectangle {
            color: Theme.surface
            border.color: Theme.border
        }

        contentItem: Flickable {
            contentWidth: width
            contentHeight: editorContent.implicitHeight + 42
            clip: true
            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

            ColumnLayout {
                id: editorContent
                width: parent.width - 44
                x: 22
                y: 22
                spacing: 10

                RowLayout {
                    Layout.fillWidth: true
                    Text { Layout.fillWidth: true; text: courseEditor.hasCourse ? "编辑课程" : "添加课程"; color: Theme.ink; font.pixelSize: 21; font.bold: true }
                    Button {
                        text: "取消"
                        flat: true
                        onClicked: drawer.close()
                        contentItem: Text { text: parent.text; color: Theme.inkSoft; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                    }
                }

                Text { Layout.fillWidth: true; text: "保存前所有修改只停留在编辑器中，取消不会改变项目。"; color: Theme.muted; font.pixelSize: 11; wrapMode: Text.WordWrap }

                Text { text: "课程名称"; color: Theme.inkSoft; font.pixelSize: 11 }
                TextField { id: nameField; Layout.fillWidth: true; placeholderText: "例如：高等数学"; selectByMouse: true; onTextEdited: courseEditor.name = text }

                RowLayout {
                    Layout.fillWidth: true
                    Text { text: "星期"; color: Theme.inkSoft; font.pixelSize: 11 }
                    ComboBox { id: weekdayBox; Layout.fillWidth: true; model: ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]; onActivated: courseEditor.weekday = currentIndex + 1 }
                    Text { text: "节次"; color: Theme.inkSoft; font.pixelSize: 11 }
                    TextField { id: startSectionField; Layout.preferredWidth: 54; inputMethodHints: Qt.ImhDigitsOnly; onTextEdited: courseEditor.startSection = Number(text) }
                    Text { text: "–"; color: Theme.muted }
                    TextField { id: endSectionField; Layout.preferredWidth: 54; inputMethodHints: Qt.ImhDigitsOnly; onTextEdited: courseEditor.endSection = Number(text) }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Text { text: "周次"; color: Theme.inkSoft; font.pixelSize: 11 }
                    TextField { id: startWeekField; Layout.preferredWidth: 62; inputMethodHints: Qt.ImhDigitsOnly; onTextEdited: courseEditor.startWeek = Number(text) }
                    Text { text: "–"; color: Theme.muted }
                    TextField { id: endWeekField; Layout.preferredWidth: 62; inputMethodHints: Qt.ImhDigitsOnly; onTextEdited: courseEditor.endWeek = Number(text) }
                    ComboBox { id: patternBox; Layout.fillWidth: true; model: ["全周", "单周", "双周", "自定义"]; onActivated: courseEditor.setWeekPatternIndex(currentIndex) }
                }

                TextField { id: customWeeksField; Layout.fillWidth: true; visible: patternBox.currentIndex === 3; placeholderText: "自定义周次，例如：1, 3, 7"; onTextEdited: courseEditor.customWeeksText = text }

                Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.border }
                Text { text: "教师与地点"; color: Theme.ink; font.pixelSize: 14; font.bold: true; topPadding: 4 }
                TextField { id: teacherField; Layout.fillWidth: true; placeholderText: "教师（可选）"; onTextEdited: courseEditor.teacher = text }
                RowLayout {
                    Layout.fillWidth: true
                    TextField { id: buildingField; Layout.fillWidth: true; placeholderText: "教学楼"; onTextEdited: courseEditor.building = text }
                    TextField { id: roomField; Layout.fillWidth: true; placeholderText: "教室"; onTextEdited: courseEditor.room = text }
                }
                TextField { id: locationField; Layout.fillWidth: true; placeholderText: "原始地点文本（可选）"; onTextEdited: courseEditor.locationText = text }
                TextField { id: colorField; Layout.fillWidth: true; placeholderText: "课程颜色，例如 #6C8EF5"; onTextEdited: courseEditor.color = text }
                TextArea { id: notesField; Layout.fillWidth: true; placeholderText: "备注（可选）"; wrapMode: TextArea.Wrap; onTextChanged: courseEditor.notes = text }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    Button {
                        visible: courseEditor.hasCourse
                        text: "删除课程"
                        onClicked: deleteDialog.open()
                        contentItem: Text { text: parent.text; color: Theme.danger; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                        background: Rectangle { radius: 9; color: Theme.surfaceSoft; border.color: Theme.danger }
                    }
                    Item { Layout.fillWidth: true }
                    Button {
                        text: "保存课程"
                        implicitWidth: 116
                        implicitHeight: 40
                        onClicked: if (appController.saveEditor()) drawer.close()
                        contentItem: Text { text: parent.text; color: "white"; font.pixelSize: 13; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                        background: Rectangle { radius: 10; color: Theme.accent }
                    }
                }
            }
        }
    }

    MessageDialog {
        id: deleteDialog
        title: "删除课程"
        text: "确定删除“" + courseEditor.name + "”吗？此操作会从当前项目移除课程。"
        buttons: MessageDialog.Ok | MessageDialog.Cancel
        onAccepted: {
            appController.deleteCourse(courseEditor.courseId)
            drawer.close()
        }
    }

    Rectangle {
        id: toast
        property bool error: false
        property alias text: toastText.text
        visible: false
        z: 20
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 24
        width: Math.min(parent.width - 48, toastText.implicitWidth + 34)
        height: 42
        radius: 21
        color: error ? Theme.danger : Theme.ink
        Text { id: toastText; anchors.centerIn: parent; color: "white"; font.pixelSize: 12; elide: Text.ElideRight }
    }
}
