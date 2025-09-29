# 🚀 Script de Benchmark para User Service - Pruebas de Rendimiento
# Ejecuta 10 peticiones concurrentes para validar objetivo de <1 segundo

Write-Host "🚀 INICIANDO BENCHMARK DE RENDIMIENTO - USER SERVICE" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green

# Configuración del test
$uri = "http://localhost:8001/register"
$headers = @{
    "Content-Type" = "application/json"
}

$concurrentRequests = 10
$jobs = @()

Write-Host "📋 Configuración del test:" -ForegroundColor Cyan
Write-Host "   • URL: $uri" -ForegroundColor White
Write-Host "   • Peticiones concurrentes: $concurrentRequests" -ForegroundColor White
Write-Host "   • Objetivo: < 1000ms promedio" -ForegroundColor White
Write-Host ""

Write-Host "🔄 Enviando $concurrentRequests peticiones concurrentes..." -ForegroundColor Yellow
$startTime = Get-Date

for ($i = 1; $i -le $concurrentRequests; $i++) {
    $testBody = @{
        nombre = "Performance Test Hospital $i"
        email = "perf.test$i@benchmark.com"
        nit = "901234567"
        password = "S3gura!2025"
    } | ConvertTo-Json
    
    $job = Start-Job -ScriptBlock {
        param($uri, $headers, $body)
        $start = Get-Date
        try {
            $response = Invoke-RestMethod -Uri $uri -Method POST -Headers $headers -Body $body -TimeoutSec 30
            $end = Get-Date
            $duration = ($end - $start).TotalMilliseconds
            return @{
                Success = $true
                Duration = $duration
                StatusCode = 200
                ResponseSize = ($response | ConvertTo-Json).Length
                UserId = $response.userId
            }
        } catch {
            $end = Get-Date
            $duration = ($end - $start).TotalMilliseconds
            $statusCode = 500
            $errorMessage = $_.Exception.Message
            
            # Intentar extraer código de estado HTTP si está disponible
            if ($_.Exception.Response) {
                $statusCode = [int]$_.Exception.Response.StatusCode
            }
            
            return @{
                Success = $false
                Duration = $duration
                Error = $errorMessage
                StatusCode = $statusCode
            }
        }
    } -ArgumentList $uri, $headers, $testBody
    
    $jobs += $job
    Write-Host "   Petición $i enviada..." -ForegroundColor Gray
}

Write-Host "⏳ Esperando respuestas..." -ForegroundColor Yellow

# Esperar a que todos terminen con timeout
$results = $jobs | Wait-Job -Timeout 60 | Receive-Job
$jobs | Remove-Job -Force

$endTime = Get-Date
$totalTime = ($endTime - $startTime).TotalMilliseconds

# Análisis de resultados
$successful = ($results | Where-Object { $_.Success -eq $true }).Count
$failed = ($results | Where-Object { $_.Success -eq $false }).Count

if ($results.Count -gt 0) {
    $durations = $results | ForEach-Object { $_.Duration }
    $avgResponseTime = ($durations | Measure-Object -Average).Average
    $maxResponseTime = ($durations | Measure-Object -Maximum).Maximum
    $minResponseTime = ($durations | Measure-Object -Minimum).Minimum
    $medianResponseTime = ($durations | Sort-Object)[[math]::Floor($durations.Count / 2)]
} else {
    $avgResponseTime = 0
    $maxResponseTime = 0
    $minResponseTime = 0
    $medianResponseTime = 0
}

# Mostrar resultados
Write-Host ""
Write-Host "📊 RESULTADOS DEL BENCHMARK:" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "⏱️  Tiempo total de ejecución: $([math]::Round($totalTime, 2)) ms" -ForegroundColor White
Write-Host "📈 Peticiones por segundo: $([math]::Round($concurrentRequests / ($totalTime / 1000), 2)) req/s" -ForegroundColor White
Write-Host ""

Write-Host "📊 Resultados por petición:" -ForegroundColor Cyan
Write-Host "   ✅ Exitosas: $successful" -ForegroundColor Green
Write-Host "   ❌ Fallidas: $failed" -ForegroundColor Red
Write-Host "   📊 Tasa de éxito: $([math]::Round(($successful / $concurrentRequests) * 100, 1))%" -ForegroundColor White
Write-Host ""

Write-Host "⚡ Tiempos de respuesta:" -ForegroundColor Cyan
Write-Host "   📈 Promedio: $([math]::Round($avgResponseTime, 2)) ms" -ForegroundColor $(if ($avgResponseTime -lt 1000) { "Green" } else { "Red" })
Write-Host "   📊 Mediana: $([math]::Round($medianResponseTime, 2)) ms" -ForegroundColor White
Write-Host "   ⚡ Mínimo: $([math]::Round($minResponseTime, 2)) ms" -ForegroundColor Green
Write-Host "   🐌 Máximo: $([math]::Round($maxResponseTime, 2)) ms" -ForegroundColor $(if ($maxResponseTime -gt 2000) { "Red" } else { "Yellow" })

# Evaluación del objetivo
Write-Host ""
if ($avgResponseTime -lt 1000 -and $successful -eq $concurrentRequests) {
    Write-Host "🎯 ¡OBJETIVO ALCANZADO!" -ForegroundColor Green
    Write-Host "   ✅ Tiempo promedio < 1000ms: $([math]::Round($avgResponseTime, 2))ms" -ForegroundColor Green
    Write-Host "   ✅ Todas las peticiones exitosas: $successful/$concurrentRequests" -ForegroundColor Green
} elseif ($avgResponseTime -lt 1000) {
    Write-Host "⚠️  OBJETIVO PARCIALMENTE ALCANZADO" -ForegroundColor Yellow
    Write-Host "   ✅ Tiempo promedio < 1000ms: $([math]::Round($avgResponseTime, 2))ms" -ForegroundColor Green
    Write-Host "   ❌ Peticiones fallidas: $failed/$concurrentRequests" -ForegroundColor Red
} else {
    Write-Host "❌ OBJETIVO NO ALCANZADO" -ForegroundColor Red
    Write-Host "   ❌ Tiempo promedio > 1000ms: $([math]::Round($avgResponseTime, 2))ms" -ForegroundColor Red
    if ($failed -gt 0) {
        Write-Host "   ❌ Peticiones fallidas: $failed/$concurrentRequests" -ForegroundColor Red
    }
}

# Detalle por petición
Write-Host ""
Write-Host "📋 Detalle por petición:" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Gray

for ($i = 0; $i -lt $results.Count; $i++) {
    $result = $results[$i]
    $status = if ($result.Success) { "✅" } else { "❌" }
    $timeColor = if ($result.Duration -lt 1000) { "Green" } elseif ($result.Duration -lt 2000) { "Yellow" } else { "Red" }
    
    if ($result.Success) {
        Write-Host "$status Petición $($i+1): $([math]::Round($result.Duration, 2)) ms - UserID: $($result.UserId)" -ForegroundColor $timeColor
    } else {
        Write-Host "$status Petición $($i+1): $([math]::Round($result.Duration, 2)) ms - Error: $($result.Error)" -ForegroundColor Red
    }
}

# Códigos de estado HTTP
if ($failed -gt 0) {
    Write-Host ""
    Write-Host "🔍 Análisis de errores:" -ForegroundColor Cyan
    $errorGroups = $results | Where-Object { -not $_.Success } | Group-Object StatusCode
    foreach ($group in $errorGroups) {
        Write-Host "   HTTP $($group.Name): $($group.Count) errores" -ForegroundColor Red
    }
}

# Recomendaciones
Write-Host ""
Write-Host "💡 RECOMENDACIONES:" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan

if ($avgResponseTime -gt 1000) {
    Write-Host "📈 Para mejorar el rendimiento:" -ForegroundColor Yellow
    Write-Host "   • Verificar que Redis esté funcionando (caché de NITs)" -ForegroundColor White
    Write-Host "   • Aumentar pool de conexiones de PostgreSQL" -ForegroundColor White
    Write-Host "   • Revisar logs de contenedores: docker-compose logs -f user-service" -ForegroundColor White
}

if ($successful -lt $concurrentRequests) {
    Write-Host "🔧 Para solucionar errores:" -ForegroundColor Yellow
    Write-Host "   • Verificar que todos los servicios estén funcionando" -ForegroundColor White
    Write-Host "   • Revisar conectividad entre microservicios" -ForegroundColor White
    Write-Host "   • Aumentar timeouts si hay problemas de red" -ForegroundColor White
}

Write-Host ""
Write-Host "🔍 Comandos útiles para diagnóstico:" -ForegroundColor Cyan
Write-Host "   docker-compose ps                                    # Estado de servicios" -ForegroundColor Gray
Write-Host "   docker-compose logs -f user-service                  # Logs del user service" -ForegroundColor Gray
Write-Host "   docker stats                                         # Uso de recursos" -ForegroundColor Gray
Write-Host "   curl http://localhost:8001/health                    # Health check" -ForegroundColor Gray

Write-Host ""
Write-Host "🏁 Benchmark completado - $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Green