<?php

return [
    'url' => env('RAG_SERVICE_URL', 'http://localhost:8001'),
    'internal_secret' => env('RAG_INTERNAL_SECRET', ''),
    'timeout' => env('RAG_TIMEOUT', 30),
];
