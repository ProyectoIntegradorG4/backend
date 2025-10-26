param([string]$Ambiente = "local")

$urls = @{
    PedidosService = "http://localhost:8007"
}

$testData = @{
    pedido_nit_cliente = "901234567"
    pedido_nit_gerente = "800123456"
}

$productIds = @(
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440001",
    "550e8400-e29b-41d4-a716-446655440002"
)

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Uri,
        [hashtable]$Headers = @{},
        [object]$Body = $null,
        [int]$Status = 200
    )
    
    try {
        Write-Host "`n[TEST] $Name" -ForegroundColor Cyan
        Write-Host "  URL: $Uri" -ForegroundColor Gray
        
        $params = @{
            Method = $Method
            Uri = $Uri
            Headers = $Headers + @{ "Content-Type" = "application/json" }
            ErrorAction = "Stop"
        }
        
        if ($Body) {
            $params.Body = $Body | ConvertTo-Json -Depth 10
        }
        
        $response = Invoke-WebRequest @params
        Write-Host "  PASS | Status: $($response.StatusCode)" -ForegroundColor Green
        return $response.Content | ConvertFrom-Json -ErrorAction SilentlyContinue
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.Value__
        if ($statusCode -eq $Status) {
            Write-Host "  PASS | Status: $statusCode (error esperado)" -ForegroundColor Green
        }
        else {
            Write-Host "  FAIL | Status: $statusCode (esperado: $Status)" -ForegroundColor Red
            try {
                $errorContent = $_.Exception.Response.Content.ReadAsStream() | ConvertFrom-Json
                Write-Host "  Error Details: $errorContent" -ForegroundColor Red
            } catch {
                Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
        return $null
    }
}

Write-Host "`n=== TESTS PEDIDOS SERVICE ===" -ForegroundColor Magenta

# 1. Health Check
Test-Endpoint -Name "Health Check" -Method GET -Uri "$($urls.PedidosService)/health" -Status 200

# 2. Listar Pedidos
$uri = "$($urls.PedidosService)/api/v1/pedidos?pagina=1&por_pagina=10"
Test-Endpoint -Name "Listar Pedidos" -Method GET -Uri $uri -Status 200

# 3. Validar Inventario
$validarBody = @{
    nit = $testData.pedido_nit_cliente
    productos = @(
        @{ producto_id = $productIds[0]; cantidad_solicitada = 5 },
        @{ producto_id = $productIds[1]; cantidad_solicitada = 10 },
        @{ producto_id = $productIds[2]; cantidad_solicitada = 8 }
    )
}

$headersValidar = @{
    "usuario-id" = "1"
    "rol-usuario" = "usuario_institucional"
}

$validarResult = Test-Endpoint -Name "Validar Inventario" -Method POST `
    -Uri "$($urls.PedidosService)/api/v1/pedidos/validar-inventario" `
    -Body $validarBody -Headers $headersValidar -Status 200

if ($validarResult) {
    Write-Host "  Validaciones:" -ForegroundColor Cyan
    if ($validarResult.validaciones) {
        $validarResult.validaciones | ForEach-Object {
            Write-Host "    - $($_.producto_id): disponible=$($_.disponible)" -ForegroundColor Gray
        }
    }
}

# 4. Crear Pedido - Cliente
Write-Host "`n[DEBUG] Creando pedido cliente..." -ForegroundColor Yellow
$pedidoBody = @{
    nit = $testData.pedido_nit_cliente
    productos = @(
        @{ producto_id = $productIds[0]; cantidad_solicitada = 2 },
        @{ producto_id = $productIds[1]; cantidad_solicitada = 3 },
        @{ producto_id = $productIds[2]; cantidad_solicitada = 1 }
    )
    observaciones = "Pedido prueba cliente"
}

Write-Host "[DEBUG] Body: $(ConvertTo-Json -Compress $pedidoBody)" -ForegroundColor Yellow

$headersCliente = @{ 
    "usuario-id" = "1"
    "rol-usuario" = "usuario_institucional" 
}

$pedido = Test-Endpoint -Name "Crear Pedido - Cliente" -Method POST `
    -Uri "$($urls.PedidosService)/api/v1/pedidos" `
    -Body $pedidoBody -Headers $headersCliente -Status 201

if ($pedido -and $pedido.pedido_id) {
    $pedidoId = $pedido.pedido_id
    Write-Host "  Pedido ID: $pedidoId" -ForegroundColor Yellow
}

Write-Host "`n=== TESTS COMPLETADOS ===" -ForegroundColor Green