import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Scalendar.Theme 1.0

Page {
    background: Rectangle { color: "transparent" }
    Flickable { anchors.fill: parent; contentWidth: width; contentHeight: body.implicitHeight + 48; clip: true; ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
 ColumnLayout { id: body; width: Math.min(parent.width - 60, 820); anchors.horizontalCenter: parent.horizontalCenter; spacing: 16; Text { text: "设置"; color: Theme.ink; font.pixelSize: 25; font.bold: true }
 Text { text: "保持简洁：视觉设置与识别服务设置分开管理。API Key 只在本次运行内存中保存。"; color: Theme.inkSoft; font.pixelSize: 13; wrapMode: Text.WordWrap; Layout.fillWidth: true }
 Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 190; radius: Theme.radius; color: Theme.surface; border.color: Theme.border; ColumnLayout { anchors.fill: parent; anchors.margins: 22; spacing: 10; Text { text: "图片识别服务"; color: Theme.ink; font.pixelSize: 16; font.bold: true }
 RowLayout { Layout.fillWidth: true; Text { Layout.fillWidth: true; text: "OpenAI API Key"; color: Theme.inkSoft; font.pixelSize: 13 }
 Text { text: appController.apiKeyStatus; color: appController.hasApiKey ? Theme.success : Theme.muted; font.pixelSize: 11 } }
 RowLayout { Layout.fillWidth: true; TextField { id: apiKeyField; Layout.fillWidth: true; echoMode: TextInput.Password; placeholderText: "本次运行输入 Key，不会写入项目文件"; selectByMouse: true }
 Button { text: "仅本次保存"; onClicked: { if (appController.setApiKey(apiKeyField.text)) apiKeyField.clear() } } }
 RowLayout { Layout.fillWidth: true; Text { text: "模型名称"; color: Theme.inkSoft; font.pixelSize: 13 }
 TextField { id: modelField; Layout.preferredWidth: 220; text: appController.openaiModel; selectByMouse: true }
 Button { text: "应用"; onClicked: appController.setOpenAIModel(modelField.text) } }
 Text { text: "图片会在识别时发送至所选 AI 服务；原图不会复制到 .scalendar。"; color: Theme.muted; font.pixelSize: 11; wrapMode: Text.WordWrap; Layout.fillWidth: true } } }
 Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 210; radius: Theme.radius; color: Theme.surface; border.color: Theme.border; ColumnLayout { anchors.fill: parent; anchors.margins: 22; spacing: 12; Text { text: "窗口外观"; color: Theme.ink; font.pixelSize: 16; font.bold: true }
 RowLayout { Layout.fillWidth: true; Text { Layout.fillWidth: true; text: "透明磨砂效果"; color: Theme.inkSoft; font.pixelSize: 13 }
 Switch { checked: true } }
 RowLayout { Layout.fillWidth: true; Text { Layout.fillWidth: true; text: "透明度"; color: Theme.inkSoft; font.pixelSize: 13 }
 Slider { Layout.preferredWidth: 220; from: 0.8; to: 1.0; value: 0.96 } }
 RowLayout { Layout.fillWidth: true; Text { Layout.fillWidth: true; text: "磨砂程度"; color: Theme.inkSoft; font.pixelSize: 13 }
 Slider { Layout.preferredWidth: 220; from: 0; to: 1; value: 0.55 } } } }
 Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 116; radius: Theme.radius; color: Theme.surfaceSoft; border.color: Theme.border; ColumnLayout { anchors.fill: parent; anchors.margins: 20; spacing: 5; Text { text: "目录策略"; color: Theme.ink; font.pixelSize: 14; font.bold: true }
 Text { text: "项目与设置默认放在用户可写目录，不写入 Program Files。具体路径选择将在 M3/M4 接入。"; color: Theme.muted; font.pixelSize: 12; wrapMode: Text.WordWrap; Layout.fillWidth: true } } } } }
}

