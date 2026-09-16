import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Scalendar.Theme 1.0
import "../components"

Page {
    id: page
    signal editCourse(var course)
    property var courses: appController.demoCourses
    background: Rectangle { color: "transparent" }
    Flickable {
        anchors.fill: parent
        contentWidth: width
        contentHeight: content.implicitHeight + 48
        clip: true
        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
        ColumnLayout {
            id: content
            width: Math.min(page.width - 60, 1120)
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 18
            RowLayout { Layout.fillWidth: true; Text { Layout.fillWidth: true; text: "本周课表"; color: Theme.ink; font.pixelSize: 25; font.bold: true }
 Rectangle { radius: 9; color: Theme.accentSoft; implicitWidth: 116; implicitHeight: 32; Text { anchors.centerIn: parent; text: "第 1 教学周"; color: Theme.accent; font.pixelSize: 12; font.bold: true } } }
            Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 58; radius: Theme.radius; color: Theme.surfaceGlass; border.color: Theme.border; RowLayout { anchors.fill: parent; anchors.margins: 16; spacing: 18; Text { text: "2026 秋季学期"; color: Theme.ink; font.pixelSize: 14; font.bold: true }
 Text { Layout.fillWidth: true; text: "9 月 7 日 — 9 月 13 日"; color: Theme.inkSoft; font.pixelSize: 13 }
 Button { text: "节次设置"; flat: true; onClicked: appController.navigate("time"); contentItem: Text { text: parent.text; color: Theme.accent; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter } } } }
            GridLayout { Layout.fillWidth: true; columns: page.width > 920 ? 3 : 2; columnSpacing: 14; rowSpacing: 14; Repeater { model: page.courses; delegate: CourseCard { Layout.fillWidth: true; course: modelData; onEditRequested: page.editCourse(course) } } }
            Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 86; radius: Theme.radius; color: Theme.surface; border.color: Theme.border; RowLayout { anchors.fill: parent; anchors.margins: 18; spacing: 12; Text { text: "＋"; color: Theme.accent; font.pixelSize: 22 }
 ColumnLayout { Layout.fillWidth: true; Text { text: "还没有显示完整课表？"; color: Theme.ink; font.pixelSize: 13; font.bold: true }
 Text { text: "完成识别和校对后，所有课程会按周次与节次出现在这里。"; color: Theme.muted; font.pixelSize: 11 } }
 Button { text: "去导入"; onClicked: appController.navigate("import"); contentItem: Text { text: parent.text; color: "white"; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
 background: Rectangle { radius: 9; color: Theme.accent } } } }
        }
    }
}

