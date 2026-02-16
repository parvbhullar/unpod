// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{
    Manager, AppHandle, State, Window, Listener,
    image::Image,
    menu::{Menu, MenuItem, PredefinedMenuItem, Submenu},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
};
use tauri_plugin_store::StoreExt;
use tauri_plugin_opener::OpenerExt;
use tauri_plugin_notification::NotificationExt;
use std::sync::Mutex;

// Only import DialogExt in production builds where it's used
#[cfg(not(debug_assertions))]
use tauri_plugin_dialog::DialogExt;

// State for managing notification count and server process
struct AppState {
    notification_count: Mutex<u32>,
    server_process: Mutex<Option<u32>>, // Store PID of the Node.js server process
}

// ============================================
// IPC Commands - Session Management
// ============================================

#[tauri::command]
fn session_get_token(app: AppHandle) -> Result<Option<String>, String> {
    let store = app.store("session.json")
        .map_err(|e| e.to_string())?;

    match store.get("authToken") {
        Some(value) => Ok(value.as_str().map(|s| s.to_string())),
        None => Ok(None),
    }
}

#[tauri::command]
fn session_set_token(app: AppHandle, token: String) -> Result<bool, String> {
    let store = app.store("session.json")
        .map_err(|e| e.to_string())?;

    store.set("authToken", serde_json::json!(token));
    store.save().map_err(|e| e.to_string())?;
    Ok(true)
}

#[tauri::command]
fn session_delete_token(app: AppHandle) -> Result<bool, String> {
    let store = app.store("session.json")
        .map_err(|e| e.to_string())?;

    store.delete("authToken");
    store.save().map_err(|e| e.to_string())?;
    Ok(true)
}

#[tauri::command]
fn session_get(app: AppHandle, key: String) -> Result<Option<String>, String> {
    let store = app.store("session.json")
        .map_err(|e| e.to_string())?;

    match store.get(&key) {
        Some(value) => Ok(value.as_str().map(|s| s.to_string())),
        None => Ok(None),
    }
}

#[tauri::command]
fn session_set(app: AppHandle, key: String, value: String) -> Result<bool, String> {
    let store = app.store("session.json")
        .map_err(|e| e.to_string())?;

    store.set(&key, serde_json::json!(value));
    store.save().map_err(|e| e.to_string())?;
    Ok(true)
}

#[tauri::command]
fn session_delete(app: AppHandle, key: String) -> Result<bool, String> {
    let store = app.store("session.json")
        .map_err(|e| e.to_string())?;

    store.delete(&key);
    store.save().map_err(|e| e.to_string())?;
    Ok(true)
}

#[tauri::command]
fn session_clear(app: AppHandle) -> Result<bool, String> {
    let store = app.store("session.json")
        .map_err(|e| e.to_string())?;

    store.clear();
    store.save().map_err(|e| e.to_string())?;
    Ok(true)
}

// ============================================
// IPC Commands - System Information
// ============================================

#[tauri::command]
fn get_platform() -> String {
    std::env::consts::OS.to_string()
}

#[tauri::command]
fn get_app_version(app: AppHandle) -> String {
    app.package_info().version.to_string()
}

#[tauri::command]
fn get_theme() -> String {
    // Note: Theme detection would require platform-specific implementation
    // For now, return a default value
    "light".to_string()
}

// ============================================
// IPC Commands - Window Controls
// ============================================

#[tauri::command]
fn window_minimize(window: Window) {
    let _ = window.minimize();
}

#[tauri::command]
fn window_maximize(window: Window) {
    if window.is_maximized().unwrap_or(false) {
        let _ = window.unmaximize();
    } else {
        let _ = window.maximize();
    }
}

#[tauri::command]
fn window_close(window: Window) {
    let _ = window.close();
}

#[tauri::command]
async fn open_external(app: AppHandle, url: String) -> Result<(), String> {
    app.opener()
        .open_url(&url, None::<&str>)
        .map_err(|e| e.to_string())
}

// ============================================
// Helper Functions
// ============================================

/// Activate app and bring window to front
fn activate_app_window(app: &AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.unminimize();
        let _ = window.show();
        let _ = window.set_focus();

        // On macOS, also activate the app at system level
        #[cfg(target_os = "macos")]
        {
            use cocoa::appkit::NSApplication;
            unsafe {
                let app = cocoa::appkit::NSApp();
                app.activateIgnoringOtherApps_(cocoa::base::YES);
            }
        }

        println!("App window activated and focused");
    }
}

// ============================================
// IPC Commands - Notifications
// ============================================

#[tauri::command]
async fn check_notification_permission(app: AppHandle) -> Result<String, String> {
    use tauri_plugin_notification::PermissionState;

    let permission = app.notification().permission_state()
        .map_err(|e| e.to_string())?;

    let state = match permission {
        PermissionState::Granted => "granted",
        PermissionState::Denied => "denied",
        _ => "unknown", // Default for any other states
    };

    Ok(state.to_string())
}

#[tauri::command]
async fn request_notification_permission(app: AppHandle) -> Result<bool, String> {
    use tauri_plugin_notification::PermissionState;

    let permission = app.notification().request_permission()
        .map_err(|e| e.to_string())?;

    Ok(permission == PermissionState::Granted)
}

#[tauri::command]
async fn show_notification(
    app: AppHandle,
    title: String,
    body: String,
) -> Result<(), String> {
    use tauri_plugin_notification::PermissionState;

    println!("=== NOTIFICATION DEBUG ===");

    // Check current permission state
    let current_state = app.notification().permission_state()
        .map_err(|e| format!("Failed to check permission: {}", e))?;
    println!("Current permission state: {:?}", current_state);

    // Request permission if needed
    let permission_state = app.notification().request_permission()
        .map_err(|e| format!("Permission request failed: {}", e))?;
    println!("Permission after request: {:?}", permission_state);

    if permission_state != PermissionState::Granted {
        let err_msg = format!("Notification permission not granted. State: {:?}", permission_state);
        println!("{}", err_msg);
        return Err(err_msg);
    }

    println!("Attempting to show notification: title='{}', body='{}'", title, body);

    // Try to load and use app icon
    let icon_result = || -> Result<(), Box<dyn std::error::Error>> {
        // Get the icon path - use different paths for dev vs prod
        let icon_path = if cfg!(debug_assertions) {
            // Development: icon is in src-tauri/icons/
            std::path::PathBuf::from("icons/icon.png")
        } else {
            // Production: icon is in resources
            app.path().resource_dir()?.join("icons/icon.png")
        };

        println!("Loading icon from: {:?}", icon_path);

        // Check if icon exists
        if icon_path.exists() {
            // Show notification with icon - notifications are clickable by default on most platforms
            app.notification()
                .builder()
                .title(&title)
                .body(&body)
                .icon(icon_path.to_string_lossy().to_string())
                .show()?;

            println!("Notification with icon sent successfully!");
            return Ok(());
        }

        Err("Icon file not found".into())
    };

    // Try with icon first, fallback to no icon if it fails
    let result = match icon_result() {
        Ok(_) => Ok(()),
        Err(e) => {
            println!("Failed to load icon ({}), showing notification without icon", e);
            app.notification()
                .builder()
                .title(&title)
                .body(&body)
                .show()
                .map_err(|e: tauri_plugin_notification::Error| e.to_string())
        }
    };

    match result {
        Ok(_) => {
            println!("Notification sent successfully!");
            Ok(())
        }
        Err(e) => {
            let err_msg = format!("Failed to show notification: {}", e);
            println!("{}", err_msg);
            Err(err_msg)
        }
    }
}

#[tauri::command]
fn update_notification_badge(
    app: AppHandle,
    count: u32,
    state: State<AppState>,
) -> Result<(), String> {
    // Update the state
    let mut notification_count = state.notification_count.lock().unwrap();
    *notification_count = count;

    // Update tray tooltip
    if let Some(tray) = app.tray_by_id("main-tray") {
        let tooltip = if count > 0 {
            format!("Unpod - {} unread notification{}", count, if count > 1 { "s" } else { "" })
        } else {
            "Unpod".to_string()
        };
        let _ = tray.set_tooltip(Some(&tooltip));
    }

    // Update window title and badge
    if let Some(window) = app.get_webview_window("main") {
        let title = if count > 0 {
            format!("({}) Unpod", count)
        } else {
            "Unpod".to_string()
        };
        let _ = window.set_title(&title);

        // Set badge count (macOS dock, Linux taskbar)
        let badge_count = if count > 0 { Some(count as i64) } else { None };
        if let Err(e) = window.set_badge_count(badge_count) {
            eprintln!("Failed to set badge count: {}", e);
        }
    }

    println!("Notification badge updated to: {} (shown in dock/taskbar badge, window title, and tray tooltip)", count);

    Ok(())
}

// ============================================
// Auto-Updater Commands
// ============================================

#[tauri::command]
async fn updater_check_for_updates(_app: AppHandle) -> Result<String, String> {
    #[cfg(not(debug_assertions))]
    {
        use tauri_plugin_updater::UpdaterExt;

        let updater = _app.updater_builder().build()
            .map_err(|e| e.to_string())?;

        match updater.check().await {
            Ok(Some(update)) => {
                Ok(format!("Update available: {}", update.version))
            }
            Ok(None) => Ok("No update available".to_string()),
            Err(e) => Err(e.to_string()),
        }
    }

    #[cfg(debug_assertions)]
    {
        Err("Auto-updates disabled in development".to_string())
    }
}

#[tauri::command]
async fn updater_download_and_install(_app: AppHandle) -> Result<(), String> {
    #[cfg(not(debug_assertions))]
    {
        use tauri_plugin_updater::UpdaterExt;

        let updater = _app.updater_builder().build()
            .map_err(|e| e.to_string())?;

        if let Some(update) = updater.check().await.map_err(|e| e.to_string())? {
            update.download_and_install(|_chunk_length, _content_length| {}, || {})
                .await
                .map_err(|e| e.to_string())?;
        }

        Ok(())
    }

    #[cfg(debug_assertions)]
    {
        Err("Auto-updates disabled in development".to_string())
    }
}

// ============================================
// System Tray Setup
// ============================================

fn create_tray(app: &tauri::AppHandle) -> Result<(), Box<dyn std::error::Error>> {
    // Create tray menu
    let show_item = MenuItem::with_id(app, "show", "Show App", true, None::<&str>)?;
    let check_updates_item = MenuItem::with_id(app, "check_updates", "Check for Updates", true, None::<&str>)?;
    let quit_item = MenuItem::with_id(app, "quit", "Quit", true, None::<&str>)?;

    let menu = Menu::with_items(
        app,
        &[
            &show_item,
            &PredefinedMenuItem::separator(app)?,
            &check_updates_item,
            &PredefinedMenuItem::separator(app)?,
            &quit_item,
        ],
    )?;

    // Load tray icon
    let icon_bytes = include_bytes!("../icons/32x32.png");
    let icon = Image::from_bytes(icon_bytes)?;

    // Create tray icon
    let _tray = TrayIconBuilder::new()
        .icon(icon)
        .menu(&menu)
        .tooltip("Unpod")
        .on_menu_event(|app, event| {
            match event.id().as_ref() {
                "show" => {
                    if let Some(window) = app.get_webview_window("main") {
                        let _ = window.show();
                        let _ = window.set_focus();
                    }
                }
                "check_updates" => {
                    let app = app.clone();
                    tauri::async_runtime::spawn(async move {
                        match updater_check_for_updates(app).await {
                            Ok(msg) => println!("{}", msg),
                            Err(e) => eprintln!("Update check failed: {}", e),
                        }
                    });
                }
                "quit" => {
                    app.exit(0);
                }
                _ => {}
            }
        })
        .on_tray_icon_event(|tray, event| {
            if let TrayIconEvent::Click {
                button: MouseButton::Left,
                button_state: MouseButtonState::Up,
                ..
            } = event
            {
                let app = tray.app_handle();
                if let Some(window) = app.get_webview_window("main") {
                    let _ = window.show();
                    let _ = window.set_focus();
                }
            }
        })
        .build(app)?;

    Ok(())
}

// ============================================
// Application Menu Setup
// ============================================

fn create_menu(app: &tauri::AppHandle) -> Result<tauri::menu::Menu<tauri::Wry>, Box<dyn std::error::Error>> {
    // File menu
    let file_menu = Submenu::with_items(
        app,
        "File",
        true,
        &[&PredefinedMenuItem::quit(app, Some("Quit"))?],
    )?;

    // Edit menu
    let edit_menu = Submenu::with_items(
        app,
        "Edit",
        true,
        &[
            &PredefinedMenuItem::undo(app, Some("Undo"))?,
            &PredefinedMenuItem::redo(app, Some("Redo"))?,
            &PredefinedMenuItem::separator(app)?,
            &PredefinedMenuItem::cut(app, Some("Cut"))?,
            &PredefinedMenuItem::copy(app, Some("Copy"))?,
            &PredefinedMenuItem::paste(app, Some("Paste"))?,
            &PredefinedMenuItem::select_all(app, Some("Select All"))?,
        ],
    )?;

    // View menu
    let view_menu = Submenu::with_items(
        app,
        "View",
        true,
        &[
            &PredefinedMenuItem::minimize(app, Some("Minimize"))?,
            &PredefinedMenuItem::maximize(app, Some("Zoom"))?,
            &PredefinedMenuItem::separator(app)?,
            &PredefinedMenuItem::fullscreen(app, Some("Toggle Full Screen"))?,
        ],
    )?;

    // Window menu
    let window_menu = Submenu::with_items(
        app,
        "Window",
        true,
        &[
            &PredefinedMenuItem::minimize(app, Some("Minimize"))?,
            &PredefinedMenuItem::close_window(app, Some("Close"))?,
        ],
    )?;

    // Build the main menu
    let menu = Menu::with_items(
        app,
        &[
            &file_menu,
            &edit_menu,
            &view_menu,
            &window_menu,
        ],
    )?;

    Ok(menu)
}

// ============================================
// Server Management
// ============================================

/// Start the Next.js server process
fn start_server(
    #[allow(unused_variables)] app: &AppHandle
) -> Result<u32, Box<dyn std::error::Error>> {
    println!("Starting Next.js server...");

    // In development, server is already running - skip
    #[cfg(debug_assertions)]
    {
        println!("Development mode - assuming server is already running on localhost:3000");
        return Ok(0); // Return dummy PID
    }

    #[cfg(not(debug_assertions))]
    {
        use std::process::{Command, Stdio};

        // Get the resource directory where we'll bundle the Next.js server
        let resource_dir = app.path().resource_dir()?;
        let server_dir = resource_dir.join("server");

        println!("Server directory: {:?}", server_dir);

        // Check if server directory exists
        if !server_dir.exists() {
            return Err(format!("Server directory not found: {:?}", server_dir).into());
        }

        // Get the bundled Node.js binary path
        // Platform-specific paths for external binaries
        let node_path = if cfg!(target_os = "macos") {
            // On macOS, external binaries go to Contents/MacOS/
            resource_dir.parent()
                .ok_or("Failed to get parent directory")?
                .join("MacOS")
                .join("node")
        } else if cfg!(target_os = "windows") {
            // On Windows, external binaries go to the same directory as the .exe
            // They are bundled with .exe extension
            let exe_dir = std::env::current_exe()?
                .parent()
                .ok_or("Failed to get exe directory")?
                .to_path_buf();
            exe_dir.join("node.exe")
        } else {
            // On Linux, external binaries are in the resources directory
            resource_dir.join("node")
        };

        println!("Using bundled Node.js at: {:?}", node_path);

        // Verify Node.js binary exists
        if !node_path.exists() {
            return Err(format!("Bundled Node.js not found at: {:?}\n\nPlease ensure Node.js is installed.", node_path).into());
        }

        // Start the Next.js standalone server
        let server_script = server_dir.join("server.js");

        println!("Starting server with bundled Node.js: {:?} {:?}", node_path, server_script);

        let child = Command::new(&node_path)
            .arg(server_script.to_str().unwrap())
            .current_dir(&server_dir)
            .env("NODE_ENV", "production")
            .env("PORT", "3000")
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()?;

        let pid = child.id();
        println!("Server started with PID: {}", pid);

        // Give the server a moment to start
        std::thread::sleep(std::time::Duration::from_secs(2));

        Ok(pid)
    }
}

/// Stop the server process
fn stop_server(pid: u32) {
    if pid == 0 {
        return; // Development mode or invalid PID
    }

    println!("Stopping server process (PID: {})...", pid);

    #[cfg(target_os = "windows")]
    {
        use std::process::Command;
        let _ = Command::new("taskkill")
            .args(&["/PID", &pid.to_string(), "/F"])
            .output();
    }

    #[cfg(not(target_os = "windows"))]
    {
        use std::process::Command;
        let _ = Command::new("kill")
            .arg(pid.to_string())
            .output();
    }

    println!("Server stopped");
}

// ============================================
// Main Application
// ============================================

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_os::init())
        .plugin(tauri_plugin_notification::init())
        .manage(AppState {
            notification_count: Mutex::new(0),
            server_process: Mutex::new(None),
        })
        .invoke_handler(tauri::generate_handler![
            // Session management
            session_get_token,
            session_set_token,
            session_delete_token,
            session_get,
            session_set,
            session_delete,
            session_clear,
            // System info
            get_platform,
            get_app_version,
            get_theme,
            // Window controls
            window_minimize,
            window_maximize,
            window_close,
            open_external,
            // Notifications
            check_notification_permission,
            request_notification_permission,
            show_notification,
            update_notification_badge,
            // Updater
            updater_check_for_updates,
            updater_download_and_install,
        ])
        .setup(|app| {
            // Start the Next.js server first
            match start_server(&app.handle()) {
                Ok(pid) => {
                    println!("Server started successfully with PID: {}", pid);
                    // Store the PID in app state
                    if let Some(state) = app.try_state::<AppState>() {
                        let mut server_process = state.server_process.lock().unwrap();
                        *server_process = Some(pid);
                    }
                }
                Err(e) => {
                    eprintln!("Failed to start server: {}", e);
                    // In development this is OK, in production we should show an error
                    #[cfg(not(debug_assertions))]
                    {
                        app.dialog()
                            .message(format!("Failed to start server: {}\n\nPlease ensure Node.js is installed.", e))
                            .title("Server Start Error")
                            .blocking_show();
                    }
                }
            }

            // Create application menu
            let menu = create_menu(&app.handle()).expect("Failed to create menu");
            app.set_menu(menu).expect("Failed to set menu");

            // Create system tray
            create_tray(&app.handle()).expect("Failed to create tray");

            // Setup notification click handler using event listeners
            // Try multiple event names to catch notification clicks
            let app_handle_1 = app.handle().clone();
            let app_handle_2 = app.handle().clone();
            let app_handle_3 = app.handle().clone();

            // Listen for various notification event patterns
            app.listen("notification-action", move |event| {
                println!("Notification event (notification-action) received: {:?}", event);
                activate_app_window(&app_handle_1);
            });

            app.listen("notification", move |event| {
                println!("Notification event (notification) received: {:?}", event);
                activate_app_window(&app_handle_2);
            });

            app.listen("tauri://notification", move |event| {
                println!("Notification event (tauri://notification) received: {:?}", event);
                activate_app_window(&app_handle_3);
            });

            // Handle app activation to show window when app is activated from notification
            let app_handle_activation = app.handle().clone();
            app.listen("tauri://focus", move |_event| {
                println!("App focus event received");
                activate_app_window(&app_handle_activation);
            });

            // Also handle window events - when window gains focus, ensure it's fully visible
            if let Some(window) = app.get_webview_window("main") {
                let app_for_focus = app.handle().clone();
                window.on_window_event(move |event| {
                    match event {
                        tauri::WindowEvent::Focused(focused) => {
                            if *focused {
                                println!("Window focused - ensuring visibility");
                                activate_app_window(&app_for_focus);
                            }
                        }
                        _ => {}
                    }
                });
            }

            // Open DevTools in debug mode
            #[cfg(debug_assertions)]
            {
                if let Some(window) = app.get_webview_window("main") {
                    window.open_devtools();
                }
            }

            // Setup cleanup handler to stop server when app exits
            let app_for_cleanup = app.handle().clone();
            app.listen("tauri://close-requested", move |_| {
                println!("App closing - stopping server...");
                if let Some(state) = app_for_cleanup.try_state::<AppState>() {
                    let server_process = state.server_process.lock().unwrap();
                    if let Some(pid) = *server_process {
                        stop_server(pid);
                    }
                }
            });

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
