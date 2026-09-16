import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Scalendar.Theme 1.0

Item {
    id: root
    property string title: "首页"
    property string subtitle: ""
    signal settingsClicked()
    implicitHeight: 78

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 30
        anchors.rightMargin: 30
        spacing: 14
        ColumnLayout { Layout.fillWidth: true; spacing: 3; Text { text: root.title; color: Theme.ink; font.pixelSize: 23; font.bold: true }
 Text { text: root.subtitle; color: Theme.muted; font.pixelSize: 12; visible: root.subtitle.length > 0 } }
        Button { text: "设置"; flat: true; implicitWidth: 70; implicitHeight: 38; onClicked: root.settingsClicked(); contentItem: Text { text: parent.text; color: Theme.inkSoft; font.pixelSize: 13; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
 background: Rectangle { radius: Theme.radiusSmall; color: parent.hovered ? Theme.surfaceSoft : "transparent" } }
    }
}

