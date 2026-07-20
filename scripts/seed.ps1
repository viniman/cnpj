$body = "{}"
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/seed" -Body $body -ContentType "application/json"

