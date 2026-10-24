// المونتير: the Mac window around the local editor (editor/app/server.py).
//
// First run: shows setup.html (bundled) and runs setup.sh (bundled), which installs everything into
// ~/Library/Application Support/Montier without admin rights. After that: starts the local server with the
// installed Python and shows it. The server exits with 75 after an update; the window then starts it again.
// Built by .github/workflows/mac-app.yml with plain swiftc (no Xcode project).
import Cocoa
import WebKit

let port = 47823
let fm = FileManager.default
let home = fm.homeDirectoryForCurrentUser
let support = home.appendingPathComponent("Library/Application Support/Montier")
let code = support.appendingPathComponent("code")
let tools = support.appendingPathComponent("tools")
let updateExit: Int32 = 75

final class AppDelegate: NSObject, NSApplicationDelegate, WKScriptMessageHandler, WKNavigationDelegate, WKUIDelegate {
    var window: NSWindow!
    var web: WKWebView!
    var server: Process?
    var setupProc: Process?
    var quitting = false

    func applicationDidFinishLaunching(_ notification: Notification) {
        buildMenu()
        let cfg = WKWebViewConfiguration()
        cfg.userContentController.add(self, name: "app")
        cfg.mediaTypesRequiringUserActionForPlayback = []
        cfg.preferences.setValue(true, forKey: "developerExtrasEnabled")
        web = WKWebView(frame: .zero, configuration: cfg)
        web.navigationDelegate = self
        web.uiDelegate = self
        web.setValue(false, forKey: "drawsBackground")
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 1320, height: 860),
                          styleMask: [.titled, .closable, .miniaturizable, .resizable], backing: .buffered, defer: false)
        window.title = "المونتير"
        window.minSize = NSSize(width: 900, height: 600)
        window.backgroundColor = NSColor(red: 0.059, green: 0.075, blue: 0.11, alpha: 1)
        window.contentView = web
        window.center()
        window.setFrameAutosaveName("main")
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        if isReady() { startServer() } else { showSetup() }
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }

    func applicationWillTerminate(_ notification: Notification) {
        quitting = true
        server?.terminate()
        setupProc?.terminate()
    }

    // MARK: setup

    func isReady() -> Bool {
        fm.fileExists(atPath: support.appendingPathComponent("ready").path)
            && fm.fileExists(atPath: code.appendingPathComponent("editor/app/server.py").path)
            && fm.fileExists(atPath: tools.appendingPathComponent("venv/bin/python").path)
    }

    func showSetup(error: Bool = false) {
        guard let url = Bundle.main.url(forResource: "setup", withExtension: "html") else { return }
        let target = error ? URL(string: url.absoluteString + "#error")! : url
        web.loadFileURL(target, allowingReadAccessTo: url.deletingLastPathComponent())
    }

    func js(_ source: String) {
        DispatchQueue.main.async { self.web.evaluateJavaScript(source, completionHandler: nil) }
    }

    func quoted(_ s: String) -> String {
        let data = (try? JSONSerialization.data(withJSONObject: [s])) ?? Data("[\"\"]".utf8)
        let arr = String(decoding: data, as: UTF8.self)
        return String(arr.dropFirst().dropLast())
    }

    func toolPath() -> String {
        [tools.appendingPathComponent("venv/bin").path, tools.appendingPathComponent("node/bin").path,
         tools.appendingPathComponent("bin").path, home.appendingPathComponent(".local/bin").path,
         "/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin", "/usr/sbin", "/sbin"].joined(separator: ":")
    }

    func runSetup() {
        guard setupProc == nil, let script = Bundle.main.url(forResource: "setup", withExtension: "sh") else { return }
        stopServer()
        let p = Process()
        p.executableURL = URL(fileURLWithPath: "/bin/bash")
        p.arguments = [script.path]
        var env = ProcessInfo.processInfo.environment
        env["PATH"] = toolPath()
        p.environment = env
        let pipe = Pipe()
        p.standardOutput = pipe
        p.standardError = pipe
        try? fm.createDirectory(at: support.appendingPathComponent("logs"), withIntermediateDirectories: true)
        let logURL = support.appendingPathComponent("logs/setup.log")
        fm.createFile(atPath: logURL.path, contents: nil)
        let log = try? FileHandle(forWritingTo: logURL)
        var buffer = Data()
        let lock = NSLock()
        pipe.fileHandleForReading.readabilityHandler = { [weak self] handle in
            let data = handle.availableData
            guard let self = self, !data.isEmpty else { return }
            log?.write(data)
            lock.lock()
            buffer.append(data)
            var lines: [String] = []
            while let nl = buffer.firstIndex(of: 10) {
                lines.append(String(decoding: buffer[buffer.startIndex..<nl], as: UTF8.self))
                buffer.removeSubrange(buffer.startIndex...nl)
            }
            lock.unlock()
            for line in lines { self.js("onLine(\(self.quoted(line)))") }
        }
        p.terminationHandler = { [weak self] proc in
            pipe.fileHandleForReading.readabilityHandler = nil
            try? log?.close()
            DispatchQueue.main.async {
                guard let self = self else { return }
                self.setupProc = nil
                let ok = proc.terminationStatus == 0
                self.js("onDone(\(ok))")
                if ok { DispatchQueue.main.asyncAfter(deadline: .now() + 1.2) { self.startServer() } }
            }
        }
        setupProc = p
        do { try p.run() } catch {
            setupProc = nil
            js("onLine(\(quoted("❌ " + error.localizedDescription))); onDone(false)")
        }
    }

    // MARK: server

    func startServer() {
        if server != nil { return }
        ping { alive in
            if alive { self.load(); return }       // one is already running (the app was reopened)
            let p = Process()
            p.executableURL = tools.appendingPathComponent("venv/bin/python")
            p.arguments = ["-m", "editor.app.server", "--port", "\(port)"]
            p.currentDirectoryURL = code
            var env = ProcessInfo.processInfo.environment
            env["PATH"] = self.toolPath()
            env["MONTIER_HOME"] = support.path
            env["MONTIER_APP"] = "1"
            env["PYTHONUNBUFFERED"] = "1"
            p.environment = env
            try? fm.createDirectory(at: support.appendingPathComponent("logs"), withIntermediateDirectories: true)
            let logURL = support.appendingPathComponent("logs/server.log")
            if !fm.fileExists(atPath: logURL.path) { fm.createFile(atPath: logURL.path, contents: nil) }
            let log = try? FileHandle(forWritingTo: logURL)
            log?.seekToEndOfFile()
            p.standardOutput = log
            p.standardError = log
            p.terminationHandler = { [weak self] proc in
                DispatchQueue.main.async {
                    guard let self = self else { return }
                    self.server = nil
                    if self.quitting { return }
                    if proc.terminationStatus == updateExit { self.startServer() }
                    else { self.showSetup(error: true) }   // our own stops clear this handler first
                }
            }
            do {
                try p.run()
                self.server = p
                self.waitAndLoad(tries: 0)
            } catch {
                self.showSetup(error: true)
            }
        }
    }

    func stopServer() {
        guard let s = server else { return }
        server = nil
        s.terminationHandler = nil
        s.terminate()
    }

    func restartServer() {
        stopServer()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.8) {
            if self.isReady() { self.startServer() } else { self.showSetup() }
        }
    }

    func ping(_ done: @escaping (Bool) -> Void) {
        var req = URLRequest(url: URL(string: "http://127.0.0.1:\(port)/api/ping")!)
        req.timeoutInterval = 1.5
        URLSession.shared.dataTask(with: req) { _, resp, _ in
            let ok = (resp as? HTTPURLResponse)?.statusCode == 200
            DispatchQueue.main.async { done(ok) }
        }.resume()
    }

    func waitAndLoad(tries: Int) {
        ping { ok in
            if ok { self.load() }
            else if tries < 120 && self.server != nil {
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { self.waitAndLoad(tries: tries + 1) }
            } else if self.server != nil { self.showSetup(error: true) }
        }
    }

    func load() {
        web.load(URLRequest(url: URL(string: "http://127.0.0.1:\(port)/")!))
    }

    // MARK: page → app

    func userContentController(_ controller: WKUserContentController, didReceive message: WKScriptMessage) {
        guard let body = message.body as? [String: Any], let cmd = body["cmd"] as? String else { return }
        switch cmd {
        case "setup": runSetup()
        case "restart": restartServer()
        case "pick": pickFile(types: body["types"] as? [String])
        case "open":
            if let s = body["url"] as? String, let u = URL(string: s) { NSWorkspace.shared.open(u) }
        default: break
        }
    }

    func pickFile(types: [String]?) {
        let panel = NSOpenPanel()
        panel.canChooseFiles = true
        panel.canChooseDirectories = false
        panel.allowsMultipleSelection = false
        let lut = types?.contains("cube") ?? false
        panel.message = lut ? "اختار ملف الألوان" : "اختار الفيديو الخام"
        panel.prompt = "اختار"
        panel.allowedFileTypes = types ?? ["mp4", "mov", "m4v", "mkv", "MP4", "MOV"]
        panel.beginSheetModal(for: window) { result in
            if result == .OK, let url = panel.url { self.js("onPicked(\(self.quoted(url.path)))") }
        }
    }

    // MARK: web view

    func webView(_ webView: WKWebView, decidePolicyFor action: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        if let url = action.request.url, let scheme = url.scheme,
           (scheme == "http" || scheme == "https"), url.host != "127.0.0.1", url.host != "localhost" {
            NSWorkspace.shared.open(url)       // links to the web open in the browser
            decisionHandler(.cancel)
            return
        }
        decisionHandler(.allow)
    }

    func webView(_ webView: WKWebView, createWebViewWith configuration: WKWebViewConfiguration,
                 for action: WKNavigationAction, windowFeatures: WKWindowFeatures) -> WKWebView? {
        if let url = action.request.url {
            if url.host == "127.0.0.1" || url.host == "localhost" { webView.load(action.request) }
            else { NSWorkspace.shared.open(url) }
        }
        return nil
    }

    func webView(_ webView: WKWebView, runOpenPanelWith parameters: WKOpenPanelParameters,
                 initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping ([URL]?) -> Void) {
        let panel = NSOpenPanel()
        panel.canChooseFiles = true
        panel.allowsMultipleSelection = parameters.allowsMultipleSelection
        panel.beginSheetModal(for: window) { result in completionHandler(result == .OK ? panel.urls : nil) }
    }

    func webView(_ webView: WKWebView, runJavaScriptAlertPanelWithMessage message: String,
                 initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping () -> Void) {
        let alert = NSAlert()
        alert.messageText = message
        alert.addButton(withTitle: "تمام")
        alert.beginSheetModal(for: window) { _ in completionHandler() }
    }

    func webView(_ webView: WKWebView, runJavaScriptConfirmPanelWithMessage message: String,
                 initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping (Bool) -> Void) {
        let alert = NSAlert()
        alert.messageText = message
        alert.addButton(withTitle: "إي")
        alert.addButton(withTitle: "لا")
        alert.beginSheetModal(for: window) { r in completionHandler(r == .alertFirstButtonReturn) }
    }

    @available(macOS 12.0, *)
    func webView(_ webView: WKWebView, requestMediaCapturePermissionFor origin: WKSecurityOrigin,
                 initiatedByFrame frame: WKFrameInfo, type: WKMediaCaptureType,
                 decisionHandler: @escaping (WKPermissionDecision) -> Void) {
        decisionHandler(origin.host == "127.0.0.1" ? .grant : .deny)   // voice notes in the editing room
    }

    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {}

    // MARK: menu (copy and paste need it)

    func buildMenu() {
        let main = NSMenu()
        let appItem = NSMenuItem()
        main.addItem(appItem)
        let appMenu = NSMenu()
        appMenu.addItem(withTitle: "حول المونتير", action: #selector(NSApplication.orderFrontStandardAboutPanel(_:)), keyEquivalent: "")
        appMenu.addItem(.separator())
        appMenu.addItem(withTitle: "إعادة التحميل", action: #selector(reloadPage), keyEquivalent: "r")
        appMenu.addItem(withTitle: "إخفاء المونتير", action: #selector(NSApplication.hide(_:)), keyEquivalent: "h")
        appMenu.addItem(.separator())
        appMenu.addItem(withTitle: "إنهاء المونتير", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        appItem.submenu = appMenu

        let editItem = NSMenuItem()
        main.addItem(editItem)
        let edit = NSMenu(title: "تعديل")
        edit.addItem(withTitle: "تراجع", action: Selector(("undo:")), keyEquivalent: "z")
        edit.addItem(withTitle: "إعادة", action: Selector(("redo:")), keyEquivalent: "Z")
        edit.addItem(.separator())
        edit.addItem(withTitle: "قص", action: #selector(NSText.cut(_:)), keyEquivalent: "x")
        edit.addItem(withTitle: "نسخ", action: #selector(NSText.copy(_:)), keyEquivalent: "c")
        edit.addItem(withTitle: "لصق", action: #selector(NSText.paste(_:)), keyEquivalent: "v")
        edit.addItem(withTitle: "تحديد الكل", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a")
        editItem.submenu = edit

        let winItem = NSMenuItem()
        main.addItem(winItem)
        let win = NSMenu(title: "النافذة")
        win.addItem(withTitle: "تصغير", action: #selector(NSWindow.performMiniaturize(_:)), keyEquivalent: "m")
        win.addItem(withTitle: "إغلاق", action: #selector(NSWindow.performClose(_:)), keyEquivalent: "w")
        winItem.submenu = win
        NSApp.mainMenu = main
    }

    @objc func reloadPage() {
        if server != nil { load() } else if isReady() { startServer() } else { web.reload() }
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.setActivationPolicy(.regular)
app.run()
