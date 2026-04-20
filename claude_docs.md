# PyQt5 Custom Browser — Documentation

**File:** `main.py`  
**Author:** MasonKimball05  
**Stack:** Python 3, PyQt5, QtWebEngine

---

## Overview

This browser is built on top of PyQt5's `QWebEngineView`, which embeds Chromium to handle actual page rendering. The app is structured as a single `QMainWindow` subclass (`MainWindow`) that owns a tab bar, a navigation toolbar, and a URL bar. Each browser tab is its own `QWebEngineView` instance.

---

## Dependencies

```bash
pip install PyQt5 PyQtWebEngine
```

| Module | Purpose |
|---|---|
| `PyQt5.QtCore` | Core Qt types (`QUrl`, signals/slots, `Qt` enum namespace) |
| `PyQt5.QtWidgets` | UI widgets: `QMainWindow`, `QToolBar`, `QTabWidget`, `QLineEdit`, etc. |
| `PyQt5.QtGui` | Fonts, icons, and other GUI resources |
| `PyQt5.QtWebEngineWidgets` | `QWebEngineView` — the embedded Chromium browser |
| `PyQt5.QtPrintSupport` | Print dialog support (imported but not yet wired up) |

---

## Class: `MainWindow`

Inherits from `QMainWindow`. This is the single top-level window for the entire browser.

### `__init__(self, *args, **kwargs)`

Sets up all UI components on startup.

**What it builds, in order:**

1. **Status bar** — A `QStatusBar` at the bottom of the window. Navigation buttons write their `statusTip` here on hover.

2. **Navigation toolbar** — A `QToolBar` added to the top of the window with these actions:

   | Button | Symbol | Action |
   |---|---|---|
   | Back | `←` | Calls `.back()` on the active tab's `QWebEngineView` |
   | Forward | `→` | Calls `.forward()` on the active tab |
   | Reload | `⟳` | Calls `.reload()` on the active tab |
   | Home | `Home` | Navigates active tab to Google |
   | Stop | `Stop` | Calls `.stop()` on the active tab |

3. **URL bar** — A `QLineEdit` widget embedded in the toolbar. Pressing Enter triggers `navigate_to_url()`.

4. **Tab widget** — A `QTabWidget` set as the central widget of the window. Configured with:
   - `setDocumentMode(True)` — removes the frame border around tabs
   - `setMovable(True)` — lets users drag tabs to reorder
   - `setElideMode(Qt.ElideRight)` — truncates long tab titles with `…` on the right
   - `setTabsClosable(True)` — adds an `×` close button on each tab

5. **Initial tabs** — One real browser tab (via `add_new_tab()`) and one `+` placeholder tab (via `add_plus_tab()`).

---

### `update_title(self)`

Sets the OS window title to the current tab's page title.

```python
self.setWindowTitle(current_browser.page().title())
```

> **Note:** This method is defined but not connected to any signal. To auto-update the title as pages load, wire it to `browser.loadFinished` in `add_new_tab()`.

---

### `navigate_home(self)`

Navigates the active tab to `https://www.google.com`.

Triggered by the **Home** toolbar button.

---

### `navigate_to_url(self)`

Reads the URL bar text, prepends `https://` if no scheme is present, and loads it in the active tab.

```python
if not text.startswith("http"):
    text = "https://" + text
```

Triggered by pressing **Enter** in the URL bar (`urlbar.returnPressed`).

> **Known gap:** This only checks for `http` as a prefix, so `ftp://` or `file://` URLs would incorrectly get `https://` prepended. You can fix this with:
> ```python
> if "://" not in text:
>     text = "https://" + text
> ```

---

### `update_urlbar(self, q)`

Updates the URL bar text when the page navigates to a new URL.

**Parameter:** `q` — a `QUrl` object emitted by `QWebEngineView.urlChanged`.

Guards against updating the bar from a background tab by checking:
```python
if current and sender == self:  # only fires for the active tab
```

Connected to each new browser's `urlChanged` signal inside `add_new_tab()`.

---

### `add_new_tab(self, url="https://www.google.com")`

Creates a new browser tab and inserts it before the `+` tab.

**Steps:**
1. Creates a `QWebEngineView` and loads `url`.
2. Scans existing tabs to find the `+` tab index.
3. Inserts the new tab before `+` (or appends it if `+` doesn't exist yet).
4. Switches focus to the new tab.
5. Connects signals:
   - `urlChanged` → `update_urlbar`
   - `loadFinished` → updates the tab's label to the page title

**Default URL:** `https://www.google.com`

> **Heads-up on the `loadFinished` lambda:** The tab index `i` is captured at creation time. If tabs are closed or reordered, `i` may no longer point to the right tab. A more robust approach is to look up the tab by the `browser` object directly:
> ```python
> browser.loadFinished.connect(
>     lambda _, b=browser: self.tabs.setTabText(
>         self.tabs.indexOf(b), b.page().title()
>     )
> )
> ```

---

### `add_plus_tab(self)`

Adds a `+` dummy tab at the far right of the tab bar as a "new tab" button.

**Steps:**
1. Removes any existing `+` tab (prevents duplicates).
2. Appends a blank `QWidget` with the label `"+"`.
3. Hides the close button on the `+` tab:
   ```python
   self.tabs.tabBar().setTabButton(index, QTabBar.RightSide, None)
   ```

---

### `on_tab_changed(self, index)`

Called whenever the user switches tabs (`currentChanged` signal).

If the selected tab is the `+` tab, it opens a new browser tab instead:
```python
if self.tabs.tabText(index) == "+":
    self.add_new_tab()
```

---

### `close_tab(self, i)`

Called when the user clicks the `×` on a tab (`tabCloseRequested` signal).

- Prevents the `+` tab from being closed.
- After removing the tab, checks if any browser tabs remain. If none do, opens a fresh one to avoid an empty window.

---

## Application Entry Point

```python
app = QApplication(sys.argv)
app.setApplicationName("MasonKimball05's Attempt at a Browser")
app.setStyle("Fusion")  # cross-platform flat UI style

window = MainWindow()
app.exec_()            # starts the Qt event loop
```

`app.exec_()` blocks until the window is closed.

---

## Signal/Slot Map

| Signal | Source | Connected To | Effect |
|---|---|---|---|
| `back_btn.triggered` | Back button | `tabs.currentWidget().back()` | Navigate back |
| `forward_btn.triggered` | Forward button | `tabs.currentWidget().forward()` | Navigate forward |
| `reload_btn.triggered` | Reload button | `tabs.currentWidget().reload()` | Reload page |
| `home_btn.triggered` | Home button | `navigate_home()` | Go to Google |
| `stop_btn.triggered` | Stop button | `tabs.currentWidget().stop()` | Stop loading |
| `urlbar.returnPressed` | URL bar Enter | `navigate_to_url()` | Load typed URL |
| `tabs.tabCloseRequested` | Tab × button | `close_tab(i)` | Close a tab |
| `tabs.currentChanged` | Tab switch | `on_tab_changed(index)` | Handle + tab click |
| `browser.urlChanged` | Page navigation | `update_urlbar(q)` | Sync URL bar |
| `browser.loadFinished` | Page load done | lambda | Update tab title |

---

## Possible Next Steps

- **Bookmarks** — store URLs in a list or JSON file; add a toolbar dropdown
- **History** — log `urlChanged` events to a list
- **Search bar vs URL bar** — detect non-URL input and redirect to a search engine (`https://www.google.com/search?q=...`)
- **Tab title fix** — use `self.tabs.indexOf(browser)` in the `loadFinished` lambda instead of the captured index
- **Window title sync** — connect `browser.loadFinished` to `update_title()`
- **Keyboard shortcuts** — `QShortcut` for Ctrl+T (new tab), Ctrl+W (close tab), Ctrl+R (reload)
- **Print support** — wire up `QtPrintSupport` (already imported) to a menu action