# Building on Your PyQt5 Browser — Developer Guide

This guide covers how to extend your existing browser with new features. Each section is self-contained and builds on the patterns already in your code.

---

## Core Concepts to Know First

### Signals and Slots

PyQt5's entire event system runs on signals and slots. A **signal** fires when something happens; a **slot** is any callable that responds to it.

```python
# Connecting a signal to a slot
some_widget.someSignal.connect(self.my_method)

# Connecting to a lambda inline
some_widget.someSignal.connect(lambda value: print(value))

# Disconnecting
some_widget.someSignal.disconnect(self.my_method)
```

You already use this pattern throughout. Any new feature you add will follow this same structure.

### Getting the Active Browser Tab

Almost every feature needs a reference to whichever tab is currently open. This pattern is your bread and butter:

```python
def some_action(self):
    browser = self.tabs.currentWidget()
    if not browser or self.tabs.tabText(self.tabs.currentIndex()) == "+":
        return  # guard against the + tab
    # do something with browser
```

### `QWebEnginePage` vs `QWebEngineView`

- `QWebEngineView` is the visible widget you put in a tab.
- `QWebEnginePage` is the underlying engine that owns the URL, title, history, and JavaScript context. Access it via `browser.page()`.

```python
browser.page().title()       # page title string
browser.page().url()         # current QUrl
browser.page().history()     # QWebEngineHistory object
browser.page().runJavaScript("document.title")  # execute JS
```

---

## Adding Keyboard Shortcuts

Use `QShortcut` with a `QKeySequence`. Add these inside `__init__` after your toolbar setup.

```python
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtGui import QKeySequence

# New tab
QShortcut(QKeySequence("Ctrl+T"), self).activated.connect(self.add_new_tab)

# Close tab
QShortcut(QKeySequence("Ctrl+W"), self).activated.connect(
    lambda: self.close_tab(self.tabs.currentIndex())
)

# Reload
QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(
    lambda: self.tabs.currentWidget().reload()
)

# Focus URL bar
QShortcut(QKeySequence("Ctrl+L"), self).activated.connect(
    lambda: (self.urlbar.setFocus(), self.urlbar.selectAll())
)

# Navigate back/forward
QShortcut(QKeySequence("Alt+Left"), self).activated.connect(
    lambda: self.tabs.currentWidget().back()
)
QShortcut(QKeySequence("Alt+Right"), self).activated.connect(
    lambda: self.tabs.currentWidget().forward()
)
```

---

## Smarter URL Bar

Right now the URL bar only loads URLs. A real browser detects whether you typed a URL or a search query.

```python
def navigate_to_url(self):
    text = self.urlbar.text().strip()

    # Detect if it's a search query vs a URL
    is_url = (
        "." in text and " " not in text
    ) or text.startswith("http")

    if is_url:
        if "://" not in text:
            text = "https://" + text
        url = QUrl(text)
    else:
        # Treat as a search query
        query = QUrl.toPercentEncoding(text)
        url = QUrl(f"https://www.google.com/search?q={query.data().decode()}")

    browser = self.tabs.currentWidget()
    if browser:
        browser.setUrl(url)
```

You can swap the search engine by replacing the Google URL with DuckDuckGo (`https://duckduckgo.com/?q=`), Bing, etc.

---

## Bookmarks

### Data Model

Store bookmarks as a list of dicts in memory (or persist to JSON for saving between sessions).

```python
# In __init__
self.bookmarks = []  # [{"title": "...", "url": "..."}]
```

### Saving a Bookmark

```python
def bookmark_current_page(self):
    browser = self.tabs.currentWidget()
    if not browser:
        return
    entry = {
        "title": browser.page().title(),
        "url": browser.page().url().toString()
    }
    if entry not in self.bookmarks:
        self.bookmarks.append(entry)
        print(f"Bookmarked: {entry['title']}")
```

Wire this to a toolbar button or `Ctrl+D`.

### Showing Bookmarks in a Menu

```python
from PyQt5.QtWidgets import QMenu, QAction

def show_bookmarks_menu(self):
    menu = QMenu(self)
    for bm in self.bookmarks:
        action = QAction(bm["title"], self)
        action.triggered.connect(
            lambda checked, url=bm["url"]: self.tabs.currentWidget().setUrl(QUrl(url))
        )
        menu.addAction(action)
    # Show the menu at the cursor
    menu.exec_(self.cursor().pos())
```

### Persisting Bookmarks to Disk

```python
import json

def save_bookmarks(self):
    with open("bookmarks.json", "w") as f:
        json.dump(self.bookmarks, f, indent=2)

def load_bookmarks(self):
    try:
        with open("bookmarks.json") as f:
            self.bookmarks = json.load(f)
    except FileNotFoundError:
        self.bookmarks = []
```

Call `load_bookmarks()` in `__init__` and `save_bookmarks()` on close.

---

## Browsing History

### Tracking History

```python
# In __init__
self.history = []  # [{"title": "...", "url": "..."}]
```

Connect to `urlChanged` globally by adding this to `add_new_tab()`:

```python
browser.urlChanged.connect(self.record_history)
```

```python
def record_history(self, q):
    browser = self.sender()  # the QWebEngineView that fired
    entry = {
        "title": browser.page().title(),
        "url": q.toString()
    }
    self.history.append(entry)
```

### Per-Tab Navigation History

`QWebEnginePage` has a built-in history object you can query without tracking it yourself:

```python
def get_tab_history(self):
    browser = self.tabs.currentWidget()
    history = browser.page().history()

    for i in range(history.count()):
        item = history.itemAt(i)
        print(item.title(), item.url().toString())

    # Navigate to a specific history entry
    history.goToItem(history.itemAt(2))
```

---

## Find-in-Page (Ctrl+F)

`QWebEngineView` has built-in text search via `findText()`.

```python
from PyQt5.QtWidgets import QLineEdit, QDockWidget

def setup_find_bar(self):
    self.find_bar = QLineEdit(self)
    self.find_bar.setPlaceholderText("Find on page...")
    self.find_bar.textChanged.connect(self.do_find)
    self.find_bar.hide()

    # Dock it at the bottom
    dock = QDockWidget(self)
    dock.setWidget(self.find_bar)
    dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
    self.addDockWidget(Qt.BottomDockWidgetArea, dock)

def do_find(self, text):
    browser = self.tabs.currentWidget()
    if browser:
        browser.findText(text)  # highlights matches as you type

def toggle_find_bar(self):
    if self.find_bar.isVisible():
        self.find_bar.hide()
        self.tabs.currentWidget().findText("")  # clear highlights
    else:
        self.find_bar.show()
        self.find_bar.setFocus()
```

Wire `toggle_find_bar` to `Ctrl+F`.

---

## Download Manager

Handle file downloads by connecting to the page's download request signal.

```python
from PyQt5.QtWebEngineWidgets import QWebEngineDownloadItem
from PyQt5.QtWidgets import QFileDialog

def setup_downloads(self):
    # Connect once at the profile level, not per-tab
    from PyQt5.QtWebEngineWidgets import QWebEngineProfile
    QWebEngineProfile.defaultProfile().downloadRequested.connect(self.handle_download)

def handle_download(self, download: QWebEngineDownloadItem):
    # Ask the user where to save
    path, _ = QFileDialog.getSaveFileName(self, "Save File", download.suggestedFileName())
    if path:
        download.setPath(path)
        download.accept()
        download.downloadProgress.connect(
            lambda received, total: print(f"Download: {received}/{total} bytes")
        )
    else:
        download.cancel()
```

Call `setup_downloads()` once in `__init__`.

---

## Custom Context Menu (Right-Click Menu)

Override the default context menu to add your own options.

```python
class BrowserView(QWebEngineView):
    def contextMenuEvent(self, event):
        menu = self.page().createStandardContextMenu()

        # Add a custom action
        open_new_tab = QAction("Open Link in New Tab", self)
        open_new_tab.triggered.connect(lambda: print("open in new tab"))  # wire up as needed
        menu.insertAction(menu.actions()[0], open_new_tab)

        menu.exec_(event.globalPos())
```

Then in `add_new_tab`, replace `QWebEngineView()` with `BrowserView()`.

---

## Intercepting Requests (Ad Block / Custom Headers)

Use `QWebEngineUrlRequestInterceptor` to inspect or block outgoing requests.

```python
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor

class RequestInterceptor(QWebEngineUrlRequestInterceptor):
    BLOCKED_DOMAINS = {"ads.example.com", "tracker.example.com"}

    def interceptRequest(self, info):
        url = info.requestUrl().host()
        if url in self.BLOCKED_DOMAINS:
            info.block(True)
```

Register it once on the default profile:

```python
# In __init__
from PyQt5.QtWebEngineWidgets import QWebEngineProfile
interceptor = RequestInterceptor()
QWebEngineProfile.defaultProfile().setUrlRequestInterceptor(interceptor)
```

---

## Injecting JavaScript into Pages

Use `runJavaScript` on the page to interact with the DOM after a page loads.

```python
def inject_script(self):
    browser = self.tabs.currentWidget()
    # Example: get the page's H1 text
    browser.page().runJavaScript(
        "document.querySelector('h1')?.innerText",
        lambda result: print("H1:", result)
    )
```

To inject CSS (e.g., dark mode):

```python
def inject_dark_mode(self):
    css = "body { background: #1e1e1e !important; color: #d4d4d4 !important; }"
    js = f"""
        var style = document.createElement('style');
        style.textContent = `{css}`;
        document.head.appendChild(style);
    """
    browser = self.tabs.currentWidget()
    browser.page().runJavaScript(js)
```

---

## Persistent Settings with `QSettings`

Use `QSettings` to save and restore things like window size, home page, or zoom level between sessions.

```python
from PyQt5.QtCore import QSettings

# In __init__ — load settings
self.settings = QSettings("MasonKimball05", "MyBrowser")
home = self.settings.value("home_url", "https://www.google.com")
geometry = self.settings.value("geometry")
if geometry:
    self.restoreGeometry(geometry)

# In closeEvent — save settings
def closeEvent(self, event):
    self.settings.setValue("geometry", self.saveGeometry())
    event.accept()
```

Settings are stored in the OS-appropriate location (registry on Windows, `~/.config` on Linux/macOS).

---

## Printing

You already import `QtPrintSupport`. Here's how to wire it up.

```python
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter

def print_page(self):
    browser = self.tabs.currentWidget()
    if not browser:
        return
    printer = QPrinter()
    dialog = QPrintDialog(printer, self)
    if dialog.exec_() == QPrintDialog.Accepted:
        browser.page().print(printer, lambda success: print("Print success:", success))
```

Wire this to `Ctrl+P` or a menu action.

---

## Zoom Controls

`QWebEngineView` has built-in zoom factor support.

```python
def zoom_in(self):
    browser = self.tabs.currentWidget()
    browser.setZoomFactor(min(browser.zoomFactor() + 0.1, 3.0))

def zoom_out(self):
    browser = self.tabs.currentWidget()
    browser.setZoomFactor(max(browser.zoomFactor() - 0.1, 0.25))

def zoom_reset(self):
    self.tabs.currentWidget().setZoomFactor(1.0)
```

Wire to `Ctrl++`, `Ctrl+-`, `Ctrl+0`.

---

## Useful `QWebEngineView` Methods Reference

| Method | What it does |
|---|---|
| `.setUrl(QUrl)` | Navigate to a URL |
| `.url()` | Returns current `QUrl` |
| `.back()` / `.forward()` | History navigation |
| `.reload()` / `.stop()` | Reload or cancel loading |
| `.zoomFactor()` / `.setZoomFactor(f)` | Get/set zoom (1.0 = 100%) |
| `.findText(str)` | Highlight matching text on page |
| `.page().title()` | Current page title |
| `.page().runJavaScript(str, cb)` | Execute JS, optional callback |
| `.page().history()` | `QWebEngineHistory` object |
| `.page().print(printer, cb)` | Print the page |
| `.loadProgress` signal | Fires with 0–100 during loading |
| `.loadStarted` signal | Fires when a load begins |
| `.loadFinished` signal | Fires when load completes (`bool` success) |
| `.urlChanged` signal | Fires on every URL change |
| `.titleChanged` signal | Fires when the page title changes |

---

## Suggested Build Order

If you want a path forward, here's a reasonable order of increasing complexity:

1. Keyboard shortcuts — easiest, no new widgets needed
2. Smarter URL bar with search fallback
3. Zoom controls
4. Find-in-page
5. Bookmarks (in-memory first, then JSON persistence)
6. History tracking
7. Download manager
8. Print support
9. Request interception / ad blocking
10. JavaScript injection / dark mode