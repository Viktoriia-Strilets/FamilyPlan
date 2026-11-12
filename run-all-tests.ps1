
# Список мікросервісів
$services = @(
    "user-service",
    "budget-service",
    "shopping-service",
    "analytics-service"
)

# Використовуємо Python 3.12
$python = "py"
$pythonVersion = "-3.12"

$root = $PSScriptRoot
$failedServices = @()

# Перевірка доступності Python 3.12
Write-Host "`nChecking Python 3.12..." -ForegroundColor Yellow

& $python $pythonVersion --version

if ($LASTEXITCODE -ne 0) {
    Write-Host "Python 3.12 not found!" -ForegroundColor Red
    exit 1
}

foreach ($service in $services) {

    $servicePath = Join-Path $root "backend\$service"
    $requirementsPath = Join-Path $servicePath "requirements.txt"
    $testsPath = Join-Path $servicePath "tests"

    Write-Host "`n====================================" -ForegroundColor Cyan
    Write-Host "Testing: $service" -ForegroundColor Cyan
    Write-Host "====================================" -ForegroundColor Cyan

    # 1. Перевірка папки сервісу
    if (-not (Test-Path $servicePath)) {
        Write-Host "Service folder not found!" -ForegroundColor Red
        $failedServices += $service
        continue
    }

    Push-Location $servicePath

    try {

        # 2. Перевірка requirements.txt
        if (-not (Test-Path $requirementsPath)) {
            Write-Host "requirements.txt not found!" -ForegroundColor Red
            $failedServices += $service
            continue
        }

        # 3. Перевірка та встановлення основних залежностей
        Write-Host "`nChecking dependencies..." -ForegroundColor Yellow

        & $python $pythonVersion -m pip install -r requirements.txt --quiet --no-warn-script-location

        if ($LASTEXITCODE -ne 0) {
            Write-Host "Dependency installation failed!" -ForegroundColor Red
            $failedServices += $service
            continue
        }

        # 4. Перевірка та встановлення тестових залежностей
        Write-Host "Checking test dependencies..." -ForegroundColor Yellow

        & $python $pythonVersion -m pip install pytest httpx --quiet

        if ($LASTEXITCODE -ne 0) {
            Write-Host "Test dependencies installation failed!" -ForegroundColor Red
            $failedServices += $service
            continue
        }

        # 5. Перевірка папки tests
        if (-not (Test-Path $testsPath)) {
            Write-Host "Tests folder not found!" -ForegroundColor Red
            $failedServices += $service
            continue
        }

        # 6. Запуск тестів
        Write-Host "`nRunning tests..." -ForegroundColor Yellow

        & $python $pythonVersion -m pytest tests/ -v

        if ($LASTEXITCODE -ne 0) {
            Write-Host "Tests failed for $service!" -ForegroundColor Red
            $failedServices += $service
        }
        else {
            Write-Host "Tests passed for $service!" -ForegroundColor Green
        }
    }
    finally {
        Pop-Location
    }
}

# 7. Загальний результат
Write-Host "`n====================================" -ForegroundColor Cyan
Write-Host "           FINAL SUMMARY            " -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

if ($failedServices.Count -eq 0) {
    Write-Host "`nAll services passed!" -ForegroundColor Green
}
else {
    Write-Host "`nFailed services:" -ForegroundColor Red

    $failedServices | ForEach-Object {
        Write-Host "- $_" -ForegroundColor Red
    }

    Write-Host "`nSome tests or installations failed!" -ForegroundColor Red
}
