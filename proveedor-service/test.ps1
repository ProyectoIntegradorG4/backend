# Variables de configuración (basadas en Postman)
$providerUrl = "http://localhost:8006"
$proveedorRazonSocial = "Proveedor Test $(Get-Date -Format 'yyyyMMddHHmmss')"
$proveedorNit = "900$(Get-Random -Minimum 100000 -Maximum 999999)"
$proveedorNitExistente = ""  # Se llenará después de crear uno exitoso
$proveedorEmail = "test.$(Get-Date -Format 'yyyyMMddHHmmss')@example.com"
$proveedorTelefono = "+57-1-$(Get-Random -Minimum 1000000 -Maximum 9999999)"
$proveedorDireccion = "Calle Test $(Get-Random -Minimum 1 -Maximum 1000)"
$idempotencyKey = [guid]::NewGuid().ToString()

# Función auxiliar para imprimir respuestas
function Print-Response {
    param ($Response, $Description)
    Write-Host "`n--- $Description ---"
    Write-Host "Status Code: $($Response.StatusCode)"
    Write-Host "Content: $($Response.Content)"
}

# 1. Registrar Proveedor - Sin X-Idempotency-Key (debe retornar 400, pero actualmente crea)
Write-Host "Ejecutando: Registrar Proveedor - Sin X-Idempotency-Key"
$body = @{
    razon_social = $proveedorRazonSocial
    nit = $proveedorNit
    tipo_proveedor = "laboratorio"
    email = $proveedorEmail
    telefono = $proveedorTelefono
    direccion = $proveedorDireccion
    ciudad = "Bogota"
    pais = "colombia"
    certificaciones = @("ISO 9001")
    estado = "activo"
    calificacion = 4.5
    tiempo_entrega_promedio = 3
} | ConvertTo-Json
try {
    $response = Invoke-WebRequest -Uri "$providerUrl/api/proveedores" -Method POST -Body $body -ContentType "application/json"
    Print-Response -Response $response -Description "Sin X-Idempotency-Key"
} catch {
    Print-Response -Response $_.Exception.Response -Description "Sin X-Idempotency-Key (Error esperado)"
}

# 2. Registrar Proveedor - Exitoso (con X-Idempotency-Key, usar NIT nuevo para evitar duplicado)
$proveedorNitExitoso = "900$(Get-Random -Minimum 100000 -Maximum 999999)"  # Nuevo NIT
$bodyExitoso = $body | ConvertFrom-Json
$bodyExitoso.nit = $proveedorNitExitoso
$bodyExitoso.email = "exitoso.$(Get-Date -Format 'yyyyMMddHHmmss')@example.com"
$bodyExitoso = $bodyExitoso | ConvertTo-Json
Write-Host "`nEjecutando: Registrar Proveedor - Exitoso"
$headers = @{ "X-Idempotency-Key" = $idempotencyKey }
try {
    $response = Invoke-WebRequest -Uri "$providerUrl/api/proveedores" -Method POST -Headers $headers -Body $bodyExitoso -ContentType "application/json"
    Print-Response -Response $response -Description "Registro Exitoso"
    # Guardar NIT para pruebas futuras
    $jsonResponse = $response.Content | ConvertFrom-Json
    if ($jsonResponse.nit) { $proveedorNitExistente = $jsonResponse.nit }
} catch {
    Print-Response -Response $_.Exception.Response -Description "Registro Exitoso (Error)"
}

# 3. Registrar Proveedor - NIT Duplicado (debe retornar 409)
Write-Host "`nEjecutando: Registrar Proveedor - NIT Duplicado"
$bodyDuplicado = @{
    razon_social = "Otro Nombre"
    nit = $proveedorNitExistente
    tipo_proveedor = "laboratorio"
    email = "otro.$(Get-Date -Format 'yyyyMMddHHmmss')@example.com"
    telefono = "+57-1-9998888"
    direccion = "Otra Calle 789"
    ciudad = "Bogota"
    pais = "colombia"
    certificaciones = @("ISO 9001")
    estado = "activo"
    calificacion = 4.0
    tiempo_entrega_promedio = 4
} | ConvertTo-Json
$headersDuplicado = @{ "X-Idempotency-Key" = [guid]::NewGuid().ToString() }
try {
    $response = Invoke-WebRequest -Uri "$providerUrl/api/proveedores" -Method POST -Headers $headersDuplicado -Body $bodyDuplicado -ContentType "application/json"
    Print-Response -Response $response -Description "NIT Duplicado"
} catch {
    Print-Response -Response $_.Exception.Response -Description "NIT Duplicado (Error esperado)"
}

# 4. Registrar Proveedor - Reintento con misma Key (debe retornar la misma respuesta)
Write-Host "`nEjecutando: Registrar Proveedor - Reintento con misma Key"
try {
    $response = Invoke-WebRequest -Uri "$providerUrl/api/proveedores" -Method POST -Headers $headers -Body $bodyExitoso -ContentType "application/json"
    Print-Response -Response $response -Description "Reintento con misma Key"
} catch {
    Print-Response -Response $_.Exception.Response -Description "Reintento con misma Key (Error)"
}

# 5. Listar Proveedores
Write-Host "`nEjecutando: Listar Proveedores"
try {
    $response = Invoke-WebRequest -Uri "$providerUrl/api/proveedores?skip=0&limit=10" -Method GET
    Print-Response -Response $response -Description "Listar Proveedores"
} catch {
    Print-Response -Response $_.Exception.Response -Description "Listar Proveedores (Error)"
}

# 6. Verificar Existencia Proveedor (usar query param)
Write-Host "`nEjecutando: Verificar Existencia Proveedor"
try {
    $response = Invoke-WebRequest -Uri "$providerUrl/api/proveedores/exists?nit=$proveedorNitExistente" -Method GET
    Print-Response -Response $response -Description "Verificar Existencia"
} catch {
    Print-Response -Response $_.Exception.Response -Description "Verificar Existencia (Error)"
}

# 7. Health Check Provider Service
Write-Host "`nEjecutando: Health Check Provider Service"
try {
    $response = Invoke-WebRequest -Uri "$providerUrl/health" -Method GET
    Print-Response -Response $response -Description "Health Check"
} catch {
    Print-Response -Response $_.Exception.Response -Description "Health Check (Error)"
}