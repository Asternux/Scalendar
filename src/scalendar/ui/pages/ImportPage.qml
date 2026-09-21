import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Dialogs 6.5
import QtQuick.Layouts 1.15
import Scalendar.Theme 1.0

Page {
    id: page
    objectName: "importPage"
    property string importMode: "image"
    background: Rectangle { color: "transparent" }

    FileDialog {
        id: imagePicker
        title: "选择课表图片"
        fileMode: FileDialog.OpenFile
        nameFilters: ["课表图片 (*.png *.jpg *.jpeg *.webp)", "所有文件 (*)"]
        onAccepted: appController.selectImage(selectedFile.toString())
    }
    FileDialog {
        id: excelPicker
        title: "选择 Excel 课表"
        fileMode: FileDialog.OpenFile
        nameFilters: ["Excel 工作簿 (*.xlsx)", "所有文件 (*)"]
        onAccepted: appController.selectExcel(selectedFile.toString())
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

            Text { text: page.importMode === "image" ? "图片导入与识别" : "Excel 导入"
color: Theme.ink
font.pixelSize: 25
font.bold: true }
            Text {
                Layout.fillWidth: true
                text: page.importMode === "image" ? "M5 · 选择或拖入一张完整课表图片。识别结果会先进入确认状态，不会自动覆盖当前课程。" : "M6 · 选择或拖入 XLSX 文件。先检查导入候选，再追加到当前课表。标准 Scalendar 文件可以完整恢复项目设置。"
                color: Theme.inkSoft
font.pixelSize: 13
wrapMode: Text.WordWrap
            }
            RowLayout {
                Layout.fillWidth: true
spacing: 8
                Button { text: "图片识别"
checkable: true
checked: page.importMode === "image"
onClicked: page.importMode = "image" }
                Button { text: "Excel 导入"
checkable: true
checked: page.importMode === "excel"
onClicked: page.importMode = "excel" }
                Item { Layout.fillWidth: true }
            }

            Rectangle {
                visible: !appController.hasProject
                Layout.fillWidth: true
Layout.preferredHeight: 220
radius: Theme.radius
color: Theme.surface
border.color: Theme.border
                ColumnLayout {
                    anchors.fill: parent
anchors.margins: 20
spacing: 10
                    Text { text: "先创建一个项目"
color: Theme.ink
font.pixelSize: 16
font.bold: true }
                    Text { Layout.fillWidth: true
text: page.importMode === "excel" ? "导入标准 Excel 时会用文件中的学期设置初始化这个空白项目。" : "图片识别需要一个现有项目来提供学期周数和节次上下文。"
color: Theme.muted
font.pixelSize: 12
wrapMode: Text.WordWrap }
                    RowLayout { Layout.fillWidth: true
TextField { id: projectNameField
Layout.fillWidth: true
text: "我的课表"
placeholderText: "项目名称" }
TextField { id: semesterNameField
Layout.fillWidth: true
text: "2026 秋季学期"
placeholderText: "学期名称" } }
                    RowLayout {
                        Layout.fillWidth: true
                        TextField { id: firstMondayField
Layout.fillWidth: true
text: "2026-09-07"
placeholderText: "第 1 教学周周一 YYYY-MM-DD" }
                        SpinBox { id: totalWeeksField
from: 1
to: 60
value: 16
editable: true
Layout.preferredWidth: 130 }
                        Button { text: "创建项目"
onClicked: appController.createProject(projectNameField.text, semesterNameField.text, firstMondayField.text, totalWeeksField.value)
contentItem: Text { text: parent.text
color: "white"
font.pixelSize: 12
horizontalAlignment: Text.AlignHCenter
verticalAlignment: Text.AlignVCenter }
background: Rectangle { radius: 9
color: Theme.accent } }
                    }
                }
            }

            Rectangle {
                visible: page.importMode === "image"
                Layout.fillWidth: true
Layout.preferredHeight: appController.hasImage ? 188 : 224
radius: Theme.radius
color: Theme.surface
border.color: Theme.border
                DropArea {
                    id: imageDropArea
anchors.fill: parent
keys: ["text/uri-list"]
                    onDropped: { if (drop.hasUrls && drop.urls.length > 0) { appController.selectImage(drop.urls[0].toString())
drop.acceptProposedAction() } }
                }
                ColumnLayout {
                    anchors.fill: parent
anchors.margins: 20
spacing: 10
                    RowLayout { Layout.fillWidth: true
Text { Layout.fillWidth: true
text: "课表图片"
color: Theme.ink
font.pixelSize: 16
font.bold: true }
Text { text: "PNG / JPG / JPEG / WEBP"
color: Theme.muted
font.pixelSize: 11 } }
                    Rectangle {
                        Layout.fillWidth: true
Layout.fillHeight: true
radius: Theme.radiusSmall
color: imageDropArea.containsDrag ? Theme.accentSoft : Theme.surfaceSoft
border.color: imageDropArea.containsDrag ? Theme.accent : Theme.border
                        RowLayout {
                            anchors.fill: parent
anchors.margins: 12
spacing: 14
                            Image { visible: appController.hasImage
Layout.preferredWidth: 128
Layout.fillHeight: true
source: appController.imagePreviewUrl
fillMode: Image.PreserveAspectFit
asynchronous: true }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { Layout.fillWidth: true
text: appController.hasImage ? appController.imageName : "把课表图片拖到这里，或点击选择文件"
color: Theme.ink
font.pixelSize: 13
font.bold: true
elide: Text.ElideRight }
                                Text { visible: appController.hasImage
text: appController.imageWidth + " × " + appController.imageHeight + " px"
color: Theme.muted
font.pixelSize: 11 }
                                Text { visible: !appController.hasImage
text: "不会修改原图，也不会复制到 .scalendar 项目中。"
color: Theme.muted
font.pixelSize: 11 }
                                RowLayout { Layout.fillWidth: true
Button { text: appController.hasImage ? "更换图片" : "选择图片"
onClicked: imagePicker.open()
contentItem: Text { text: parent.text
color: Theme.accent
font.pixelSize: 12
horizontalAlignment: Text.AlignHCenter
verticalAlignment: Text.AlignVCenter }
background: Rectangle { radius: 9
color: Theme.surface
border.color: Theme.borderStrong } }
Button { visible: appController.hasImage
text: "清除"
flat: true
onClicked: appController.clearImage()
contentItem: Text { text: parent.text
color: Theme.danger
font.pixelSize: 11
horizontalAlignment: Text.AlignHCenter
verticalAlignment: Text.AlignVCenter } } }
                            }
                        }
                    }
                }
            }

            RowLayout {
                visible: page.importMode === "image"
                Layout.fillWidth: true
                Text { Layout.fillWidth: true
text: appController.hasApiKey ? "API Key 已设置，仅保存在本次运行内存中。" : "尚未设置 API Key。"
color: appController.hasApiKey ? Theme.success : Theme.warning
font.pixelSize: 11 }
                Button { visible: !appController.hasApiKey
text: "去设置"
flat: true
onClicked: appController.navigate("settings")
contentItem: Text { text: parent.text
color: Theme.accent
font.pixelSize: 11
horizontalAlignment: Text.AlignHCenter
verticalAlignment: Text.AlignVCenter } }
                Button { enabled: appController.hasProject && appController.hasImage && appController.recognitionState !== "recognizing" && appController.recognitionState !== "ready_to_import"
text: appController.recognitionState === "recognizing" ? "正在识别…" : "开始识别"
onClicked: appController.startRecognition()
implicitWidth: 120
implicitHeight: 38
contentItem: Text { text: parent.text
color: parent.enabled ? "white" : Theme.muted
font.pixelSize: 12
font.bold: true
horizontalAlignment: Text.AlignHCenter
verticalAlignment: Text.AlignVCenter }
background: Rectangle { radius: 10
color: parent.enabled ? Theme.accent : Theme.surfaceSoft
border.color: Theme.border } }
            }
            Text { visible: page.importMode === "image" && appController.hasImage && appController.recognitionState !== "ready_to_import"
Layout.fillWidth: true
text: "图片将发送至所选 AI 服务进行识别。请确认图片中不包含你不希望上传的私人信息。"
color: Theme.muted
font.pixelSize: 11
wrapMode: Text.WordWrap }

            Rectangle {
                visible: page.importMode === "image" && (appController.recognitionState === "recognizing" || appController.recognitionState === "error")
                Layout.fillWidth: true
Layout.preferredHeight: 82
radius: Theme.radius
color: appController.recognitionState === "error" ? "#FFF0F0" : Theme.surfaceGlass
border.color: appController.recognitionState === "error" ? Theme.danger : Theme.border
                RowLayout { anchors.fill: parent
anchors.margins: 18
spacing: 12
BusyIndicator { running: appController.recognitionState === "recognizing"
visible: running
Layout.preferredWidth: 28
Layout.preferredHeight: 28 }
ColumnLayout { Layout.fillWidth: true
Text { text: appController.recognitionState === "error" ? "识别未完成" : "正在识别课表"
color: Theme.ink
font.pixelSize: 14
font.bold: true }
Text { Layout.fillWidth: true
text: appController.recognitionState === "error" ? appController.recognitionErrorText : appController.recognitionPhase
color: appController.recognitionState === "error" ? Theme.danger : Theme.muted
font.pixelSize: 11
wrapMode: Text.WordWrap } } }
            }

            Rectangle {
                visible: page.importMode === "image" && appController.recognitionState === "ready_to_import"
                Layout.fillWidth: true
Layout.preferredHeight: 330
radius: Theme.radius
color: Theme.surface
border.color: Theme.border
                ColumnLayout {
                    anchors.fill: parent
anchors.margins: 18
spacing: 8
                    RowLayout { Layout.fillWidth: true
Text { Layout.fillWidth: true
text: "课表已识别"
color: Theme.ink
font.pixelSize: 16
font.bold: true }
Text { text: "识别到 " + appController.recognitionCourseCount + " 门课程，其中 " + appController.recognitionReviewCount + " 门需要确认"
color: appController.recognitionReviewCount > 0 ? Theme.warning : Theme.success
font.pixelSize: 11 } }
                    ListView {
                        id: recognitionCandidates
Layout.fillWidth: true
Layout.fillHeight: true
model: appController.recognitionCandidateModel
spacing: 6
clip: true
                        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                        delegate: Rectangle {
                            required property string name
required property string weekdayLabel
required property string scheduleLabel
required property string weekLabel
required property bool needsReview
                            width: recognitionCandidates.width
height: 48
radius: 8
color: needsReview ? "#FFF8E8" : Theme.surfaceSoft
border.color: needsReview ? Theme.warning : Theme.border
                            RowLayout { anchors.fill: parent
anchors.margins: 10
spacing: 10
Text { Layout.fillWidth: true
text: name
color: Theme.ink
font.pixelSize: 12
font.bold: true
elide: Text.ElideRight }
Text { text: weekdayLabel + " · " + scheduleLabel
color: Theme.muted
font.pixelSize: 10 }
Text { text: weekLabel
color: Theme.muted
font.pixelSize: 10 }
Text { text: needsReview ? "⚠ 待确认" : "已识别"
color: needsReview ? Theme.warning : Theme.success
font.pixelSize: 10 } }
                        }
                    }
                    RowLayout { Layout.fillWidth: true
Text { Layout.fillWidth: true
text: "导入后会追加到当前课表，不会覆盖已有课程。"
color: Theme.muted
font.pixelSize: 11 }
Button { text: "取消"
onClicked: appController.cancelRecognition() }
Button { text: "导入到课表"
onClicked: appController.applyRecognitionResult()
contentItem: Text { text: parent.text
color: "white"
font.pixelSize: 12
horizontalAlignment: Text.AlignHCenter
verticalAlignment: Text.AlignVCenter }
background: Rectangle { radius: 9
color: Theme.accent } } }
                }
            }

            Rectangle {
                visible: page.importMode === "excel"
                Layout.fillWidth: true
Layout.preferredHeight: appController.excelState === "ready_to_import" ? 214 : 236
radius: Theme.radius
color: Theme.surface
border.color: Theme.border
                DropArea {
                    id: excelDropArea
anchors.fill: parent
keys: ["text/uri-list"]
                    onDropped: { if (drop.hasUrls && drop.urls.length > 0) { appController.selectExcel(drop.urls[0].toString())
drop.acceptProposedAction() } }
                }
                ColumnLayout {
                    anchors.fill: parent
anchors.margins: 20
spacing: 10
                    RowLayout { Layout.fillWidth: true
Text { Layout.fillWidth: true
text: "Excel 课表文件"
color: Theme.ink
font.pixelSize: 16
font.bold: true }
Text { text: "标准 XLSX"
color: Theme.muted
font.pixelSize: 11 } }
                    Rectangle {
                        Layout.fillWidth: true
Layout.fillHeight: true
radius: Theme.radiusSmall
color: excelDropArea.containsDrag ? Theme.accentSoft : Theme.surfaceSoft
border.color: excelDropArea.containsDrag ? Theme.accent : Theme.border
                        ColumnLayout {
                            anchors.fill: parent
anchors.margins: 14
spacing: 8
                            Text { Layout.fillWidth: true
text: appController.excelFileName.length > 0 ? appController.excelFileName : "把 XLSX 文件拖到这里，或点击选择文件"
color: Theme.ink
font.pixelSize: 13
font.bold: true
elide: Text.ElideRight }
                            Text { visible: appController.excelState === "ready_to_import"
text: appController.excelSheetCount + " 个 Sheet · " + appController.excelFormatText
color: Theme.muted
font.pixelSize: 11 }
                            Text { visible: appController.excelState === "idle"
text: "支持 Scalendar 标准工作簿，也会谨慎尝试识别常见外部课表表格。"
color: Theme.muted
font.pixelSize: 11
wrapMode: Text.WordWrap }
                            Text { visible: appController.excelState === "error"
Layout.fillWidth: true
text: appController.excelErrorText
color: Theme.danger
font.pixelSize: 11
wrapMode: Text.WordWrap }
                            RowLayout { Layout.fillWidth: true
Button { text: appController.excelState === "ready_to_import" ? "更换文件" : "选择 Excel"
onClicked: excelPicker.open()
contentItem: Text { text: parent.text
color: Theme.accent
font.pixelSize: 12
horizontalAlignment: Text.AlignHCenter
verticalAlignment: Text.AlignVCenter }
background: Rectangle { radius: 9
color: Theme.surface
border.color: Theme.borderStrong } }
Button { visible: appController.excelState !== "idle"
text: "清除"
flat: true
onClicked: appController.clearExcel()
contentItem: Text { text: parent.text
color: Theme.danger
font.pixelSize: 11
horizontalAlignment: Text.AlignHCenter
verticalAlignment: Text.AlignVCenter } } }
                        }
                    }
                }
            }

            Rectangle {
                visible: page.importMode === "excel" && appController.excelState === "ready_to_import"
                Layout.fillWidth: true
Layout.preferredHeight: 330
radius: Theme.radius
color: Theme.surface
border.color: Theme.border
                ColumnLayout {
                    anchors.fill: parent
anchors.margins: 18
spacing: 8
                    RowLayout { Layout.fillWidth: true
Text { Layout.fillWidth: true
text: "Excel 导入预览"
color: Theme.ink
font.pixelSize: 16
font.bold: true }
Text { text: "识别到 " + appController.excelCourseCount + " 门课程，其中 " + appController.excelReviewCount + " 门需要确认"
color: appController.excelReviewCount > 0 ? Theme.warning : Theme.success
font.pixelSize: 11 } }
                    ListView {
                        id: excelCandidates
Layout.fillWidth: true
Layout.fillHeight: true
model: appController.excelCandidateModel
spacing: 6
clip: true
                        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                        delegate: Rectangle {
                            required property string name
required property string weekdayLabel
required property string scheduleLabel
required property string weekLabel
required property bool needsReview
                            width: excelCandidates.width
height: 48
radius: 8
color: needsReview ? "#FFF8E8" : Theme.surfaceSoft
border.color: needsReview ? Theme.warning : Theme.border
                            RowLayout { anchors.fill: parent
anchors.margins: 10
spacing: 10
Text { Layout.fillWidth: true
text: name
color: Theme.ink
font.pixelSize: 12
font.bold: true
elide: Text.ElideRight }
Text { text: weekdayLabel + " · " + scheduleLabel
color: Theme.muted
font.pixelSize: 10 }
Text { text: weekLabel
color: Theme.muted
font.pixelSize: 10 }
Text { text: needsReview ? "⚠ 待确认" : "已识别"
color: needsReview ? Theme.warning : Theme.success
font.pixelSize: 10 } }
                        }
                    }
                    RowLayout { Layout.fillWidth: true
Text { Layout.fillWidth: true
text: "导入后会追加课程；标准工作簿在空白项目中还会恢复项目与节次设置。"
color: Theme.muted
font.pixelSize: 11
wrapMode: Text.WordWrap }
Button { text: "取消"
onClicked: appController.clearExcel() }
Button { text: "导入到课表"
onClicked: appController.applyExcelImport()
contentItem: Text { text: parent.text
color: "white"
font.pixelSize: 12
horizontalAlignment: Text.AlignHCenter
verticalAlignment: Text.AlignVCenter }
background: Rectangle { radius: 9
color: Theme.accent } } }
                }
            }
        }
    }
}
