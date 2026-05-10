' Nexus AI - Launcher Windows (doble click, cero terminales)
' Inicia el backend oculto y abre la interfaz.

Dim WshShell, FSO, RootDir
Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
RootDir = FSO.GetParentFolderName(WScript.ScriptFullLocation)
WshShell.CurrentDirectory = RootDir

' 1. Matar backends previos (por puerto)
On Error Resume Next
WshShell.Run "cmd.exe /c netstat -ano | findstr :8000 > ""%TEMP%\nexus_port.txt""", 0, True
Dim TS, PID
If FSO.FileExists(WshShell.ExpandEnvironmentStrings("%TEMP%") & "\nexus_port.txt") Then
    Set TS = FSO.OpenTextFile(WshShell.ExpandEnvironmentStrings("%TEMP%") & "\nexus_port.txt", 1)
    Do While Not TS.AtEndOfStream
        Dim Line : Line = TS.ReadLine
        If InStr(Line, "LISTENING") Then
            PID = Trim(Mid(Line, InStrRev(Line, " ")))
            If IsNumeric(PID) Then
                WshShell.Run "taskkill /f /pid " & PID, 0, True
            End If
        End If
    Loop
    TS.Close
End If
On Error GoTo 0

' 2. Iniciar backend con pythonw (SIN CONSOLA)
Dim Cmd : Cmd = "pythonw.exe -m backend.api.main --host 127.0.0.1 --port 8000 --log-level warning"
WshShell.Run Cmd, 0, False

' 3. Esperar hasta 30s a que responda
Dim Ready, Retries, HTTP
Ready = False
For Retries = 1 To 30
    WScript.Sleep 1000
    On Error Resume Next
    Set HTTP = CreateObject("MSXML2.XMLHTTP")
    HTTP.Open "GET", "http://127.0.0.1:8000/", False
    HTTP.SetTimeouts 2000, 2000, 2000, 2000
    HTTP.Send
    If HTTP.Status = 200 Then
        Ready = True
        Exit For
    End If
    On Error GoTo 0
Next

' 4. Abrir interfaz
If Ready Then
    ' Intentar Tauri compilado
    Dim TauriExe : TauriExe = RootDir & "\apps\nexus-desktop\src-tauri\target\release\nexus-desktop.exe"
    If FSO.FileExists(TauriExe) Then
        WshShell.Run Chr(34) & TauriExe & Chr(34), 1, False
    Else
        ' Abrir navegador con el frontend
        WshShell.Run "cmd.exe /c start http://localhost:1420", 0, False
        WshShell.Run "cmd.exe /c start http://127.0.0.1:8000/docs", 0, False
    End If
Else
    MsgBox "Nexus no pudo conectar con el backend." & vbCrLf & vbCrLf & _
           "Verifica que Python 3.10+ y Ollama esten instalados y en PATH.", _
           vbCritical + vbOKOnly, "Nexus AI - Error de inicio"
End If
