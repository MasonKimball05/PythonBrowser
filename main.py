# This my attempt at learning how to make a custom browser using Python
# I am using Python because at time point I'm not overly interested in making a full top-down browser
# Maybe one day, but for now I am contempt with first learning how to use existing tools to do so

# Required Packages
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtPrintSupport import *
import os
import qtawesome as qta
import sys

class TabBar(QTabBar):
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        # Only snap the + tab back once the drag is fully done, not during it
        for i in range(self.count()):
            if self.tabText(i) == "+":
                if i != self.count() - 1:
                    self.moveTab(i, self.count() - 1)
                break


class BrowserTabs(QTabWidget):
    def __init__(self):
        super().__init__()
        self.setTabBar(TabBar())


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        navtb = QToolBar("Navigation")
        self.addToolBar(navtb)

        back_btn = QAction(qta.icon("fa5s.arrow-left", color="#e0e0e0"), "Back", self)
        back_btn.setStatusTip("Back to previous page")
        back_btn.triggered.connect(lambda: self.tabs.currentWidget().back())
        navtb.addAction(back_btn)

        forward_btn = QAction(qta.icon("fa5s.arrow-right", color="#e0e0e0"), "Forward", self)
        forward_btn.setStatusTip("Forward to next page")
        forward_btn.triggered.connect(lambda: self.tabs.currentWidget().forward())
        navtb.addAction(forward_btn)

        reload_btn = QAction(qta.icon("fa5s.redo", color="#e0e0e0"), "Reload", self)
        reload_btn.setStatusTip("Reload page")
        reload_btn.triggered.connect(lambda: self.tabs.currentWidget().reload())
        navtb.addAction(reload_btn)

        stop_btn = QAction(qta.icon("fa5s.times", color="#e0e0e0"), "Stop", self)
        stop_btn.setStatusTip("Stop loading page")
        stop_btn.triggered.connect(lambda: self.tabs.currentWidget().stop())
        navtb.addAction(stop_btn)

        home_btn = QAction(qta.icon("fa5s.home", color="#e0e0e0"), "Home", self)
        home_btn.setStatusTip("Go Home")
        home_btn.triggered.connect(self.navigate_home)
        navtb.addAction(home_btn)

        navtb.addSeparator()

        self.urlbar = QLineEdit()

        self.urlbar.returnPressed.connect(self.navigate_to_url)

        navtb.addWidget(self.urlbar)

        self.tabs = BrowserTabs()
        self.setCentralWidget(self.tabs)
        self.tabs.setDocumentMode(True)
        self.tabs.setMovable(True)
        self.tabs.setElideMode(Qt.ElideRight)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.add_new_tab()
        self.add_plus_tab()
        self.resize(1200, 800)
        self.show()


    def update_title(self):
        current_browser = self.tabs.currentWidget()
        if current_browser:
            self.setWindowTitle(current_browser.page().title())

    def navigate_home(self):
        current_browser = self.tabs.currentWidget()
        if current_browser:
            current_browser.setUrl(QUrl("https://www.google.com"))


    def navigate_to_url(self):
        text = self.urlbar.text().strip()
        # QUrl.fromUserInput handles URLs, bare domains, and search terms automatically
        url = QUrl.fromUserInput(text)
        current_browser = self.tabs.currentWidget()
        if current_browser:
            current_browser.setUrl(url)

    def update_urlbar(self, q):
        current = self.tabs.currentWidget()
        sender = self.sender()
        if current and sender == current:
            self.urlbar.setText(q.toString())
            self.urlbar.setCursorPosition(0)


    def add_new_tab(self, url="https://www.google.com"):
        browser = QWebEngineView()
        browser.setUrl(QUrl(url))

        # insert before + tab if it exists
        plus_index = None
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == "+":
                plus_index = i
                break

        if plus_index is None:
            index = self.tabs.addTab(browser, "New Tab")
        else:
            index = self.tabs.insertTab(plus_index, browser, "New Tab")

        self.tabs.setCurrentWidget(browser)

        browser.urlChanged.connect(self.update_urlbar)
        # titleChanged fires whenever the page title updates, so we wire both title and window
        browser.titleChanged.connect(
            lambda title, browser=browser:
            self.tabs.setTabText(self.tabs.indexOf(browser), title or "New Tab")
        )
        browser.titleChanged.connect(lambda _: self.update_title())

    def add_plus_tab(self):
        # remove any existing + tab
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == "+":
                self.tabs.removeTab(i)
                break

        # add + tab at end
        index = self.tabs.addTab(QWidget(), "+")

        # hide close button on + tab
        self.tabs.tabBar().setTabButton(index, QTabBar.RightSide, None)

    def on_tab_changed(self, index):
        # if + tab clicked, open new tab
        if self.tabs.tabText(index) == "+":
            self.add_new_tab()
            return
        browser = self.tabs.widget(index)
        if browser:
            self.urlbar.setText(browser.url().toString())

    def close_tab(self, i):
        if self.tabs.tabText(i) == "+":
            return

        # Pre-select a valid tab so Qt doesn't auto-select + after removal
        if self.tabs.count() > 2:
            self.tabs.setCurrentIndex(i - 1 if i > 0 else 1)

        self.tabs.removeTab(i)

        # if no browser tabs left, ensure at least one exists
        has_browser = any(self.tabs.tabText(j) != "+" for j in range(self.tabs.count()))
        if not has_browser:
            self.add_new_tab()

app = QApplication(sys.argv)
app.setApplicationName("MasonKimball05's Attempt at a Browser")
app.setStyle("Fusion")
app.setStyleSheet("""
    QMainWindow, QWidget {
        background-color: #1e1e1e;
        color: #e0e0e0;
    }
    QToolBar {
        background-color: #2b2b2b;
        border-bottom: 1px solid #3a3a3a;
        padding: 4px 6px;
        spacing: 4px;
    }
    QToolBar QToolButton {
        color: #e0e0e0;
        background: transparent;
        border: none;
        border-radius: 4px;
        padding: 4px;
    }
    QToolBar QToolButton:hover { background-color: #3a3a3a; }
    QToolBar QToolButton:pressed { background-color: #4a4a4a; }
    QLineEdit {
        background-color: #3a3a3a;
        color: #e0e0e0;
        border: 1px solid #555;
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 13px;
        selection-background-color: #0078d4;
    }
    QLineEdit:focus { border: 1px solid #0078d4; }
    QTabWidget::pane { border: none; background-color: #1e1e1e; }
    QTabBar {
        background-color: #2b2b2b;
    }
    QTabBar::tab {
        background-color: #2b2b2b;
        color: #999;
        padding: 6px 14px;
        min-width: 80px;
        max-width: 200px;
        border-right: 1px solid #3a3a3a;
    }
    QTabBar::tab:selected {
        background-color: #1e1e1e;
        color: #e0e0e0;
        border-top: 2px solid #0078d4;
    }
    QTabBar::tab:hover:!selected { background-color: #363636; }
    QTabBar::tab:last {
        background-color: transparent;
        border: none;
        color: #aaa;
        min-width: 28px;
        max-width: 28px;
        font-size: 16px;
        padding: 4px 8px;
    }
    QTabBar::tab:last:hover {
        background-color: #3a3a3a;
        border-radius: 4px;
        color: #e0e0e0;
    }
    QStatusBar {
        background-color: #2b2b2b;
        color: #888;
        border-top: 1px solid #3a3a3a;
        font-size: 11px;
    }
""")

window = MainWindow()

# Loop
app.exec_()