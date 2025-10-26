# ============================================
# SCRIPT DE TESTS MEJORADO - CON DATOS REALES
# ============================================
param([string]$Ambiente = "local")

$urls = @{
    UserService = "http://localhost:8001"
    PedidosService = "http://localhost:8007"
    ProductService = "http://localhost:8005"
}

$testData = @{
    nit_valido = "901234567"
    nit_invalido = "999999999"
    pedido_nit_cliente = "901234567"  # Clínica Central
    pedido_nit_gerente = "800123456"  # Hospital Universitario
}

function Test-Endpoint {
    param([string]$Name, [string]$Method, [string]$Uri, [hashtable]$Headers = @{}, [object]$Body = $null, [int]$Status = 200)
    
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
        
        if ($response.StatusCode -eq $Status) {
            Write-Host "  [PASS] Status: $($response.StatusCode)" -ForegroundColor Green
            return $response.Content | ConvertFrom-Json -ErrorAction SilentlyContinue
        }
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.Value__
        if ($statusCode -eq $Status) {
            Write-Host "  [PASS] Status: $statusCode (error esperado)" -ForegroundColor Green
        }
        else {
            Write-Host "  [FAIL] Status: $statusCode (esperado: $Status)" -ForegroundColor Red
            Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

# 1. Obtener productos disponibles
Write-Host "`n=== OBTENIENDO PRODUCTOS DISPONIBLES ===" -ForegroundColor Yellow
$productosResponse = Test-Endpoint -Name "Obtener Productos" -Method GET `
    -Uri "$($urls.ProductService)/api/v1/productos?skip=0&limit=5"

$productos = @()
if ($productosResponse -and $productosResponse.items) {
    $productos = $productosResponse.items | Select-Object -First 3
    Write-Host "  Productos encontrados: $($productos.Count)" -ForegroundColor Yellow
    $productos | ForEach-Object { Write-Host "    - $($_.nombre) (ID: $($_.productoId))" }
}

if ($productos.Count -lt 3) {
    Write-Host "  ERROR: No hay suficientes productos" -ForegroundColor Red
    exit
}

# 2. Tests del Pedidos Service
Write-Host "`n=== PEDIDOS SERVICE (8007) ===" -ForegroundColor Magenta

# Health Check
Test-Endpoint -Name "Health Check" -Method GET -Uri "$($urls.PedidosService)/health" -Status 200

# Listar Pedidos
Test-Endpoint -Name "Listar Pedidos" -Method GET `
    -Uri "$($urls.PedidosService)/api/v1/pedidos?pagina=1&por_pagina=10" -Status 200

# Validar Inventario
$validarBody = @{
    productos = @(
        @{ producto_id = $productos[0].productoId; cantidad_solicitada = 5 },
        @{ producto_id = $productos[1].productoId; cantidad_solicitada = 10 },
        @{ producto_id = $productos[2].productoId; cantidad_solicitada = 8 }
    )
}

Test-Endpoint -Name "Validar Inventario" -Method POST `
    -Uri "$($urls.PedidosService)/api/v1/pedidos/validar-inventario" `
    -Body $validarBody -Status 200

# Crear Pedido - Cliente
$pedidoClienteBody = @{
    nit = $testData.pedido_nit_cliente
    productos = @(
        @{ producto_id = $productos[0].productoId; cantidad_solicitada = 5 },
        @{ producto_id = $productos[1].productoId; cantidad_solicitada = 10 },
        @{ producto_id = $productos[2].productoId; cantidad_solicitada = 8 }
    )
    observaciones = "Pedido de prueba cliente"
}

$headers = @{ 
    "usuario-id" = "1"
    "rol-usuario" = "usuario_institucional" 
}

$pedidoCliente = Test-Endpoint -Name "Crear Pedido - Cliente" -Method POST `
    -Uri "$($urls.PedidosService)/api/v1/pedidos" `
    -Body $pedidoClienteBody -Headers $headers -Status 201

# Si se creó el pedido, obtenerlo y actualizar estado
if ($pedidoCliente -and $pedidoCliente.id) {
    $pedidoId = $pedidoCliente.id
    Write-Host "  Pedido creado: $pedidoId" -ForegroundColor Yellow
    
    # Obtener Pedido
    Test-Endpoint -Name "Obtener Pedido" -Method GET `
        -Uri "$($urls.PedidosService)/api/v1/pedidos/$pedidoId" -Status 200
    
    # Actualizar Estado
    $updateBody = @{ 
        nuevo_estado = "confirmado"
        observaciones = "Confirmado desde test" 
    }
    
    Test-Endpoint -Name "Actualizar Estado" -Method PUT `
        -Uri "$($urls.PedidosService)/api/v1/pedidos/$pedidoId/estado" `
        -Body $updateBody -Status 200
}

# Crear Pedido - Gerente
$pedidoGerenteBody = @{
    nit = $testData.pedido_nit_gerente
    productos = @(
        @{ producto_id = $productos[0].productoId; cantidad_solicitada = 8 },
        @{ producto_id = $productos[1].productoId; cantidad_solicitada = 12 },
        @{ producto_id = $productos[2].productoId; cantidad_solicitada = 6 }
    )
    observaciones = "Pedido por gerente"
}

$headersGerente = @{ 
    "usuario-id" = "2"
    "rol-usuario" = "admin" 
}

Test-Endpoint -Name "Crear Pedido - Gerente" -Method POST `
    -Uri "$($urls.PedidosService)/api/v1/pedidos" `
    -Body $pedidoGerenteBody -Headers $headersGerente -Status 201

# Listar por NIT
Test-Endpoint -Name "Listar Pedidos por NIT" -Method GET `
    -Uri "$($urls.PedidosService)/api/v1/pedidos?nit=$($testData.pedido_nit_cliente)&pagina=1&por_pagina=10" -Status 200

Write-Host "`n=== TODOS LOS TESTS COMPLETADOS ===" -ForegroundColor Green