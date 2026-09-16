import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Dialogs 6.5
import QtQuick.Layouts 1.15
import Scalendar.Theme 1.0

Page {
    id: page
    objectName: "exportPage"
    background: Rectangle { color: "transparent" }
    FileDialog {
        id: excelSaveDialog
        title: "导出 Excel 课表"
        fileMode: FileDialog.SaveFile
        nameFilters: ["Excel 工作簿 (*.xlsx)"]
        defaultSuffix: "xlsx"
        onAccepted: appController.exportExcel(selectedFile.toString())
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
            spacing: 18
            Text { text: "导出结果"
color: Theme.ink
font.pixelSize: 25
font.bold: true }
            Text { Layout.fillWidth: true
text: "将当前项目导出为可继续整理的标准 XLSX 文件。导出的 Courses 和 Settings Sheet 可以再次导入 Scalendar。"
color: Theme.inkSoft
font.pixelSize: 13
wrapMode: Text.WordWrap }
            RowLayout {
                Layout.fillWidth: true
                spacing: 16
                Rectangle {
                    Layout.fillWidth: true
Layout.preferredHeight: 208
radius: Theme.radius
color: Theme.surface
border.color: Theme.border
                    ColumnLayout {
                        anchors.fill: parent
anchors.margins: 20
spacing: 9
                        Text { text: "▤"
color: Theme.accent
font.pixelSize: 27 }
                        Text { text: "Excel"
color: Theme.ink
font.pixelSize: 16
font.bold: true }
                        Text { Layout.fillWidth: true
text: "导出课程、学期设置和节次时间，适合备份、批量整理和重新导入。"
color: Theme.muted
font.pixelSize: 12
wrapMode: Text.WordWrap }
                        Item { Layout.fillHeight: true }
                        Button {
                            enabled: appController.hasProject
                            text: enabled ? "导出 Excel" : "请先打开项目"
                            Layout.preferredWidth: 124
Layout.preferredHeight: 36
                            onClicked: excelSaveDialog.open()
                            contentItem: Text { text: parent.text
color: parent.enabled ? "white" : Theme.muted
font.pixelSize: 12
font.bold: true
horizontalAlignment: Text.AlignHCenter
verticalAlignment: Text.AlignVCenter }
                            background: Rectangle { radius: 9
color: parent.enabled ? Theme.accent : Theme.surfaceSoft
border.color: Theme.border }
                        }
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
Layout.preferredHeight: 208
radius: Theme.radius
color: Theme.surfaceSoft
border.color: Theme.border
opacity: 0.78
                    ColumnLayout {
                        anchors.fill: parent
anchors.margins: 20
spacing: 9
                        Text { text: "◫"
color: Theme.muted
font.pixelSize: 27 }
                        Text { text: "Apple 日历"
color: Theme.ink
font.pixelSize: 16
font.bold: true }
                        Text { Layout.fillWidth: true
text: "ICS 导出将在后续 M7 阶段实现。"
color: Theme.muted
font.pixelSize: 12
wrapMode: Text.WordWrap }
                        Item { Layout.fillHeight: true }
                        Button { text: "M7 开放"
enabled: false
Layout.preferredWidth: 124
Layout.preferredHeight: 36 }
                    }
                }
            }
            Rectangle {
                Layout.fillWidth: true
Layout.preferredHeight: 96
radius: Theme.radius
color: Theme.surfaceGlass
border.color: Theme.border
                Text { anchors.fill: parent
anchors.margins: 18
text: "导出前会检查学期日期、节次时间和课程周次。Excel 只包含课程与项目设置，不包含 API Key、图片或内部 UUID；项目原文件仍然是 Scalendar 的主要数据源。"
color: Theme.inkSoft
font.pixelSize: 12
wrapMode: Text.WordWrap
verticalAlignment: Text.AlignVCenter }
            }
        }
    }
}

