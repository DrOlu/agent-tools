@echo off
setlocal EnableDelayedExpansion

:: ============================================================================
:: Install Agent Tools to System PATH
:: This script copies all .exe files from the current directory to a permanent
:: location and adds that location to the system PATH.
:: 
:: Run as Administrator for system-wide installation.
:: ============================================================================

:: Configuration
set "INSTALL_DIR=%ProgramFiles%\AgentTools"
set "SOURCE_DIR=%~dp0"
set "RELEASE_URL=https://github.com/DrOlu/agent-tools/releases/download/large-binaries"
:: Large binaries (>100 MB) live on the repo's large-binaries GitHub release,
:: not in the git tree (GitHub refuses files >100 MB in normal git).
set "LARGE_TOOLS=opencode.exe omp.exe usql.exe"

echo.
echo ============================================
echo   Agent Tools Installer
echo ============================================
echo.

:: Check for admin privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] This script requires Administrator privileges.
    echo         Right-click and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

:: Create installation directory
echo [1/5] Creating installation directory...
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create directory: %INSTALL_DIR%
        pause
        exit /b 1
    )
    echo       Created: %INSTALL_DIR%
) else (
    echo       Directory exists: %INSTALL_DIR%
)

:: Copy all .exe files
echo.
echo [2/5] Copying bundled executables...
set "COUNT=0"
for %%F in ("%SOURCE_DIR%*.exe") do (
    set "FILENAME=%%~nxF"
    :: Skip this installer script itself
    if /i not "!FILENAME!"=="install-agent-tools.exe" (
        echo       Copying: !FILENAME!
        copy /Y "%%F" "%INSTALL_DIR%\" >nul
        if !errorlevel! neq 0 (
            echo       [WARNING] Failed to copy: !FILENAME!
        ) else (
            set /a COUNT+=1
        )
    )
)
echo       Copied %COUNT% bundled executable(s)

echo.
echo [3/5] Downloading large binaries from GitHub release...
:: These three exceed GitHub's 100 MB per-file limit and ship as release assets.
for %%T in (%LARGE_TOOLS%) do (
    echo       Downloading: %%T
    curl -L --fail --silent --show-error -o "%INSTALL_DIR%\%%T" "%RELEASE_URL%/%%T"
    if !errorlevel! neq 0 (
        echo       [WARNING] Failed to download: %%T
    ) else (
        set /a COUNT+=1
    )
)
echo       %COUNT% total executable(s) in place after download

:: Check if already in PATH
echo.
echo [4/5] Checking system PATH...
echo %PATH% | find /i "%INSTALL_DIR%" >nul
if %errorlevel% equ 0 (
    echo       %INSTALL_DIR% is already in PATH
    goto :verify
)

:: Add to system PATH
echo       Adding to system PATH...
for /f "tokens=2*" %%A in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "CURRENT_PATH=%%B"

:: Check if path would exceed limit (8191 chars)
set "NEW_PATH=%CURRENT_PATH%;%INSTALL_DIR%"
if "!NEW_PATH:~8000,1!" neq "" (
    echo [ERROR] PATH would exceed maximum length. Cannot add directory.
    echo         Please manually add: %INSTALL_DIR%
    pause
    exit /b 1
)

:: Update the registry
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path /t REG_EXPAND_SZ /d "%NEW_PATH%" /f >nul
if %errorlevel% neq 0 (
    echo [ERROR] Failed to update system PATH
    pause
    exit /b 1
)

:: Broadcast environment change
echo       Broadcasting environment change...
powershell -Command "[Environment]::SetEnvironmentVariable('Path', [Environment]::GetEnvironmentVariable('Path', 'Machine'), 'Machine')" 2>nul

:verify
:: Verify installation
echo.
echo [5/5] Verifying installation...
set "VERIFIED=0"
for %%F in ("%INSTALL_DIR%\*.exe") do (
    set /a VERIFIED+=1
)
echo       Found %VERIFIED% executable(s) in %INSTALL_DIR%

:: List installed tools
echo.
echo ============================================
echo   Installed Tools:
echo ============================================
for %%F in ("%INSTALL_DIR%\*.exe") do (
    echo   - %%~nF
)

echo.
echo ============================================
echo   Installation Complete!
echo ============================================
echo.
echo   Location: %INSTALL_DIR%
echo.
echo   NOTE: You may need to restart your terminal
echo         or log out/in for PATH changes to take effect.
echo.
echo   To verify, open a new terminal and run:
echo     where opencode
echo.

pause
exit /b 0
