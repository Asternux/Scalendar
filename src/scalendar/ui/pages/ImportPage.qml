import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs 6.5
import Scalendar.Theme 1.0

Page {
    id: page
    signal openTimetableRequested()
    background: Rectangle { color: "transparent" }
    FileDialog { id: picker; title: "选择课表图片"; nameFilters: ["图片文件 (*.png *.jpg *.jpeg *.webp)", "所有文件 (*)"]; onAccepted: page.openTimetableRequested() }
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
            Text { text: "导入课表"; color: Theme.ink; font.pixelSize: 25; font.bold: true }
            Text { text: "第 1 步 · 添加一张清晰的课表图片，之后我们会带你完成校对。"; color: Theme.inkSoft; font.pixelSize: 13 }
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 310
                radius: Theme.radiusLarge
                color: Theme.surface
                border.color: Theme.borderStrong
                border.width: 1
                DropArea { anchors.fill: parent; onDropped: page.openTimetableRequested(); ColumnLayout { anchors.centerIn: parent; spacing: 12; Text { Layout.alignment: Qt.AlignHCenter; text: "＋"; color: Theme.accent; font.pixelSize: 46 }
 Text { Layout.alignment: Qt.AlignHCenter; text: "拖拽课表图片到这里"; color: Theme.ink; font.pixelSize: 19; font.bold: true }
 Text { Layout.alignment: Qt.AlignHCenter; text: "支持 PNG、JPG、JPEG、WebP"; color: Theme.muted; font.pixelSize: 12 }
 Button { Layout.alignment: Qt.AlignHCenter; text: "选择图片"; implicitWidth: 126; implicitHeight: 40; onClicked: picker.open(); contentItem: Text { text: parent.text; color: "white"; font.pixelSize: 13; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
 background: Rectangle { radius: 11; color: parent.down ? "#4C7BD7" : Theme.accent } }
 Text { Layout.alignment: Qt.AlignHCenter; text: "M2 界面演示：导入后的识别服务将在 M3 接入"; color: Theme.muted; font.pixelSize: 11 } } }
            }
            Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 86; radius: Theme.radius; color: Theme.surfaceSoft; RowLayout { anchors.fill: parent; anchors.margins: 18; spacing: 14; Text { text: "i"; color: Theme.accent; font.pixelSize: 18; font.bold: true }
 Text { Layout.fillWidth: true; text: "建议使用横向、完整、文字清晰的课表截图。原始图片只在本地流程中处理，项目文件不会嵌入图片。"; color: Theme.inkSoft; font.pixelSize: 12; wrapMode: Text.WordWrap } } }
        }
    }
}

