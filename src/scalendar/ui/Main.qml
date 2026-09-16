import QtQuick 2.15
import QtQuick.Controls 2.15
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
    title: "Scalendar · 课表日历助手"
    color: Theme.canvas
    property string currentPage: "home"
    property int pageIndex: pageIndexFor(currentPage)
    property string pageTitle: pageTitleFor(currentPage)
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
        if (page === "import") return "导入课表"
        if (page === "timetable") return "课表视图"
        if (page === "courses") return "课程列表"
        if (page === "time") return "学期与节次"
        if (page === "export") return "导出结果"
        if (page === "settings") return "设置"
        return "首页"
    }
    function navigate(page) { currentPage = page }
    Connections {
        target: appController
        function onPageRequested(page) { window.navigate(page) }
        function onToastRequested(message) { toast.text = message; toast.visible = true; toastTimer.restart() }
    }
    Timer { id: toastTimer; interval: 2200; onTriggered: toast.visible = false }
    RowLayout {
        anchors.fill: parent
        spacing: 0
        Sidebar { Layout.preferredWidth: 224; Layout.fillHeight: true; currentPage: window.currentPage; onNavigate: window.navigate(page) }
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0
            Topbar { Layout.fillWidth: true; title: window.pageTitle; subtitle: window.currentPage === "home" ? "把课表整理成你真正愿意使用的日历" : appController.projectName; onSettingsClicked: window.navigate("settings") }
            StackLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: window.pageIndex
                HomePage { onStartRequested: window.navigate("import") }
                ImportPage { onOpenTimetableRequested: window.navigate("timetable") }
                TimetablePage { onEditCourse: drawer.openWith(course) }
                CourseListPage { onEditCourse: drawer.openWith(course) }
                TimeSettingsPage {}
                ExportPage {}
                SettingsPage {}
            }
        }
    }
    Drawer {
        id: drawer
        edge: Qt.RightEdge
        width: 390
        height: window.height
        modal: true
        interactive: true
        property var currentCourse: ({})
        function openWith(course) { currentCourse = course; open() }
        background: Rectangle { color: Theme.surface; border.color: Theme.border }
        contentItem: Flickable {
            contentWidth: width
            contentHeight: drawerContent.implicitHeight + 40
            clip: true
            ColumnLayout {
                id: drawerContent
                width: parent.width - 44
                x: 22
                y: 22
                spacing: 14
                RowLayout {
                    Layout.fillWidth: true
                    Text { Layout.fillWidth: true; text: "编辑课程"; color: Theme.ink; font.pixelSize: 21; font.bold: true }
                    Button { text: "关闭"; flat: true; onClicked: drawer.close(); contentItem: Text { text: parent.text; color: Theme.inkSoft; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter } }
                }
                Text { Layout.fillWidth: true; text: "全局课程编辑器抽屉 · M2 mock"; color: Theme.muted; font.pixelSize: 12; wrapMode: Text.WordWrap }
                Text { text: "课程名称"; color: Theme.inkSoft; font.pixelSize: 12 }
                TextField { Layout.fillWidth: true; text: drawer.currentCourse.name || ""; placeholderText: "课程名称" }
                Text { text: "上课地点"; color: Theme.inkSoft; font.pixelSize: 12 }
                TextField { Layout.fillWidth: true; text: drawer.currentCourse.location || ""; placeholderText: "教学楼、教室或自定义地点" }
                RowLayout {
                    Layout.fillWidth: true
                    Text { Layout.fillWidth: true; text: "周次与节次"; color: Theme.inkSoft; font.pixelSize: 12 }
                    Text { text: drawer.currentCourse.meta || ""; color: Theme.accent; font.pixelSize: 12 }
                }
                Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.border }
                Text { Layout.fillWidth: true; text: "M3 将在这里接入单门编辑、批量编辑、地点字段和识别置信度提示。"; color: Theme.muted; font.pixelSize: 12; wrapMode: Text.WordWrap }
                Item { Layout.fillHeight: true; Layout.minimumHeight: 160 }
                Button { Layout.fillWidth: true; text: "保存修改（下一阶段）"; enabled: false; implicitHeight: 42 }
            }
        }
    }
    Rectangle {
        id: toast
        visible: false
        z: 20
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 24
        width: toastText.implicitWidth + 34
        height: 42
        radius: 21
        color: Theme.ink
        Text { id: toastText; anchors.centerIn: parent; text: ""; color: "white"; font.pixelSize: 12 }
        property alias text: toastText.text
    }
}
