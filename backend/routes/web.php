<?php

use Illuminate\Support\Facades\Route;

Route::get('/', function () {
    return response()->json([
        'product' => 'GlucoRAG',
        'status' => 'online',
        'documentation' => 'https://github.com/mohamed/MRAG',
    ]);
});

Route::get('/health', function () {
    return response()->json([
        'status' => 'ok',
        'service' => 'GlucoRAG Backend',
        'timestamp' => now()->toIso8601String(),
    ]);
});
