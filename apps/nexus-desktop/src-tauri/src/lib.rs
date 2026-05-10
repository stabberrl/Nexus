use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::time::Duration;
use tauri::Manager;

fn http_agent(timeout_secs: u64) -> ureq::Agent {
    ureq::AgentBuilder::new()
        .timeout_connect(Duration::from_secs(timeout_secs))
        .timeout_read(Duration::from_secs(timeout_secs))
        .timeout_write(Duration::from_secs(timeout_secs))
        .build()
}

struct BackendProcess(Mutex<Option<Child>>);

/// Busca el directorio raiz del proyecto mirando hacia arriba desde el .exe
fn find_project_root() -> Option<std::path::PathBuf> {
    // 1. Variable de entorno
    if let Ok(root) = std::env::var("NEXUS_ROOT") {
        let p = std::path::PathBuf::from(&root);
        if p.join("backend").join("api").join("main.py").exists() {
            return Some(p);
        }
    }

    // 2. Subir desde la ubicacion del .exe
    if let Ok(exe) = std::env::current_exe() {
        let mut dir = exe.parent().unwrap_or(&exe).to_path_buf();
        for _ in 0..6 {
            if dir.join("backend").join("api").join("main.py").exists() {
                return Some(dir);
            }
            if let Some(parent) = dir.parent() {
                dir = parent.to_path_buf();
            } else {
                break;
            }
        }
    }

    // 3. Directorio actual
    if let Ok(cwd) = std::env::current_dir() {
        if cwd.join("backend").join("api").join("main.py").exists() {
            return Some(cwd);
        }
    }

    None
}

fn start_backend(root: &std::path::Path) -> Option<Child> {
    // Probar pythonw.exe primero (sin consola), fallback a python.exe
    let pythons = ["pythonw.exe", "python.exe"];
    let module = "backend.api.main";
    let port = "8000";

    for python in &pythons {
        if let Ok(child) = Command::new(python)
            .args(["-m", module, "--host", "127.0.0.1", "--port", port, "--log-level", "warning"])
            .current_dir(root)
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()
        {
            return Some(child);
        }
    }
    None
}

fn wait_for_backend(timeout_secs: u64) -> bool {
    let url = "http://127.0.0.1:8000/";
    let agent = http_agent(1);
    let start = std::time::Instant::now();
    while start.elapsed().as_secs() < timeout_secs {
        if let Ok(resp) = agent.get(url).call() {
            if resp.status() == 200 {
                return true;
            }
        }
        std::thread::sleep(std::time::Duration::from_millis(500));
    }
    false
}

#[tauri::command]
fn get_backend_status() -> String {
    let agent = http_agent(2);
    match agent.get("http://127.0.0.1:8000/").call() {
        Ok(resp) => {
            if resp.status() == 200 {
                "online".to_string()
            } else {
                "error".to_string()
            }
        }
        Err(_) => "offline".to_string(),
    }
}

fn run_event_handler(app: &tauri::AppHandle, event: tauri::RunEvent) {
    if let tauri::RunEvent::ExitRequested { .. } = event {
        let state = app.state::<BackendProcess>();
        if let Some(ref mut child) = *state.0.lock().unwrap() {
            println!("[Nexus] Deteniendo backend...");
            let _ = child.kill();
            let _ = child.wait();
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(BackendProcess(Mutex::new(None)))
        .invoke_handler(tauri::generate_handler![get_backend_status])
        .setup(|app| {
            if let Some(root) = find_project_root() {
                println!("[Nexus] Project root: {:?}", root);
                if let Some(child) = start_backend(&root) {
                    println!("[Nexus] Backend iniciado (PID: {})", child.id());
                    let state = app.state::<BackendProcess>();
                    *state.0.lock().unwrap() = Some(child);

                    if wait_for_backend(15) {
                        println!("[Nexus] Backend listo!");
                    } else {
                        println!("[Nexus] Warning: Backend no respondio en 15s");
                    }
                } else {
                    println!("[Nexus] Error: No se encontro python");
                }
            } else {
                println!("[Nexus] Error: No se encontro el proyecto");
            }

            #[cfg(debug_assertions)]
            {
                let window = app.get_webview_window("main").unwrap();
                window.open_devtools();
            }
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(run_event_handler);
}
