import sys
import os
import logging

from PyQt4.Qt import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from graph.verilog_graph import VerilogGraph

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from model.module_list_model import ModuleListModel

from include_path_dialog import IncludePathDialog
from matplot_lib_widget import MatplotLibWidget


FORMAT = '%(asctime)-15s %(message)s'

VERILOG_EXTENSIONS = ["v"]
VERILOG_NAME_EXTENSION = [("Verilog (*.v)")]
PREVIOUS_DIR_KEY = "prev_dir"
INCLUDE_PATH_START_DIR = "include_path_start_dir"
INCLUDE_PATH_DIRS = "include_paths_dirs"


def is_verilog_file(path):
    if not os.path.isfile(str(path)):
        return False
    fname, ext = os.path.splitext(path)
    ext = ext.strip(".")
    return ext in VERILOG_EXTENSIONS


class MainForm (QMainWindow):

    def __init__(self, app, actions):
        super (MainForm, self).__init__()
        self.settings = QSettings("Cospan Design", "verilog-visualizer")
        if not self.settings.contains(INCLUDE_PATH_DIRS):
            self.settings.setValue(INCLUDE_PATH_DIRS, [os.curdir])



        #Configure Settings
        self.actions = actions
        self.logger = logging.getLogger("verilogviz")
        self.setWindowTitle("Verilog Visualizer")
        self.show()

        ## Actions
        exit_action = QAction('&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(quit)

        save_action = QAction("&Save", self)
        save_action.setShortcut('Ctrl+S')

        open_action = QAction("&Open", self)
        open_action.setShortcut('Ctrl+O')

        demo_action = QAction("&Demo", self)
        demo_action.setShortcut('Ctrl+D')

        configure_include_path_action = QAction("Configure &Include Paths", self)
        configure_include_path_action.setShortcut('Ctrl+I')

        save_action.triggered.connect(self.save_clicked)
        open_action.triggered.connect(self.open_clicked)
        demo_action.triggered.connect(self.demo_action)
        configure_include_path_action.triggered.connect(self.actions.configure_include_paths)

        #Toolbar
        self.toolbar = self.addToolBar("main")
        self.toolbar.addAction(exit_action)
        self.toolbar.addAction(demo_action)
        self.toolbar.addAction(configure_include_path_action)

        #Menubar
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        file_menu.addAction(exit_action)
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)

        #Custom Views
        self.verilog_graph = VerilogGraph(app, self.actions)
        #self.verilog_graph = MatplotLibWidget()

        #Project/File Pane
        project_file_view = QSplitter(Qt.Vertical)
        #self.project_list = QListWidget()
        self.project_list = QListView()
        self.project_list.setModel(ModuleListModel(self))

        #self.user_path = "."
        self.user_path = os.path.expanduser("~")
        if self.settings.contains(PREVIOUS_DIR_KEY):
            self.user_path = self.settings.value(PREVIOUS_DIR_KEY, type=str)
            self.logger.info("Loading previous path: %s" % self.user_path)

        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(self.user_path)
        index = self.file_model.index(self.user_path)
        vext = []
        for v in VERILOG_EXTENSIONS:
            vext.append("*.%s" % v)
        self.file_model.setNameFilters(vext)
        self.file_model.setNameFilterDisables(False)
        self.file_view = QTreeView()
        self.file_view.setModel(self.file_model)
        self.file_view.setCurrentIndex(index)

        self.file_view.clicked.connect(self.tree_clicked)
        self.file_model.directoryLoaded.connect(self.tree_directory_loaded)

        self.main_splitter = QSplitter(Qt.Horizontal)
        #self.main_splitter.addWidget(self.file_view)
        project_file_view.addWidget(self.project_list)
        project_file_view.addWidget(self.file_view)
        self.main_splitter.addWidget(project_file_view)
        self.main_splitter.addWidget(self.verilog_graph)

        self.setCentralWidget(self.main_splitter)

        self.show()
        self.logger.debug("Showing")

    def save_clicked(self):
        self.logger.debug("Save Clicked")

    def open_clicked(self):
        self.logger.debug("Open Clicked")

    def demo_action(self):
        self.logger.debug("Demo Action!")
        #self.verilog_graph.add_verilog_module("test", {"test_data":"data"})

    def clear_graph(self):
        self.verilog_graph.clear()

    def draw_module(self, module):
        self.verilog_graph.draw_module(module)

    def add_verilog_project_list_item(self, module):
        if self.project_list.model().in_list(module.name()):
            raise LookupError("Project name in list") 
        
        self.project_list.model().addItem(module) 

    def remove_verilog_project_list_item(self, module_name):
        if not self.project_list.model().in_list(module_name):
            raise LookupError("Project not found in list")
        self.project_list.removeItemWidget(items[0])

    def get_module(self, module_name):
        return self.project_list.model().get_module_by_name(module_name)

    def get_graph(self):
        return self.verilog_graph

    def tree_clicked(self):
        index = self.file_view.currentIndex()
        path = self.file_model.filePath(index)
        if os.path.isdir(str(path)):
            self.user_path = path
            self.logger.info("Start Path changed to: %s" % self.user_path)
        elif is_verilog_file(str(path)):
            self.logger.info("verilog path: %s" % path)
            self.actions.add_verilog_module.emit(0, path)

        for i in range(self.file_model.columnCount()):
            self.file_view.resizeColumnToContents(i)

    def tree_directory_loaded(self):
         for i in range(self.file_model.columnCount()):
            self.file_view.resizeColumnToContents(i)

    def closeEvent(self, event):
        self.logger.debug("Close Event")
        self.settings.setValue(PREVIOUS_DIR_KEY, self.user_path)
        del(self.settings)
        quit()

    def configure_include_paths_dialog(self):
        self.logger.debug("Paths dialog clicked")
        start_path = os.path.expanduser("~")

        if self.settings.contains(INCLUDE_PATH_START_DIR):
            start_path = self.settings.value(INCLUDE_PATH_START_DIR, type = str)

        include_paths = self.settings.value(INCLUDE_PATH_DIRS, type = str)
        self.logger.debug("Loading Paths: %s " % str(include_paths))

        ipd = IncludePathDialog(self)
        ipd.set_path_list(include_paths)
        ipd.set_start_path(start_path)
        result = ipd.exec_()
        paths = ipd.get_path_list()

        if result:
            self.logger.debug("Accepted, new paths: %s" % str(ipd.get_path_list()))
            print "Paths: %s " % str(ipd.get_path_list())
            self.settings.setValue(INCLUDE_PATH_DIRS, ipd.get_path_list())
            self.settings.setValue(INCLUDE_PATH_START_DIR, ipd.get_start_path())
            return True
        else:
            self.logger.debug("Rejected")
            return False

    def get_include_paths(self):
        return self.settings.value(INCLUDE_PATH_DIRS, type = str)

    def update_modules_user_paths(self, paths):
        self.project_list.model().update_modules_user_paths(paths)


