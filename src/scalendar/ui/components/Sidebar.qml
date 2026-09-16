import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Scalendar.Theme 1.0

Item {
    id: root
    property string currentPage: "home"
    signal navigate(string page)

    Rectangle { anchors.fill: parent; color: Theme.surface; border.color: Theme.border; border.width: 1 }
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 12
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            Rectangle { Layout.preferredWidth: 38; Layout.preferredHeight: 38; radius: 12; color: Theme.accent; Text { anchors.centerIn: parent; text: "S"; color: "white"; font.pixelSize: 21; font.bold: true } }
            ColumnLayout { Layout.fillWidth: true; spacing: 0; Text { text: "Scalendar"; color: Theme.ink; font.pixelSize: 17; font.bold: true }
 Text { text: "课表日历助手"; color: Theme.muted; font.pixelSize: 11 } }
        }
        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.border }
        Text { text: "工作区"; color: Theme.muted; font.pixelSize: 11; font.bold: true; leftPadding: 8; topPadding: 5 }
        SidebarItem { Layout.fillWidth: true; label: "首页"; glyph: "⌂"; selected: root.currentPage === "home"; onClicked: root.navigate("home") }
        SidebarItem { Layout.fillWidth: true; label: "导入课表"; glyph: "＋"; selected: root.currentPage === "import"; onClicked: root.navigate("import") }
        SidebarItem { Layout.fillWidth: true; label: "课表视图"; glyph: "▦"; selected: root.currentPage === "timetable"; onClicked: root.navigate("timetable") }
        SidebarItem { Layout.fillWidth: true; label: "课程列表"; glyph: "☷"; selected: root.currentPage === "courses"; onClicked: root.navigate("courses") }
        Text { text: "配置"; color: Theme.muted; font.pixelSize: 11; font.bold: true; leftPadding: 8; topPadding: 12 }
        SidebarItem { Layout.fillWidth: true; label: "节次与时间"; glyph: "◷"; selected: root.currentPage === "time"; onClicked: root.navigate("time") }
        SidebarItem { Layout.fillWidth: true; label: "导出"; glyph: "↗"; selected: root.currentPage === "export"; onClicked: root.navigate("export") }
        Item { Layout.fillHeight: true }
        SidebarItem { Layout.fillWidth: true; label: "设置"; glyph: "⚙"; selected: root.currentPage === "settings"; onClicked: root.navigate("settings") }
        Text { Layout.fillWidth: true; text: "V1 · M8 Windows"; color: Theme.muted; font.pixelSize: 11; horizontalAlignment: Text.AlignHCenter; bottomPadding: 3 }
    }
}

