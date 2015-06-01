"""

This tool can be launched by copying the code and pasting in the Script Editor in NUKE.

This nuke tool lists all nodes found in the current nuke script.  It organizes them by node class.
There is a name search field which hides all nodes that do not match the node name search.  It is not case-sensative.
There is a button to toggle the expansion and collapse of the rows of the node classes.

In the tree itself, there are only two columns: Name and Disable.
There are two types of rows: ClassRows and NodeRows (sub rows)
Clicking on the Name column in the NodeRow will center zoom the node in the DAG.
Clicking on the Disable column in the NodeRow will disable the node in the script.
Clicking on the Disable column in the ClassRow will disable all nodes of that class.

"""

__author__ = 'John'

import nuke
import re
from PySide.QtCore import QObject, Qt
from PySide.QtGui import QBrush, QColor, QFrame, QHBoxLayout, QIcon, QLabel, QLineEdit, QMouseEvent, QPushButton, \
    QSortFilterProxyModel, QStandardItem, QStandardItemModel, QStyledItemDelegate, QTreeView, QVBoxLayout


class NodeLister(QFrame):
    def __init__(self):
        super(NodeLister, self).__init__()

        self.setWindowTitle('Node Lister')

        self._btn_refresh = QPushButton('Refresh')
        self._btn_expand = QPushButton('Expand/Collapse')
        self._tree = NodeTree()
        self._ledit_search = QLineEdit()

        self._expand_state = False

        self._setup_ui()
        self._set_connections()

    def _expand_toggle(self):
        self._expand_state = not self._expand_state
        if self._expand_state:
            self._tree.expandAll()
        else:
            self._tree.collapseAll()

    def _filter_list(self):
        search_strings = str(self._ledit_search.text()).split()
        proxy = self._tree.model()
        model = proxy.sourceModel()
        show_rows = list()
        node_rows = list()
        rows = model.get_rows()
        class_rows = filter(lambda x: type(x) == ClassRow, rows)
        for class_row in class_rows:
            node_rows.extend(class_row.get_node_rows())

        for row in class_rows + node_rows:
            item = row.first_item()
            index = model.indexFromItem(item)
            proxy_index = proxy.mapFromSource(index)
            self._tree.setRowHidden(proxy_index.row(), proxy_index.parent(), False)

        if search_strings:
            for search_item in search_strings:
                for row in node_rows:
                    if search_item.strip().lower() in row.get_item('Node').text().lower():
                        show_rows.append(row)

            self._tree.expandAll()
            self._expand_state = True

            show_class_rows = list(set(map(lambda x: x.get_parent_class_row(), show_rows)))

            for row in node_rows:
                if row not in show_rows:
                    item = row.first_item()
                    index = model.indexFromItem(item)
                    proxy_index = proxy.mapFromSource(index)
                    self._tree.setRowHidden(proxy_index.row(), proxy_index.parent(), True)
            for row in class_rows:
                if row not in show_class_rows:
                    item = row.first_item()
                    index = model.indexFromItem(item)
                    proxy_index = proxy.mapFromSource(index)
                    self._tree.setRowHidden(proxy_index.row(), proxy_index.parent(), True)
        else:
            self._tree.collapseAll()
            self._expand_state = False

    def _refresh(self):
        model = self._tree.model().sourceModel()
        nodes = nuke.allNodes()

        node_dict = {}

        for node in nodes:
            if node.Class() not in node_dict.keys():
                node_dict[node.Class()] = []
            node_dict[node.Class()].append(node)

        model.clear_rows()

        model.populate(node_dict)

    def _set_connections(self):
        self._btn_refresh.released.connect(self._refresh)
        self._ledit_search.textChanged.connect(self._filter_list)
        self._btn_expand.released.connect(self._expand_toggle)

    def _setup_ui(self):
        self._btn_refresh.setIcon(QIcon(':qrc/images/Refresh.png'))
        self._btn_refresh.setToolTip('Populate tree with nodes')
        self._btn_expand.setToolTip('Toggle expanding and collapsing the tree')
        self._ledit_search.setToolTip('Search by node name')

        lyt_refresh = QHBoxLayout()
        lyt_refresh.addWidget(self._btn_refresh)
        lyt_refresh.addWidget(self._btn_expand)

        lyt_search = QHBoxLayout()
        lbl_search = QLabel('Name Search')
        lyt_search.addWidget(lbl_search)
        lyt_search.addWidget(self._ledit_search)

        lyt_main = QVBoxLayout()
        lyt_main.addLayout(lyt_refresh)
        lyt_main.addWidget(self._tree)
        lyt_main.addLayout(lyt_search)

        self.setLayout(lyt_main)


class NodeTree(QTreeView):
    def __init__(self):
        super(NodeTree, self).__init__()

        self._model = NodeModel(self)
        self._proxy = QSortFilterProxyModel()
        self._proxy.setSortRole(Qt.UserRole)    # sort order is stored in item in Qt.UserRole
        self._proxy.setSourceModel(self._model)

        self.setModel(self._proxy)
        self.setItemDelegate(NodeDelegate())
        self.header().setResizeMode(self.header().ResizeToContents)
        self.header().setStretchLastSection(False)
        self.setSortingEnabled(True)
        self.sortByColumn(self.model().sourceModel().HEADER.index('Node'), Qt.AscendingOrder)


class NodeDelegate(QStyledItemDelegate):
    def editorEvent(self, event, model, option, index):
        """

        :param event:
        :type event: QEvent
        :param model:
        :type model: NodeModel
        :param option:
        :type option: QStyleOptionViewItem
        :param index:
        :type index: QModelIndex
        :return:
        :rtype: bool
        """
        idx = index.model().mapToSource(index)
        item = model.sourceModel().itemFromIndex(idx)
        row = item.get_parent_row()

        if event.type() != QMouseEvent.MouseButtonRelease:
            return False

        if type(row) == ClassRow:
            if event.button() == Qt.MouseButton.LeftButton:
                if item.get_header() == 'Disable':
                    if 'disable' in row.get_node_rows()[0].get_node().knobs().keys():
                                                                # assuming if one child NodeRow has a disable knob
                                                                # all child rows for that ClassRow do as well
                        if item.checkState() == Qt.Checked:
                            check_state = Qt.Unchecked
                        else:
                            check_state = Qt.Checked
                        item.setCheckState(check_state)
                        for node_row in row.get_node_rows():
                            node_row.get_item('Disable').setCheckState(check_state)
                            node_row.get_node().knob('disable').setValue(check_state == Qt.Checked)

                    return True

        elif type(row) == NodeRow:
            if event.button() == Qt.MouseButton.LeftButton:
                if item.get_header() == 'Node':
                    node = item.get_parent_row().get_node()
                    nuke.zoom(3, (node.xpos() + (node.screenWidth()/2), node.ypos() + (node.screenHeight()/2)))

                    return True
                elif item.get_header() == 'Disable':
                    if 'disable' in row.get_node().knobs().keys():
                        if item.checkState() == Qt.Checked:
                            check_state = Qt.Unchecked
                        else:
                            check_state = Qt.Checked
                        item.setCheckState(check_state)
                        row.get_item('Disable').setCheckState(check_state)
                        row.get_node().knob('disable').setValue(check_state == Qt.Checked)

                    return True
        return False

    def paint(self, painter, option, index):
        """

        :param painter:
        :type painter: QPainter
        :param option:
        :type option: QStyleOptionViewItem
        :param index:
        :type index: QModelIndex
        """
        super(NodeDelegate, self).paint(painter, option, index)

        painter.save()
        painter.setPen(Qt.black)
        painter.drawRect(option.rect)

        painter.restore()

    def sizeHint(self, option, index):
        """

        :param option:
        :type option: QStyleOptionViewItem
        :param index:
        :type index: QModelIndex
        :return:
        :rtype: QSize
        """
        idx = index.model().mapToSource(index)
        size = QStyledItemDelegate.sizeHint(self, option, idx)
        item = idx.model().itemFromIndex(idx)
        row = item.get_parent_row()
        size.setHeight(row.ROW_HEIGHT)

        return size


class NodeModel(QStandardItemModel):
    HEADER = [
        'Node',
        'Disable'
    ]

    def __init__(self, tree_view):
        """

        :param tree_view:
        :type tree_view: NodeTree
        """
        super(NodeModel, self).__init__()

        self.setHorizontalHeaderLabels(self.HEADER)

        self._tree_view = tree_view

        self._node_dict = {}

    def clear_rows(self):
        count = self.rowCount()
        self.removeRows(0, count)

    def data(self, index, role=Qt.DisplayRole):
        """

        :param index:
        :type index: QModelIndex
        :param role:
        :type role: int
        :return:
        :rtype: QBrush
        """
        item = self.itemFromIndex(index)
        idx = self._tree_view.model().mapFromSource(index)
        row = item.get_parent_row()

        if role == Qt.BackgroundRole:
            color = row.bg_color()

            if idx.row() % 2 == 0:
                color = color.darker(120)
            if not item.isEnabled():
                color = color.darker(110)
            return QBrush(color)

        return QStandardItemModel.data(self, index, role)

    def get_rows(self):
        """

        :return:
        :rtype: list[ClassRow]
        """
        rows = []
        for c in range(self.rowCount()):
            row = self.item(c, 0).get_parent_row()
            rows.append(row)
        return rows

    def populate(self, node_dict):
        """

        :param node_dict: {node class: [node,...]}
        :type node_dict: dict
        """

        def try_int(chunk):
            """

            :param chunk:
            :type chunk: str
            :return:
            :rtype: int|str
            """
            try:
                return int(chunk)
            except:
                return chunk

        def alphanum_key(s, n=False):
            """
            Turn a string into a list of string and number chunks.
            This way numbers sort correctly so "var10" doesn't come before "var2".
            "z23a" -> ["z", 23, "a"]

            :param s:
            :type s: str|nuke.Node
            :return:
            :rtype: list
            """
            if n:
                s = s.name()

            return [try_int(chunk) for chunk in re.split('([0-9]+)', s)]

        def correct_sort(l, n=False):
            l.sort(key=lambda x: alphanum_key(x, n))

        self._node_dict = node_dict

        class_list = node_dict.keys()
        correct_sort(class_list)
        for i, node_class in enumerate(class_list):                                 # enumerate so order can be stored
            class_row = ClassRow(node_class, self, node_dict[node_class][0], i)
            self.appendRow(class_row.items())
            node_list = node_dict[node_class]
            correct_sort(node_list, True)
            for j, node in enumerate(node_list):
                node_row = NodeRow(class_row, self, node, j)
                class_row.append_row(node_row)
        self._tree_view.sortByColumn(self.HEADER.index('Node'), Qt.AscendingOrder)


class ClassRow(QObject):
    ROW_HEIGHT = 25

    def __init__(self, node_class, model, first_node, order):
        """

        :param node_class: The class of the nodes
        :type node_class: str
        :param model: tree model
        :type model: NodeModel
        :param first_node: first node of the children
        :type first_node: nuke.Node
        """
        super(ClassRow, self).__init__()

        self._node_class = node_class
        self._model = model
        self._items = dict()
        self._first_node = first_node

        self._children = []
        """:type: list[NodeRow]"""

        self._back_color = QColor(110, 110, 110)

        self._build_items(order)

    def append_row(self, node_row):
        """

        :param node_row: Node row being appended
        :type node_row: NodeRow
        """
        self.items()[0].appendRow(node_row.items())
        self._children.append(node_row)

    def bg_color(self):
        return self._back_color

    def first_item(self):
        """

        :return: the item at column 0
        :rtype: NodeItem
        """
        for item in self.items():
            index = self._model.indexFromItem(item)
            if index.column() == 0:
                return item

    def get_header_name(self, item):
        """

        :param item:
        :type item: NodeItem
        :return: the header of the column of the item
        :rtype: str
        """
        if item in self._items.values():
            for header in self._model.HEADER:
                if self._items[header] == item:
                    return header
        return None

    def get_item(self, header):
        """

        :param header:
        :type header: str
        :return: the item for that header
        :rtype: NodeItem
        """
        return self._items[header]

    def get_node_rows(self):
        return self._children

    def items(self):
        """

        :return: list of items for the row
        :rtype: list[NodeItem]
        """
        items = list()
        for header in self._model.HEADER:
            items.append(self._items[header])
        return items

    def _build_items(self, order):
        """

        :param order:
        :type order: int
        """
        for header in self._model.HEADER:
            item = NodeItem(self)
            item.setSelectable(False)
            item.setEditable(False)

            if header == 'Node':
                item.setText(self._node_class)
                item.setData(order, Qt.UserRole)                    # sort order called by tree
            elif header == 'Disable':
                if 'disable' in self._first_node.knobs().keys():
                    item.setCheckable(True)

            self._items[header] = item


class NodeRow(QObject):
    ROW_HEIGHT = 30

    def __init__(self, parent_class_row, model, node, order):
        """

        :param parent_class_row:
        :type parent_class_row: ClassRow
        :param model:
        :type model: NodeModel
        :param node:
        :type node: nuke.Node
        """
        super(NodeRow, self).__init__()

        self._parent_class_row = parent_class_row
        self._model = model
        self._items = dict()
        self._node = node

        self._back_color = QColor(79, 79, 79)

        self._build_items(order)

    def bg_color(self):
        return self._back_color

    def first_item(self):
        """


        :return:
        :rtype: NodeItem
        """
        for item in self.items():
            index = self._model.indexFromItem(item)
            """:type: QModelIndex"""
            if index.column() == 0:
                return item

    def get_header_name(self, item):
        """

        :param item:
        :type item: NodeItem
        :return:
        :rtype: str
        """
        if item in self._items.values():
            for header in self._model.HEADER:
                if self._items[header] == item:
                    return header
        return None

    def get_item(self, header):
        """

        :param header:
        :type header: str
        :return:
        :rtype: NodeItem
        """
        return self._items[header]

    def get_node(self):
        return self._node

    def get_parent_class_row(self):
        return self._parent_class_row

    def items(self):
        """

        :return:
        :rtype: list[NodeItem]
        """
        items = list()
        for header in self._model.HEADER:
            items.append(self._items[header])
        return items

    def _build_items(self, order):
        """

        :param order:
        :type order: int
        """
        for header in self._model.HEADER:
            item = NodeItem(self)
            item.setSelectable(False)

            if header == 'Node':
                item.setText(self._node.name())
                item.setData(order, Qt.UserRole)                                # sort order called by tree
            elif header == 'Disable':
                if 'disable' in self._node.knobs().keys():
                    item.setCheckable(True)
                    if self._node.knob('disable').value():
                        check_state = Qt.Checked
                    else:
                        check_state = Qt.Unchecked
                    item.setCheckState(check_state)
                else:
                    item.setEnabled(False)
                    parent_dis_item = self._parent_class_row.get_item('Disable')
                    if parent_dis_item.isEnabled():
                        parent_dis_item.setEnabled(False)

            self._items[header] = item


class NodeItem(QStandardItem):
    def __init__(self, row):
        """

        :param row:
        :type row: ClassRow|NodeRow
        """
        super(NodeItem, self).__init__()

        self._parentRow = row
        self.setEditable(False)

    def __eq__(self, other):
        return str(self) == str(other)

    def get_header(self):
        return self.get_parent_row().get_header_name(self)

    def get_parent_row(self):
        return self._parentRow


def main():
    nuke.ui = NodeLister()
    nuke.ui.show()

if __name__ == '__main__':
    main()
