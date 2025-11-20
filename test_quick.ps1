# Quick test of multilingual functionality

# Test 1: Chinese input
Write-Host "=" * 70
Write-Host "Test 1: Chinese Input"
Write-Host "=" * 70

$zh_body = @{
    messages = @(
        @{
            role    = "user"
            content = "我叫李四。我是一名高级Python后端工程师。我喜欢使用FastAPI框架和异步编程。"
        }
    )
    user_id  = "test_user_zh"
} | ConvertTo-Json -Depth 10

Write-Host "Input: 我叫李四。我是一名高级Python后端工程师。我喜欢使用FastAPI框架和异步编程。"
Write-Host ""

$response = Invoke-WebRequest -Uri "http://localhost:8000/memories" `
    -Method POST `
    -ContentType "application/json" `
    -Body $zh_body

Write-Host "Status: $($response.StatusCode)"
$json = $response.Content | ConvertFrom-Json
Write-Host "Results:"
if ($json.results) {
    $json.results | ForEach-Object {
        Write-Host "  - $($_.memory)"
    }
}
Write-Host ""

# Test 2: English input
Write-Host "=" * 70
Write-Host "Test 2: English Input"
Write-Host "=" * 70

$en_body = @{
    messages = @(
        @{
            role    = "user"
            content = "My name is John Smith. I am a senior Python backend engineer. I love working with FastAPI and async programming."
        }
    )
    user_id  = "test_user_en"
} | ConvertTo-Json -Depth 10

Write-Host "Input: My name is John Smith. I am a senior Python backend engineer. I love working with FastAPI and async programming."
Write-Host ""

$response = Invoke-WebRequest -Uri "http://localhost:8000/memories" `
    -Method POST `
    -ContentType "application/json" `
    -Body $en_body

Write-Host "Status: $($response.StatusCode)"
$json = $response.Content | ConvertFrom-Json
Write-Host "Results:"
if ($json.results) {
    $json.results | ForEach-Object {
        Write-Host "  - $($_.memory)"
    }
}
Write-Host ""

# Test 3: Search in Chinese
Write-Host "=" * 70
Write-Host "Test 3: Search Chinese Memories"
Write-Host "=" * 70

$search_body = @{
    query   = "这个人做什么工作"
    user_id = "test_user_zh"
    limit   = 5
} | ConvertTo-Json -Depth 10

Write-Host "Query: 这个人做什么工作"
Write-Host ""

$response = Invoke-WebRequest -Uri "http://localhost:8000/memories/search" `
    -Method POST `
    -ContentType "application/json" `
    -Body $search_body

Write-Host "Status: $($response.StatusCode)"
$json = $response.Content | ConvertFrom-Json
Write-Host "Results:"
if ($json.results) {
    $json.results | ForEach-Object {
        Write-Host "  [$([math]::Round($_.score, 4))] $($_.memory)"
    }
}
Write-Host ""

# Test 4: List memories for Chinese user
Write-Host "=" * 70
Write-Host "Test 4: List Chinese User's Memories"
Write-Host "=" * 70

$response = Invoke-WebRequest -Uri "http://localhost:8000/memories?user_id=test_user_zh" `
    -Method GET

Write-Host "Status: $($response.StatusCode)"
$json = $response.Content | ConvertFrom-Json
Write-Host "Memories (with metadata):"
if ($json.results) {
    $json.results | ForEach-Object {
        Write-Host "  Memory: $($_.content)"
        Write-Host "  Metadata: $(($_.metadata | ConvertTo-Json -Compress))"
        Write-Host ""
    }
}
